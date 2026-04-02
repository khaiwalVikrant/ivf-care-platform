"""TaskOrchestrator — coordinates sub-agents, manages workflow lifecycle, and tracks IVF stages."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from task_manager.db.database import Database
from task_manager.models import (
    ErrorResponse,
    IVFCycle,
    IVFStage,
    StepTransition,
    Workflow,
    WorkflowStatus,
    WorkflowStep,
)

# Ordered list of IVF stages for sequential validation
_IVF_STAGE_ORDER: list[IVFStage] = [
    IVFStage.baseline,
    IVFStage.stimulation,
    IVFStage.trigger,
    IVFStage.retrieval,
    IVFStage.fertilisation,
    IVFStage.transfer,
    IVFStage.luteal_support,
    IVFStage.pregnancy_test,
]

# Keyword → capability mapping for request parsing
_KEYWORD_CAPABILITY: list[tuple[list[str], str]] = [
    (["nurse", "injection"], "book_nurse_visit"),
    (["reminder"], "schedule_reminder"),
    (["cost", "price"], "benchmark_price"),
    (["event", "appointment", "schedule"], "create_event"),
    (["note"], "create_note"),
    (["task"], "create_task"),
]


def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


class TaskOrchestrator:
    """Orchestrates sub-agents to fulfil natural-language requests."""

    def __init__(self, sub_agents: list[Any], db: Database) -> None:
        self._db = db
        # Build capability → sub_agent registry
        self._registry: dict[str, Any] = {}
        for agent in sub_agents:
            for cap in getattr(agent, "capabilities", []):
                self._registry[cap] = agent

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def submit(self, request: str) -> Workflow | ErrorResponse:
        """Parse *request* into a Workflow and persist it.

        Returns an ErrorResponse if the request cannot be mapped to any capability.
        """
        capability = self._parse_capability(request)
        if capability is None:
            return ErrorResponse(
                error_code="UNPARSEABLE_REQUEST",
                message="Could not map request to a known capability",
                detail={"request": request},
            )

        step_id = _new_id()
        workflow = await self._db.create_workflow(
            request=request,
            steps=[{"step_id": step_id, "capability": capability, "input": {"request": request}}],
        )
        return workflow

    async def execute(self, workflow: Workflow) -> dict[str, Any]:
        """Execute all steps in *workflow* in order.

        Each failing step is retried once.  On unrecoverable failure the workflow
        is rolled back and marked failed.  Returns a summary dict.
        """
        await self._db.update_workflow_status(workflow.workflow_id, WorkflowStatus.running)

        for step in workflow.steps:
            # Transition step → running
            transition = StepTransition(
                from_status=WorkflowStatus.pending,
                to_status=WorkflowStatus.running,
                timestamp=_now(),
            )
            await self._db.update_workflow_step(
                workflow.workflow_id,
                step.step_id,
                WorkflowStatus.running,
                transition=transition,
            )

            agent = self._registry.get(step.capability)
            if agent is None:
                error_msg = f"No agent registered for capability '{step.capability}'"
                await self._fail_step(workflow.workflow_id, step, error_msg)
                await self._rollback(workflow.workflow_id, step.step_id, error_msg)
                return self._failure_summary(workflow, step.step_id, error_msg)

            # Execute with one retry
            result = await self._execute_with_retry(agent, step)

            if result.error:
                await self._fail_step(workflow.workflow_id, step, result.error)
                await self._rollback(workflow.workflow_id, step.step_id, result.error)
                return self._failure_summary(workflow, step.step_id, result.error)

            # Success
            transition = StepTransition(
                from_status=WorkflowStatus.running,
                to_status=WorkflowStatus.completed,
                timestamp=_now(),
            )
            await self._db.update_workflow_step(
                workflow.workflow_id,
                step.step_id,
                WorkflowStatus.completed,
                output=result.output,
                transition=transition,
            )

        completed_at = _now()
        await self._db.update_workflow_status(
            workflow.workflow_id,
            WorkflowStatus.completed,
            completed_at=completed_at,
        )
        updated = await self._db.get_workflow(workflow.workflow_id)
        return updated.model_dump(mode="json") if updated else {"workflow_id": workflow.workflow_id, "status": "completed"}

    async def get_status(self, workflow_id: str) -> Workflow | None:
        """Return the current Workflow record, or None if not found."""
        return await self._db.get_workflow(workflow_id)

    async def transition_ivf_stage(self, cycle_id: str, new_stage: IVFStage) -> IVFCycle | ErrorResponse:
        """Validate sequential order and advance the IVF cycle to *new_stage*."""
        cycle = await self._db.get_ivf_cycle(cycle_id)
        if cycle is None:
            return ErrorResponse(
                error_code="CYCLE_NOT_FOUND",
                message=f"IVF cycle '{cycle_id}' not found",
                detail={"cycle_id": cycle_id},
            )

        current_idx = _IVF_STAGE_ORDER.index(cycle.current_stage)
        new_idx = _IVF_STAGE_ORDER.index(new_stage)

        if new_idx != current_idx + 1:
            return ErrorResponse(
                error_code="INVALID_STAGE_TRANSITION",
                message=(
                    f"Cannot transition from '{cycle.current_stage.value}' to '{new_stage.value}'. "
                    f"Expected next stage: '{_IVF_STAGE_ORDER[current_idx + 1].value}'"
                    if current_idx + 1 < len(_IVF_STAGE_ORDER)
                    else f"Cannot transition from '{cycle.current_stage.value}' — already at final stage"
                ),
                detail={
                    "cycle_id": cycle_id,
                    "current_stage": cycle.current_stage.value,
                    "requested_stage": new_stage.value,
                },
            )

        # Append to stage history
        history = list(cycle.stage_history)
        history.append({
            "stage": new_stage.value,
            "transitioned_at": _now().isoformat(),
        })

        updated = await self._db.update_ivf_cycle(
            cycle_id,
            current_stage=new_stage,
            stage_history=history,
        )
        return updated  # type: ignore[return-value]

    async def get_cycle_summary(self, cycle_id: str) -> dict[str, Any]:
        """Return a dict with the IVF cycle and all linked records."""
        cycle = await self._db.get_ivf_cycle(cycle_id)
        if cycle is None:
            return ErrorResponse(
                error_code="CYCLE_NOT_FOUND",
                message=f"IVF cycle '{cycle_id}' not found",
                detail={"cycle_id": cycle_id},
            ).model_dump()

        # Gather linked records
        appointments = await self._db.query_appointments(patient_id=cycle.patient_id)
        pathology_orders = await self._db.query_pathology_results(cycle_id=cycle_id)
        cost_records = await self._db.query_cost_records(
            patient_id=cycle.patient_id, cycle_id=cycle_id
        )
        nurse_visits = await self._db.query_nurse_visits(patient_id=cycle.patient_id)
        reminders = await self._db.query_reminders(patient_id=cycle.patient_id)
        med_history = await self._db.query_medication_history(
            patient_id=cycle.patient_id, cycle_id=cycle_id
        )

        return {
            "cycle": cycle.model_dump(mode="json"),
            "appointments": [a.model_dump(mode="json") for a in appointments],
            "pathology_results": [r.model_dump(mode="json") for r in pathology_orders],
            "medication_schedules": med_history.get("schedules", []),
            "medication_administrations": med_history.get("administrations", []),
            "nurse_visits": [v.model_dump(mode="json") for v in nurse_visits],
            "reminders": [r.model_dump(mode="json") for r in reminders],
            "cost_records": [c.model_dump(mode="json") for c in cost_records],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_capability(self, request: str) -> str | None:
        lower = request.lower()
        for keywords, capability in _KEYWORD_CAPABILITY:
            if any(kw in lower for kw in keywords):
                return capability
        return None

    async def _execute_with_retry(self, agent: Any, step: WorkflowStep) -> Any:
        """Execute *step* via *agent*, retrying once on error."""
        result = await agent.execute(step)
        if result.error:
            # Retry once
            result = await agent.execute(step)
        return result

    async def _fail_step(
        self, workflow_id: str, step: WorkflowStep, error_msg: str
    ) -> None:
        transition = StepTransition(
            from_status=WorkflowStatus.running,
            to_status=WorkflowStatus.failed,
            timestamp=_now(),
            detail=error_msg,
        )
        await self._db.update_workflow_step(
            workflow_id,
            step.step_id,
            WorkflowStatus.failed,
            error=error_msg,
            transition=transition,
        )

    async def _rollback(
        self, workflow_id: str, failure_step_id: str, failure_detail: str
    ) -> None:
        await self._db.rollback_workflow(workflow_id)
        await self._db.update_workflow_status(
            workflow_id,
            WorkflowStatus.failed,
            failure_step=failure_step_id,
            failure_detail=failure_detail,
        )

    def _failure_summary(
        self, workflow: Workflow, failure_step_id: str, failure_detail: str
    ) -> dict[str, Any]:
        return {
            "workflow_id": workflow.workflow_id,
            "status": "failed",
            "failure_step": failure_step_id,
            "failure_detail": failure_detail,
        }
