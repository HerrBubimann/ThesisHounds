from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.core.runtime import AnalysisRuntime
from app.llm.errors import LLMError
from app.schemas.domain import AgentRecord, Finding, HumanReview, RunRecord, RunRequest

router = APIRouter(prefix="/api/v1")


def get_runtime(request: Request) -> AnalysisRuntime:
    return request.app.state.runtime


RuntimeDependency = Annotated[AnalysisRuntime, Depends(get_runtime)]


@router.get("/models/status")
async def model_status(runtime: RuntimeDependency) -> dict:
    return {"models": await runtime.model_status()}


@router.get("/agents")
async def agents(runtime: RuntimeDependency) -> dict:
    runtime.cleanup()
    for record in runtime.agents.records.values():
        runtime.agents.refresh(record)
    return {
        "definitions": runtime.config.agents.model_dump(),
        "agents": [a for a in runtime.agents.records.values() if runtime.access.allows(a.run_id)],
    }


@router.get("/agents/{agent_id}", response_model=AgentRecord)
async def agent(agent_id: str, runtime: RuntimeDependency) -> AgentRecord:
    runtime.cleanup()
    record = runtime.agents.records.get(agent_id)
    if record is None:
        raise LLMError(404, "Agent wurde nicht gefunden.")
    runtime.access.require(record.run_id)
    runtime.agents.refresh(record)
    return record


@router.get("/runs", response_model=list[RunRecord])
async def runs(runtime: RuntimeDependency) -> list[RunRecord]:
    runtime.cleanup()
    return [runtime.get(key) for key in list(runtime.runs) if runtime.access.allows(key)]


@router.post("/runs", response_model=RunRecord, status_code=202)
async def start_run(payload: RunRequest, runtime: RuntimeDependency) -> RunRecord:
    return runtime.start(payload)


@router.get("/runs/{run_id}", response_model=RunRecord)
async def run(run_id: UUID, runtime: RuntimeDependency) -> RunRecord:
    return runtime.get(str(run_id))


@router.post("/runs/{run_id}/cancel", response_model=RunRecord)
async def cancel(run_id: UUID, runtime: RuntimeDependency) -> RunRecord:
    return await runtime.cancel(str(run_id))


@router.delete("/runs/{run_id}", status_code=204)
async def delete(run_id: UUID, runtime: RuntimeDependency) -> None:
    await runtime.delete(str(run_id))


@router.get("/runs/{run_id}/graph")
async def graph(run_id: UUID, runtime: RuntimeDependency) -> dict:
    runtime.get(str(run_id))
    records = runtime.agents.for_run(str(run_id))
    for record in records:
        runtime.agents.refresh(record)
    return {
        "nodes": records,
        "edges": [
            {"parent": a.parent_agent, "child": a.agent_id} for a in records if a.parent_agent
        ],
    }


@router.get("/runs/{run_id}/findings", response_model=list[Finding])
async def findings(run_id: UUID, runtime: RuntimeDependency) -> list[Finding]:
    runtime.get(str(run_id))
    return runtime.findings[str(run_id)]


@router.post("/runs/{run_id}/findings/{finding_id}/review", response_model=Finding)
async def human_review(
    run_id: UUID, finding_id: UUID, payload: HumanReview, runtime: RuntimeDependency
) -> Finding:
    return runtime.human_review(str(run_id), str(finding_id), payload)


@router.get("/system/resources")
async def resources(runtime: RuntimeDependency) -> dict:
    return await runtime.resources()
