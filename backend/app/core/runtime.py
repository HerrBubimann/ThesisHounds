import asyncio
from contextlib import suppress

from app.agents.agent_registry import AgentRegistry
from app.config import Settings
from app.core.configuration import RuntimeConfig
from app.core.execution_engine import ExecutionEngine
from app.core.orchestrator import MasterOrchestrator
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget, LLMGateway
from app.llm.providers.base import LLMProvider
from app.monitoring.resources import sample_resources
from app.schemas.domain import AgentStatus, Finding, HumanReview, RunRecord, RunRequest, now
from app.services.document_store import DocumentStore
from app.workflows.assessment_workflow import AssessmentWorkflow


class AnalysisRuntime:
    """Single-process bounded run manager. No queues or state are shared across workers."""

    def __init__(self, settings: Settings, provider: LLMProvider, *, mocked: bool = False):
        self.config = RuntimeConfig(settings.config_dir)
        self.provider, self.mocked = provider, mocked
        limits = self.config.limits
        self.gateway = LLMGateway(
            self.config.models,
            {"ollama": provider},
            self.config.policy,
            max_parallel=min(
                limits.max_parallel_model_calls, settings.max_concurrent_model_requests
            ),
            sequential_loading=limits.sequential_model_loading,
        )
        self.agents = AgentRegistry(limits)
        self.engine = ExecutionEngine(self.gateway, self.agents, limits)
        self.orchestrator = MasterOrchestrator(self.config, self.gateway, self.agents, self.engine)
        self.store = DocumentStore(settings.document_store_dir)
        self.runs: dict[str, RunRecord] = {}
        self.findings: dict[str, list[Finding]] = {}
        self.tasks: dict[str, asyncio.Task] = {}
        self.budgets: dict[str, CallBudget] = {}
        self.maintenance: asyncio.Task | None = None
        self.assessments = AssessmentWorkflow(settings, self.gateway, self.config)
        self.assessments.legacy_active = lambda: sum(not t.done() for t in self.tasks.values())

    def maintain(self) -> None:
        self.maintenance = asyncio.create_task(self._maintain())

    async def _maintain(self) -> None:
        while True:
            await asyncio.sleep(min(30, self.config.limits.retention_seconds))
            self.cleanup()

    def cleanup(self, *, make_room: bool = False) -> None:
        self.assessments.cleanup()
        completed = sorted(
            (r for r in self.runs.values() if r.finished_at is not None), key=lambda r: r.created_at
        )
        for run in completed:
            expired = (
                now() - run.finished_at
            ).total_seconds() >= self.config.limits.retention_seconds
            full = make_room and len(self.runs) >= self.config.limits.max_retained_runs
            if expired or full:
                self.store.remove(run.run_id)
                self.runs.pop(run.run_id, None)
                self.findings.pop(run.run_id, None)
                self.tasks.pop(run.run_id, None)
                self.budgets.pop(run.run_id, None)
                self.agents.remove_run(run.run_id)

    def start(self, request: RunRequest) -> RunRecord:
        self.cleanup(make_room=True)
        if (
            sum(not task.done() for task in self.tasks.values())
            + sum(not task.done() for task in self.assessments.tasks.values())
            >= self.config.limits.max_active_runs
        ):
            raise LLMError(429, "Maximale Anzahl aktiver Analysen erreicht.")
        if len(self.runs) >= self.config.limits.max_retained_runs:
            raise LLMError(429, "Run-Speicher ist belegt.")
        if any(not criterion.strip() or len(criterion) > 150 for criterion in request.criteria):
            raise LLMError(422, "Bewertungskriterien müssen 1–150 Zeichen enthalten.")
        run = RunRecord(
            mode=request.mode,
            document_id=request.document_id,
            criteria=request.criteria,
            mocked=self.mocked,
        )
        document = self.store.create_demo(run.run_id)
        run.document_digest = document.digest
        run.model_snapshot = [m.model_dump() for m in self.config.models.enabled()]
        run.execution_snapshot = self.config.limits.model_dump()
        self.runs[run.run_id], self.findings[run.run_id] = run, []
        self.tasks[run.run_id] = asyncio.create_task(self._execute(run, request, document))
        return run

    async def _execute(self, run, request, document) -> None:
        budget = CallBudget(self.config.limits.max_model_calls, self.config.limits.max_tokens)
        self.budgets[run.run_id] = budget
        run.status = "RUNNING"
        started = now()
        sampler = asyncio.create_task(self._sample(run))
        try:
            async with asyncio.timeout(self.config.limits.run_timeout_seconds):
                available = {m.name: m for m in await self.provider.discover()}
                for model in run.model_snapshot:
                    local = available.get(model["name"])
                    model["digest"] = local.digest if local else None
                await self.orchestrator.workflow(
                    run, request, document, budget, self.findings[run.run_id]
                )
            run.status = "WAITING_FOR_REVIEW" if self.findings[run.run_id] else "COMPLETED"
        except asyncio.CancelledError:
            run.status, run.stage = "CANCELLED", "cancelled"
        except TimeoutError:
            run.status, run.error = "FAILED", "Globales Ausführungszeitlimit überschritten."
        except LLMError as exc:
            run.status, run.error = "FAILED", exc.detail
        except Exception:
            # ExceptionGroups/validation errors can contain prompts; store no raw exception.
            run.status, run.error = (
                "FAILED",
                "Analyse fehlgeschlagen. Modellverfügbarkeit, Schema und Budgets prüfen.",
            )
        finally:
            sampler.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await sampler
            run.finished_at = now()
            run.runtime_seconds = (run.finished_at - started).total_seconds()
            run.model_calls, run.tokens = budget.calls, budget.observed_tokens
            run.reserved_tokens, run.unknown_token_calls = (
                budget.reserved_tokens,
                budget.unknown_token_calls,
            )
            values = self.findings[run.run_id]
            run.findings_count = len(values)
            run.validated_count = sum(f.evidence_status == "VALIDATED" for f in values)
            run.unsupported_count = sum(
                f.evidence_status == "REJECTED"
                or any(r.verdict == "UNSUPPORTED" for r in f.reviews)
                for f in values
            )
            run.conflicts_count = sum(f.conflict for f in values)
            for agent in self.agents.for_run(run.run_id):
                if agent.status in {AgentStatus.CREATED, AgentStatus.QUEUED, AgentStatus.RUNNING}:
                    self.agents.transition(agent, AgentStatus.CANCELLED)

    async def _sample(self, run: RunRecord) -> None:
        while True:
            sample = sample_resources()
            try:
                loaded = (await self.provider.resources())["loaded_models"]
                sample["model_vram_bytes"] = sum(m["vram_bytes"] for m in loaded)
            except LLMError:
                sample["model_vram_bytes"] = None
            run.resource_samples.append(sample)
            run.resource_samples = run.resource_samples[-128:]
            for key in ("cpu_percent", "backend_rss_bytes", "model_vram_bytes"):
                if sample.get(key) is not None:
                    run.resource_peaks[key] = max(run.resource_peaks.get(key, 0), sample[key])
            await asyncio.sleep(2)

    def get(self, run_id: str) -> RunRecord:
        self.cleanup()
        if run_id not in self.runs:
            raise LLMError(404, "Analyse wurde nicht gefunden oder bereits bereinigt.")
        run = self.runs[run_id]
        budget = self.budgets.get(run_id)
        if budget:
            run.model_calls, run.tokens = budget.calls, budget.observed_tokens
            run.reserved_tokens, run.unknown_token_calls = (
                budget.reserved_tokens,
                budget.unknown_token_calls,
            )
        if run.status == "RUNNING":
            run.runtime_seconds = (now() - run.created_at).total_seconds()
        return run

    async def cancel(self, run_id: str) -> RunRecord:
        run = self.get(run_id)
        task = self.tasks[run_id]
        if not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            # A task cancelled before its first instruction never enters its finally block.
            if run.status == "QUEUED":
                run.status, run.stage, run.finished_at = "CANCELLED", "cancelled", now()
        return run

    async def close(self) -> None:
        await self.assessments.close()
        if self.maintenance:
            self.maintenance.cancel()
            with suppress(asyncio.CancelledError):
                await self.maintenance
        for run_id in list(self.tasks):
            if not self.tasks[run_id].done():
                with suppress(asyncio.CancelledError):
                    await self.cancel(run_id)
        for run_id in self.runs:
            self.store.remove(run_id)

    def human_review(self, run_id: str, finding_id: str, review: HumanReview) -> Finding:
        run = self.get(run_id)
        values = self.findings.get(run_id, [])
        finding = next(
            (f for f in values if f.finding_id == finding_id and f.run_id == run_id), None
        )
        if finding is None:
            raise LLMError(404, "Befund wurde nicht gefunden.")
        if run.status not in {"WAITING_FOR_REVIEW", "COMPLETED"}:
            raise LLMError(409, "Analyse ist noch nicht für die menschliche Prüfung bereit.")
        if review.edited_statement is not None and review.edited_statement != finding.statement:
            finding.original_statement = finding.original_statement or finding.statement
            finding.statement = review.edited_statement
            finding.superseded_reviews.extend(finding.reviews)
            finding.reviews = []
            finding.review_status = "PENDING"
            finding.evidence_status = "NOT_CHECKED"
            finding.evidence_detail = (
                "Befund wurde durch einen Menschen bearbeitet; "
                "vorherige Modellprüfung ist ungültig."
            )
        finding.human_status, finding.human_note = review.decision, review.note
        if all(f.human_status != "PENDING" for f in values):
            accepted = [f for f in values if f.human_status == "ACCEPTED"]
            # The LLM synthesis is NEVER included in a final report: it is not human-approved.
            run.final_report = "Menschlich freigegebene Befunde\n\n" + "\n\n".join(
                f"{f.category}: {f.statement}\nBeleg (Seite {f.page}): {f.quote}\n"
                f"Prüfstatus: {f.evidence_status}; Konflikt: {f.conflict}"
                for f in accepted
            )
            run.status = "COMPLETED"
        else:
            run.status, run.final_report = "WAITING_FOR_REVIEW", None
        run.validated_count = sum(f.evidence_status == "VALIDATED" for f in values)
        return finding

    async def model_status(self) -> list[dict]:
        try:
            local = {m.name: m for m in await self.provider.discover()}
            state = "available"
        except LLMError:
            local, state = {}, "unreachable"
        return [
            {
                **m.model_dump(),
                "availability": "available"
                if m.name in local
                else "missing"
                if state == "available"
                else state,
                "digest": local[m.name].digest if m.name in local else None,
            }
            for m in self.config.models.models.values()
        ]

    async def resources(self) -> dict:
        result = {
            **sample_resources(),
            "privacy_mode": self.config.policy.config.mode,
            "active_runs": sum(not t.done() for t in self.tasks.values()),
            "active_agents": sum(
                a.status == AgentStatus.RUNNING for a in self.agents.records.values()
            ),
            "limits": self.config.limits.model_dump(),
            "vram_scope": "Memory occupied by Ollama models, not GPU total/utilization",
        }
        try:
            result.update(await self.provider.resources())
        except LLMError:
            result.update(loaded_models=[], vram_unavailable=True)
        return result
