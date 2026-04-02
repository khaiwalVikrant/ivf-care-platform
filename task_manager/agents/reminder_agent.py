"""Reminder Sub-Agent — handles scheduling, delivery, acknowledgement, and escalation of reminders."""

from __future__ import annotations

from datetime import datetime

from task_manager.db.database import Database
from task_manager.models import CriticalityLevel, ErrorResponse, StepResult, WorkflowStep

NOTIFICATION_CHANNELS = ["in_app", "email", "sms"]


class ReminderSubAgent:
    """Sub-agent that manages reminders via the Database facade."""

    capabilities: list[str] = [
        "schedule_reminder",
        "deliver_reminder",
        "acknowledge_reminder",
        "escalate_reminder",
    ]

    def __init__(self, db: Database) -> None:
        self._db = db

    async def execute(self, step: WorkflowStep) -> StepResult:
        cap = step.capability

        if cap == "schedule_reminder":
            return await self._schedule_reminder(step)
        if cap == "deliver_reminder":
            return await self._deliver_reminder(step)
        if cap == "acknowledge_reminder":
            return await self._acknowledge_reminder(step)
        if cap == "escalate_reminder":
            return await self._escalate_reminder(step)

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

    async def _schedule_reminder(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        scheduled_at = inp.get("scheduled_at")
        if isinstance(scheduled_at, str):
            scheduled_at = datetime.fromisoformat(scheduled_at)

        criticality_raw = inp.get("criticality", "normal")
        criticality = CriticalityLevel(criticality_raw)

        reminder = await self._db.create_reminder(
            patient_id=inp.get("patient_id", ""),
            linked_record_id=inp.get("linked_record_id", ""),
            linked_record_type=inp.get("linked_record_type", ""),
            scheduled_at=scheduled_at,
            criticality=criticality,
            workflow_id=inp.get("workflow_id"),
        )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=reminder.model_dump(mode="json"),
        )

    async def _deliver_reminder(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        reminder_id: str = inp.get("reminder_id", "")

        reminder = await self._db.get_reminder(reminder_id)
        if reminder is None:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="REMINDER_NOT_FOUND",
                    message=f"Reminder {reminder_id!r} not found",
                ).model_dump_json(),
            )

        # Stub: return delivery payload (actual delivery via NotificationMCP)
        payload = {
            "reminder_id": reminder.id,
            "patient_id": reminder.patient_id,
            "linked_record_id": reminder.linked_record_id,
            "channels": NOTIFICATION_CHANNELS,
            "status": "delivered",
        }

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=payload,
        )

    async def _acknowledge_reminder(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        reminder_id: str = inp.get("reminder_id", "")

        updated = await self._db.update_reminder(
            reminder_id,
            acknowledged=True,
            acknowledged_at=datetime.utcnow(),
        )
        if updated is None:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="REMINDER_NOT_FOUND",
                    message=f"Reminder {reminder_id!r} not found",
                ).model_dump_json(),
            )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=updated.model_dump(mode="json"),
        )

    async def _escalate_reminder(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        reminder_id: str = inp.get("reminder_id", "")

        reminder = await self._db.get_reminder(reminder_id)
        if reminder is None:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="REMINDER_NOT_FOUND",
                    message=f"Reminder {reminder_id!r} not found",
                ).model_dump_json(),
            )

        new_count = reminder.escalation_count + 1
        updated = await self._db.update_reminder(
            reminder_id,
            escalation_count=new_count,
        )

        # Re-deliver via all channels
        payload = {
            "reminder_id": reminder.id,
            "patient_id": reminder.patient_id,
            "linked_record_id": reminder.linked_record_id,
            "channels": NOTIFICATION_CHANNELS,
            "escalation_count": new_count,
            "status": "escalated_and_redelivered",
        }

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output={**updated.model_dump(mode="json"), **payload},
        )
