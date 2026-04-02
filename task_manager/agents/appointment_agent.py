"""Appointment Sub-Agent — handles booking, cancellation, rescheduling, and notes."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from task_manager.db.database import Database
from task_manager.models import AppointmentType, ErrorResponse, StepResult, WorkflowStep

# Pre-appointment checklists per appointment type
_CHECKLISTS: dict[AppointmentType, list[str]] = {
    AppointmentType.consultation: [
        "Bring previous medical records",
        "Bring ID proof",
        "List current medications",
    ],
    AppointmentType.ultrasound: [
        "Drink 1 litre of water 1 hour before",
        "Bring previous scan reports",
    ],
    AppointmentType.egg_retrieval: [
        "Fast for 6 hours before procedure",
        "Arrange transport home",
        "Bring companion",
    ],
    AppointmentType.embryo_transfer: [
        "Full bladder required",
        "Bring embryo transfer consent form",
        "Wear comfortable clothing",
    ],
}

_CONFLICT_WINDOW = timedelta(hours=1)


class AppointmentSubAgent:
    """Sub-agent that manages IVF appointments via the Database facade."""

    capabilities: list[str] = [
        "book_appointment",
        "cancel_appointment",
        "reschedule_appointment",
        "add_post_notes",
        "get_appointment",
    ]

    def __init__(self, db: Database) -> None:
        self._db = db

    async def execute(self, step: WorkflowStep) -> StepResult:
        cap = step.capability

        if cap == "book_appointment":
            return await self._book_appointment(step)
        if cap == "cancel_appointment":
            return await self._cancel_appointment(step)
        if cap == "reschedule_appointment":
            return await self._reschedule_appointment(step)
        if cap == "add_post_notes":
            return await self._add_post_notes(step)
        if cap == "get_appointment":
            return await self._get_appointment(step)

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

    async def _book_appointment(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)

        patient_id: str = inp.get("patient_id", "")
        appt_type_raw: str = inp.get("type", "")
        datetime_raw = inp.get("datetime")
        location: str = inp.get("location", "")

        # Parse appointment type
        try:
            appt_type = AppointmentType(appt_type_raw)
        except ValueError:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="VALIDATION_ERROR",
                    message=f"Invalid appointment type: {appt_type_raw!r}",
                ).model_dump_json(),
            )

        # Parse datetime
        if isinstance(datetime_raw, str):
            datetime_raw = datetime.fromisoformat(datetime_raw)
        appt_dt: datetime = datetime_raw

        # Conflict detection: check existing appointments for same patient
        existing = await self._db.query_appointments(patient_id=patient_id)
        for existing_appt in existing:
            diff = abs((existing_appt.datetime - appt_dt).total_seconds())
            if diff < _CONFLICT_WINDOW.total_seconds():
                return StepResult(
                    step_id=step.step_id,
                    capability=step.capability,
                    error=ErrorResponse(
                        error_code="APPOINTMENT_CONFLICT",
                        message="An appointment already exists within 1 hour of the requested time",
                        detail={"conflicting_id": existing_appt.id},
                    ).model_dump_json(),
                )

        checklist = _CHECKLISTS.get(appt_type, [])

        appointment = await self._db.create_appointment(
            patient_id=patient_id,
            type=appt_type,
            datetime_=appt_dt,
            location=location,
            checklist=checklist,
            workflow_id=inp.get("workflow_id"),
        )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=appointment.model_dump(mode="json"),
        )

    async def _cancel_appointment(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        appointment_id: str = inp.get("appointment_id", "")

        updated = await self._db.update_appointment(appointment_id, status="cancelled")
        if updated is None:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="APPOINTMENT_NOT_FOUND",
                    message=f"Appointment {appointment_id!r} not found",
                ).model_dump_json(),
            )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=updated.model_dump(mode="json"),
        )

    async def _reschedule_appointment(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        appointment_id: str = inp.get("appointment_id", "")
        new_datetime_raw = inp.get("new_datetime")

        if isinstance(new_datetime_raw, str):
            new_datetime_raw = datetime.fromisoformat(new_datetime_raw)

        updated = await self._db.update_appointment(appointment_id, datetime=new_datetime_raw)
        if updated is None:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="APPOINTMENT_NOT_FOUND",
                    message=f"Appointment {appointment_id!r} not found",
                ).model_dump_json(),
            )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=updated.model_dump(mode="json"),
        )

    async def _add_post_notes(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        appointment_id: str = inp.get("appointment_id", "")
        notes: str = inp.get("notes", "")

        updated = await self._db.update_appointment(appointment_id, post_notes=notes)
        if updated is None:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="APPOINTMENT_NOT_FOUND",
                    message=f"Appointment {appointment_id!r} not found",
                ).model_dump_json(),
            )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=updated.model_dump(mode="json"),
        )

    async def _get_appointment(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        appointment_id: str = inp.get("appointment_id", "")

        appointment = await self._db.get_appointment(appointment_id)
        if appointment is None:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="APPOINTMENT_NOT_FOUND",
                    message=f"Appointment {appointment_id!r} not found",
                ).model_dump_json(),
            )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=appointment.model_dump(mode="json"),
        )
