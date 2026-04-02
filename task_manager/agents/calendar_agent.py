"""Calendar Sub-Agent — handles create_event and query_events."""

from __future__ import annotations

from datetime import datetime

from task_manager.db.database import Database
from task_manager.models import ErrorResponse, StepResult, WorkflowStep


class CalendarSubAgent:
    """Sub-agent that manages calendar events via the Database facade."""

    capabilities: list[str] = ["create_event", "query_events"]

    def __init__(self, db: Database) -> None:
        self._db = db

    async def execute(self, step: WorkflowStep) -> StepResult:
        cap = step.capability

        if cap == "create_event":
            return await self._create_event(step)
        if cap == "query_events":
            return await self._query_events(step)

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

    async def _create_event(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)

        # Parse datetimes if provided as strings
        start_time = inp.get("start_time")
        end_time = inp.get("end_time")

        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
            inp["start_time"] = start_time
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)
            inp["end_time"] = end_time

        # Validate time ordering
        if start_time is not None and end_time is not None:
            if start_time > end_time:
                err = ErrorResponse(
                    error_code="INVALID_TIME_RANGE",
                    message="start_time must be less than or equal to end_time",
                    detail={
                        "start_time": str(start_time),
                        "end_time": str(end_time),
                    },
                )
                return StepResult(
                    step_id=step.step_id,
                    capability=step.capability,
                    error=err.model_dump_json(),
                )

        try:
            event = await self._db.create_event(**inp)
        except (ValueError, TypeError) as exc:
            err = ErrorResponse(
                error_code="VALIDATION_ERROR",
                message=str(exc),
            )
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=err.model_dump_json(),
            )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=event.model_dump(mode="json"),
        )

    async def _query_events(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)

        # Parse datetime strings if needed
        for key in ("start_from", "start_to"):
            if key in inp and isinstance(inp[key], str):
                inp[key] = datetime.fromisoformat(inp[key])

        events = await self._db.query_events(
            start_from=inp.get("start_from"),
            start_to=inp.get("start_to"),
        )
        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output={"events": [e.model_dump(mode="json") for e in events]},
        )
