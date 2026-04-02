"""Notes Sub-Agent — handles create_note and search_notes."""

from __future__ import annotations

from task_manager.db.database import Database
from task_manager.models import ErrorResponse, StepResult, WorkflowStep


class NotesSubAgent:
    """Sub-agent that manages notes via the Database facade."""

    capabilities: list[str] = ["create_note", "search_notes"]

    def __init__(self, db: Database) -> None:
        self._db = db

    async def execute(self, step: WorkflowStep) -> StepResult:
        cap = step.capability

        if cap == "create_note":
            return await self._create_note(step)
        if cap == "search_notes":
            return await self._search_notes(step)

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

    async def _create_note(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        body = inp.get("body", "")

        if not body or not str(body).strip():
            err = ErrorResponse(
                error_code="VALIDATION_ERROR",
                message="body must not be empty or whitespace-only",
                detail={"field": "body"},
            )
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=err.model_dump_json(),
            )

        try:
            note = await self._db.create_note(**inp)
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
            output=note.model_dump(mode="json"),
        )

    async def _search_notes(self, step: WorkflowStep) -> StepResult:
        inp = step.input
        notes = await self._db.search_notes(
            keyword=inp.get("keyword"),
            tag=inp.get("tag"),
        )
        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output={"notes": [n.model_dump(mode="json") for n in notes]},
        )
