"""Task Manager Sub-Agent — handles create_task, update_task, query_tasks."""

from __future__ import annotations

from pydantic import ValidationError

from task_manager.db.database import Database
from task_manager.models import (
    ErrorResponse,
    Priority,
    StepResult,
    TaskStatus,
    WorkflowStep,
)


class TaskManagerSubAgent:
    """Sub-agent that manages tasks via the Database facade."""

    capabilities: list[str] = ["create_task", "update_task", "query_tasks"]

    def __init__(self, db: Database) -> None:
        self._db = db

    async def execute(self, step: WorkflowStep) -> StepResult:
        cap = step.capability

        if cap == "create_task":
            return await self._create_task(step)
        if cap == "update_task":
            return await self._update_task(step)
        if cap == "query_tasks":
            return await self._query_tasks(step)

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

    async def _create_task(self, step: WorkflowStep) -> StepResult:
        inp = step.input
        title = inp.get("title", "")

        if not title or not str(title).strip():
            err = ErrorResponse(
                error_code="VALIDATION_ERROR",
                message="title must not be empty or whitespace-only",
                detail={"field": "title"},
            )
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=err.model_dump_json(),
            )

        # Validate status if provided
        raw_status = inp.get("status")
        if raw_status is not None:
            try:
                inp = dict(inp)
                inp["status"] = TaskStatus(raw_status)
            except ValueError:
                err = ErrorResponse(
                    error_code="VALIDATION_ERROR",
                    message=f"invalid status: {raw_status!r}",
                    detail={"field": "status", "value": raw_status},
                )
                return StepResult(
                    step_id=step.step_id,
                    capability=step.capability,
                    error=err.model_dump_json(),
                )

        # Validate priority if provided
        raw_priority = inp.get("priority")
        if raw_priority is not None:
            try:
                inp = dict(inp)
                inp["priority"] = Priority(raw_priority)
            except ValueError:
                err = ErrorResponse(
                    error_code="VALIDATION_ERROR",
                    message=f"invalid priority: {raw_priority!r}",
                    detail={"field": "priority", "value": raw_priority},
                )
                return StepResult(
                    step_id=step.step_id,
                    capability=step.capability,
                    error=err.model_dump_json(),
                )

        try:
            task = await self._db.create_task(**inp)
        except (ValueError, ValidationError) as exc:
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
            output=task.model_dump(mode="json"),
        )

    async def _update_task(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        task_id = inp.pop("task_id", None)

        if not task_id:
            err = ErrorResponse(
                error_code="VALIDATION_ERROR",
                message="task_id is required for update_task",
                detail={"field": "task_id"},
            )
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=err.model_dump_json(),
            )

        # Coerce status/priority enums if provided
        if "status" in inp and inp["status"] is not None:
            try:
                inp["status"] = TaskStatus(inp["status"])
            except ValueError:
                err = ErrorResponse(
                    error_code="VALIDATION_ERROR",
                    message=f"invalid status: {inp['status']!r}",
                    detail={"field": "status"},
                )
                return StepResult(
                    step_id=step.step_id,
                    capability=step.capability,
                    error=err.model_dump_json(),
                )

        if "priority" in inp and inp["priority"] is not None:
            try:
                inp["priority"] = Priority(inp["priority"])
            except ValueError:
                err = ErrorResponse(
                    error_code="VALIDATION_ERROR",
                    message=f"invalid priority: {inp['priority']!r}",
                    detail={"field": "priority"},
                )
                return StepResult(
                    step_id=step.step_id,
                    capability=step.capability,
                    error=err.model_dump_json(),
                )

        task = await self._db.update_task(task_id, **inp)

        if task is None:
            err = ErrorResponse(
                error_code="TASK_NOT_FOUND",
                message=f"Task {task_id!r} does not exist",
                detail={"task_id": task_id},
            )
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=err.model_dump_json(),
            )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=task.model_dump(mode="json"),
        )

    async def _query_tasks(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)

        if "status" in inp and inp["status"] is not None:
            try:
                inp["status"] = TaskStatus(inp["status"])
            except ValueError:
                err = ErrorResponse(
                    error_code="VALIDATION_ERROR",
                    message=f"invalid status: {inp['status']!r}",
                    detail={"field": "status"},
                )
                return StepResult(
                    step_id=step.step_id,
                    capability=step.capability,
                    error=err.model_dump_json(),
                )

        if "priority" in inp and inp["priority"] is not None:
            try:
                inp["priority"] = Priority(inp["priority"])
            except ValueError:
                err = ErrorResponse(
                    error_code="VALIDATION_ERROR",
                    message=f"invalid priority: {inp['priority']!r}",
                    detail={"field": "priority"},
                )
                return StepResult(
                    step_id=step.step_id,
                    capability=step.capability,
                    error=err.model_dump_json(),
                )

        tasks = await self._db.query_tasks(**inp)
        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output={"tasks": [t.model_dump(mode="json") for t in tasks]},
        )
