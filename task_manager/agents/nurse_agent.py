"""Nurse Sub-Agent — handles nurse visit booking, assignment, notification, confirmation, and escalation."""

from __future__ import annotations

from datetime import datetime, timedelta

from task_manager.db.database import Database
from task_manager.models import ErrorResponse, StepResult, WorkflowStep

NURSE_POOL = ["nurse-001", "nurse-002", "nurse-003"]


class NurseSubAgent:
    """Sub-agent that manages nurse visits via the Database facade."""

    capabilities: list[str] = [
        "book_nurse_visit",
        "assign_nurse",
        "notify_nurse",
        "confirm_visit",
        "escalate_visit",
    ]

    def __init__(self, db: Database) -> None:
        self._db = db

    async def execute(self, step: WorkflowStep) -> StepResult:
        cap = step.capability

        if cap == "book_nurse_visit":
            return await self._book_nurse_visit(step)
        if cap == "assign_nurse":
            return await self._assign_nurse(step)
        if cap == "notify_nurse":
            return await self._notify_nurse(step)
        if cap == "confirm_visit":
            return await self._confirm_visit(step)
        if cap == "escalate_visit":
            return await self._escalate_visit(step)

        return StepResult(
            step_id=step.step_id,
            capability=cap,
            error=ErrorResponse(
                error_code="UNKNOWN_CAPABILITY",
                message=f"Unknown capability: {cap!r}",
            ).model_dump_json(),
        )

    # ------------------------------------------------------------------
    # Capability handlers
    # ------------------------------------------------------------------

    async def _book_nurse_visit(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        patient_id: str = inp.get("patient_id", "")
        medication_administration_id: str = inp.get("medication_administration_id", "")
        scheduled_at = inp.get("scheduled_at")
        if isinstance(scheduled_at, str):
            scheduled_at = datetime.fromisoformat(scheduled_at)

        # Find an available nurse (not booked within ±1 hour of scheduled_at)
        window_start = scheduled_at - timedelta(hours=1)
        window_end = scheduled_at + timedelta(hours=1)

        existing_visits = await self._db.query_nurse_visits()
        booked_nurses_at_time = {
            v.nurse_id
            for v in existing_visits
            if window_start <= v.scheduled_at <= window_end
        }

        available_nurse = None
        for nurse_id in NURSE_POOL:
            if nurse_id not in booked_nurses_at_time:
                available_nurse = nurse_id
                break

        if available_nurse is None:
            # Suggest nearest slot: 2 hours after requested time
            nearest_slot = scheduled_at + timedelta(hours=2)
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="NO_NURSE_AVAILABLE",
                    message="No nurse available at the requested time",
                    detail={"nearest_slot": nearest_slot.isoformat()},
                ).model_dump_json(),
            )

        visit = await self._db.create_nurse_visit(
            patient_id=patient_id,
            nurse_id=available_nurse,
            scheduled_at=scheduled_at,
            medication_administration_id=medication_administration_id,
            workflow_id=inp.get("workflow_id"),
        )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=visit.model_dump(mode="json"),
        )

    async def _assign_nurse(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        visit_id: str = inp.get("visit_id", "")
        nurse_id: str = inp.get("nurse_id", "")

        updated = await self._db.update_nurse_visit(visit_id, nurse_id=nurse_id)
        if updated is None:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="NURSE_VISIT_NOT_FOUND",
                    message=f"Nurse visit {visit_id!r} not found",
                ).model_dump_json(),
            )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=updated.model_dump(mode="json"),
        )

    async def _notify_nurse(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        visit_id: str = inp.get("visit_id", "")
        dose: str = inp.get("dose", "")

        visit = await self._db.get_nurse_visit(visit_id)
        if visit is None:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="NURSE_VISIT_NOT_FOUND",
                    message=f"Nurse visit {visit_id!r} not found",
                ).model_dump_json(),
            )

        # Stub: log notification (actual delivery via NotificationMCP)
        notification = {
            "nurse_id": visit.nurse_id,
            "patient_id": visit.patient_id,
            "scheduled_at": visit.scheduled_at.isoformat(),
            "dose": dose,
            "status": "notification_sent",
        }

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=notification,
        )

    async def _confirm_visit(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        visit_id: str = inp.get("visit_id", "")

        updated = await self._db.update_nurse_visit(visit_id, status="confirmed")
        if updated is None:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="NURSE_VISIT_NOT_FOUND",
                    message=f"Nurse visit {visit_id!r} not found",
                ).model_dump_json(),
            )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=updated.model_dump(mode="json"),
        )

    async def _escalate_visit(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        visit_id: str = inp.get("visit_id", "")

        updated = await self._db.update_nurse_visit(
            visit_id,
            status="escalated",
            escalated_at=datetime.utcnow(),
        )
        if updated is None:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="NURSE_VISIT_NOT_FOUND",
                    message=f"Nurse visit {visit_id!r} not found",
                ).model_dump_json(),
            )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=updated.model_dump(mode="json"),
        )
