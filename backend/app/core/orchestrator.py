import asyncio
from typing import TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from pydantic import Field

from app.agents.agent_factory import AgentFactory
from app.agents.agent_registry import AgentRegistry
from app.core.configuration import RuntimeConfig
from app.core.execution_engine import ExecutionEngine
from app.core.task_planner import TaskPlanner
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget, LLMGateway
from app.monitoring.resources import sample_resources
from app.schemas.domain import (
    AgentProposals,
    AgentRecord,
    AgentSpec,
    ExecutionPlan,
    Finding,
    FindingsOutput,
    RunRecord,
    RunRequest,
    StrictModel,
)
from app.services.document_store import Document, DocumentInput
from app.validation.conflict_resolver import ConflictResolver
from app.validation.cross_model_review import CrossModelReview
from app.validation.evidence_validator import EvidenceValidator


class WorkflowState(TypedDict):
    run_id: str
    stage: str


class SynthesisOutput(StrictModel):
    summary: str = Field(max_length=1200)


class MasterOrchestrator:
    """A fixed LangGraph controls all stages; models can propose data, never graph edges."""

    def __init__(
        self,
        config: RuntimeConfig,
        gateway: LLMGateway,
        agents: AgentRegistry,
        engine: ExecutionEngine,
    ):
        self.config, self.gateway, self.agents, self.engine = config, gateway, agents, engine
        self.factory = AgentFactory(config, agents)

    def record(
        self,
        run: RunRecord,
        role: str,
        model_id: str,
        name: str,
        task: str,
        parent: AgentRecord | None = None,
        *,
        delegate: bool = False,
    ) -> AgentRecord:
        model = self.config.models.get(model_id, role)
        return self.agents.register(
            AgentRecord(
                agent_id=f"{run.run_id}_{uuid4().hex[:10]}",
                run_id=run.run_id,
                name=name,
                role=role,
                model_id=model_id,
                manufacturer=model.manufacturer,
                task=task,
                parent_agent=parent.agent_id if parent else None,
                depth=parent.depth + 1 if parent else 0,
                can_delegate=delegate,
            )
        )

    async def workflow(
        self,
        run: RunRecord,
        request: RunRequest,
        document: Document,
        budget: CallBudget,
        findings: list[Finding],
    ) -> None:
        single = self.config.agents.single_model
        root = self.record(
            run,
            "orchestrator",
            single if run.mode in {"A", "B"} else self.config.agents.orchestrator_model,
            "Master Orchestrator",
            request.task,
            delegate=True,
        )
        leaves: list[tuple[AgentRecord, AgentSpec]] = []
        plan: ExecutionPlan | None = None
        levels: list[list] = []

        def stage(name: str, progress: float) -> dict:
            run.stage, run.progress = name, progress
            run.resource_samples.append(sample_resources())
            return {"stage": name}

        async def planning(_state):
            nonlocal plan, levels
            stage("planning", 0.05)
            if run.mode == "A":
                return {"stage": "single"}

            async def operation():
                return await self.engine.ask(
                    root,
                    document,
                    budget,
                    "plan",
                    {
                        "task": request.task,
                        "criteria": request.criteria,
                        "allowed_supervisors": [
                            s.model_dump() for s in self.config.agents.supervisors
                        ],
                        "preferred_supervisors": self.config.agents.default_supervisors,
                        "instruction": "Select preferred supervisors with acyclic dependencies.",
                    },
                    ExecutionPlan,
                )

            plan = await self.engine.execute(root, operation)
            levels = TaskPlanner(self.config).validate(plan)
            return {"stage": "planned"}

        async def delegation(_state):
            stage("delegating", 0.2)
            if run.mode == "A":
                return {"stage": "single"}
            definitions = {s.id: s for s in self.config.agents.supervisors}
            # Propose by dependency level; children execute below with the same dependency order.
            for level in levels:
                for task in level:
                    definition = definitions[task.supervisor]
                    model_id = single if run.mode == "B" else definition.model_id
                    supervisor = self.record(
                        run,
                        task.supervisor,
                        model_id,
                        definition.name,
                        task.task,
                        root,
                        delegate=True,
                    )

                    async def operation(supervisor=supervisor, task=task, model_id=model_id):
                        if run.mode != "D":
                            return AgentProposals(
                                agents=[
                                    AgentSpec(
                                        agent_id=f"static_{task.supervisor}",
                                        name=f"{task.supervisor} specialist",
                                        description="Statisch konfigurierte Analyseaufgabe",
                                        task=task.task,
                                        category=task.supervisor,
                                        model_id=model_id,
                                        supervisor_id=supervisor.agent_id,
                                        max_runtime_seconds=min(
                                            300, int(self.config.limits.agent_timeout_seconds)
                                        ),
                                    )
                                ]
                            )
                        remaining = self.config.limits.max_dynamic_agents - len(leaves)
                        if remaining < 1:
                            raise LLMError(429, "Subagentenlimit erreicht.")
                        return await self.engine.ask(
                            supervisor,
                            document,
                            budget,
                            "delegate",
                            {
                                "task": task.task,
                                "criteria": request.criteria,
                                "category": task.supervisor,
                                "supervisor_id": supervisor.agent_id,
                                "suggested_model_id": model_id,
                                "allowed_models": [
                                    m.id
                                    for m in self.config.models.enabled()
                                    if "specialist" in m.allowed_roles
                                ],
                                "limits": {
                                    "max_agents": remaining,
                                    "prefer_agents": 1,
                                    "max_iterations": self.config.limits.max_iterations,
                                    "max_runtime_seconds": int(
                                        self.config.limits.agent_timeout_seconds
                                    ),
                                    "max_delegation_depth": self.config.limits.max_delegation_depth,
                                },
                                "document_overview": document.pages,
                            },
                            AgentProposals,
                        )

                    proposals = await self.engine.execute(supervisor, operation)
                    for spec in proposals.agents:
                        leaves.append(
                            self.factory.create(spec, supervisor, dynamic=run.mode == "D")
                        )
            return {"stage": "delegated"}

        def append_findings(result: FindingsOutput, agent: AgentRecord):
            model = self.config.models.get(agent.model_id)
            for draft in result.findings:
                findings.append(
                    Finding(
                        **draft.model_dump(),
                        run_id=run.run_id,
                        agent_id=agent.agent_id,
                        model_id=model.id,
                        model=model.name,
                        manufacturer=model.manufacturer,
                    )
                )

        async def analyze(_state):
            stage("analyzing", 0.4)

            async def analyze_agent(agent: AgentRecord, spec: AgentSpec | None):
                async def operation():
                    return await self.engine.ask(
                        agent,
                        document,
                        budget,
                        "analyze",
                        {
                            "task": agent.task,
                            "input": DocumentInput(
                                document=document,
                                criteria=request.criteria,
                            ).model_dump(mode="json"),
                            "category": spec.category if spec else "content",
                        },
                        FindingsOutput,
                        iterations=spec.max_iterations if spec else 1,
                    )

                output = await self.engine.execute(
                    agent, operation, runtime_limit=spec.max_runtime_seconds if spec else None
                )
                append_findings(output, agent)

            if run.mode == "A":
                await analyze_agent(root, None)
            else:
                for level in levels:
                    categories = {t.supervisor for t in level}
                    async with asyncio.TaskGroup() as group:
                        for agent, spec in leaves:
                            if spec.category in categories:
                                group.create_task(analyze_agent(agent, spec))
            return {"stage": "analyzed"}

        async def evidence(_state):
            stage("evidence", 0.6)
            for finding in findings:
                if run.mode == "D":
                    EvidenceValidator().validate(finding, document)
                else:
                    finding.evidence_detail = (
                        "Evidenzprüfung ist in diesem Evaluationsmodus deaktiviert."
                    )
            return {"stage": "evidence"}

        async def review(_state):
            stage("reviewing", 0.7)
            for finding in findings:
                if run.mode in {"A", "B"}:
                    finding.review_status = "NOT_REQUESTED"
                    continue
                await review_finding(finding)
            return {"stage": "reviewed"}

        async def review_finding(finding: Finding, *, third: bool = False):
            used = {r.manufacturer for r in finding.reviews} | {finding.manufacturer}
            candidates = [
                m
                for m in self.gateway.independent_reviewers(
                    self.config.models.get(finding.model_id)
                )
                if m.manufacturer not in used
            ]
            for model in candidates:
                reviewer = self.record(
                    run,
                    "reviewer",
                    model.id,
                    "Third-model review" if third else "Cross-model review",
                    "Unabhängige Befundprüfung",
                    root,
                )
                try:
                    await CrossModelReview(self.engine).review(finding, reviewer, document, budget)
                    return
                except LLMError as exc:
                    if exc.status_code == 429:
                        raise
                    # Missing reviewers are visible; never fall back to the source manufacturer.
                    continue
            finding.review_status = "REVIEWED" if finding.reviews else "MISSING"
            if "Unabhängige Prüfung war nicht für alle Befunde verfügbar." not in run.warnings:
                run.warnings.append("Unabhängige Prüfung war nicht für alle Befunde verfügbar.")

        async def conflicts(_state):
            stage("conflicts", 0.8)
            resolver = ConflictResolver()
            resolver.detect(findings)
            if run.mode in {"C", "D"}:
                remaining = self.config.limits.max_conflict_reviews
                for finding in findings:
                    if finding.conflict and remaining:
                        await review_finding(finding, third=True)
                        remaining -= 1
                resolver.detect(findings)
            return {"stage": "conflicts"}

        async def synthesis(_state):
            stage("synthesizing", 0.9)
            if run.mode == "A":
                run.synthesis_draft = "Single-Prompt-Befunde; menschliche Prüfung ausstehend."
            else:
                agent = self.record(
                    run,
                    "synthesis",
                    single if run.mode == "B" else self.config.agents.synthesis_model,
                    "Synthesis Agent",
                    "Prüfentwurf zusammenfassen",
                    root,
                )

                async def operation():
                    return await self.engine.ask(
                        agent,
                        document,
                        budget,
                        "synthesize",
                        {
                            "findings": [
                                {
                                    "statement": f.statement,
                                    "evidence": f.evidence_status,
                                    "review": [r.verdict for r in f.reviews],
                                    "conflict": f.conflict,
                                }
                                for f in findings
                            ],
                            "instruction": "Draft overview only; no finality or consensus.",
                        },
                        SynthesisOutput,
                    )

                result = await self.engine.execute(agent, operation)
                run.synthesis_draft = result.summary
            stage("human_review", 1.0)
            return {"stage": "human_review"}

        graph = StateGraph(WorkflowState)
        nodes = {
            "plan": planning,
            "delegate": delegation,
            "analyze": analyze,
            "evidence": evidence,
            "review": review,
            "conflicts": conflicts,
            "synthesis": synthesis,
        }
        previous = START
        for name, operation in nodes.items():
            graph.add_node(name, operation)
            graph.add_edge(previous, name)
            previous = name
        graph.add_edge(previous, END)
        await graph.compile().ainvoke(
            {"run_id": run.run_id, "stage": "queued"},
            config={"recursion_limit": 20, "callbacks": []},
        )
