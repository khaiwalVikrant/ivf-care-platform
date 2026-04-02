"""Medication Sub-Agent — handles schedules, dose adjustments, administrations, and history."""

from __future__ import annotations

from datetime import date, datetime

from task_manager.db.database import Database
from task_manager.models import ErrorResponse, StepResult, WorkflowStep


class MedicationSubAgent:
    """Sub-agent that manages medication schedules and administrations via the Database facade."""

    capabilities: list[str] = [
        "create_schedule",
        "adjust_dose",
        "record_administration",
        "query_medication_history",
    ]

    def __init__(self, db: Database) -> None:
        self._db = db

    async def execute(self, step: WorkflowStep) -> StepResult:
        cap = step.capability

        if cap == "create_schedule":
            return await self._create_schedule(step)
        if cap == "adjust_dose":
            return await self._adjust_dose(step)
        if cap == "record_administration":
            return await self._record_administration(step)
        if cap == "query_medication_history":
            return await self._query_medication_history(step)

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

    async def _create_schedule(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)

        # Parse dates if provided as strings
        start_date = inp.get("start_date")
        end_date = inp.get("end_date")
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)

        schedule = await self._db.create_medication_schedule(
            patient_id=inp.get("patient_id", ""),
            cycle_id=inp.get("cycle_id", ""),
            drug_name=inp.get("drug_name", ""),
            dose=inp.get("dose", ""),
            frequency=inp.get("frequency", ""),
            route=inp.get("route", ""),
            start_date=start_date,
            end_date=end_date,
            workflow_id=inp.get("workflow_id"),
        )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=schedule.model_dump(mode="json"),
        )

    async def _adjust_dose(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        schedule_id: str = inp.get("schedule_id", "")
        new_dose: str = inp.get("new_dose", "")

        # Fetch existing schedule
        schedule = await self._db.get_medication_schedule(schedule_id)
        if schedule is None:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="MEDICATION_SCHEDULE_NOT_FOUND",
                    message=f"Medication schedule {schedule_id!r} not found",
                ).model_dump_json(),
            )

        # Append current dose to history before updating
        updated_history = list(schedule.dose_history) + [
            {
                "dose": schedule.dose,
                "effective_from": datetime.utcnow().isoformat(),
            }
        ]

        updated = await self._db.update_medication_schedule(
            schedule_id,
            dose=new_dose,
            dose_history=updated_history,
        )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=updated.model_dump(mode="json"),
        )

    async def _record_administration(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)

        administered_at = inp.get("administered_at")
        if isinstance(administered_at, str):
            administered_at = datetime.fromisoformat(administered_at)

        administration = await self._db.create_medication_administration(
            schedule_id=inp.get("schedule_id", ""),
            administered_by=inp.get("administered_by", ""),
            administered_at=administered_at,
            actual_dose=inp.get("actual_dose", ""),
            nurse_visit_id=inp.get("nurse_visit_id"),
            workflow_id=inp.get("workflow_id"),
        )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=administration.model_dump(mode="json"),
        )

    async def _query_medication_history(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        patient_id: str = inp.get("patient_id", "")
        cycle_id: str = inp.get("cycle_id", "")

        history = await self._db.query_medication_history(
            patient_id=patient_id,
            cycle_id=cycle_id,
        )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=history,
        )
