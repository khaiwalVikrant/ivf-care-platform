"""Pathology Sub-Agent — handles test ordering, sample status, results, and queries."""

from __future__ import annotations

from task_manager.db.database import Database
from task_manager.models import ErrorResponse, IVFStage, StepResult, WorkflowStep

# Keywords that suggest a test is inappropriate at baseline stage
_EMBRYO_KEYWORDS = {"embryo", "transfer"}


def _is_stage_inappropriate(stage: IVFStage, test_name: str) -> bool:
    """Simple heuristic: flag embryo/transfer tests at baseline stage."""
    if stage == IVFStage.baseline:
        lower = test_name.lower()
        return any(kw in lower for kw in _EMBRYO_KEYWORDS)
    return False


def _parse_reference_range(reference_range: str) -> tuple[float, float] | None:
    """Parse 'min-max' format, e.g. '2.5-10.0'. Returns (min, max) or None."""
    parts = reference_range.split("-")
    if len(parts) == 2:
        try:
            return float(parts[0]), float(parts[1])
        except ValueError:
            pass
    return None


class PathologySubAgent:
    """Sub-agent that manages pathology orders and results via the Database facade."""

    capabilities: list[str] = [
        "order_test",
        "update_sample_status",
        "store_result",
        "query_results",
    ]

    def __init__(self, db: Database) -> None:
        self._db = db

    async def execute(self, step: WorkflowStep) -> StepResult:
        cap = step.capability

        if cap == "order_test":
            return await self._order_test(step)
        if cap == "update_sample_status":
            return await self._update_sample_status(step)
        if cap == "store_result":
            return await self._store_result(step)
        if cap == "query_results":
            return await self._query_results(step)

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

    async def _order_test(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)

        patient_id: str = inp.get("patient_id", "")
        cycle_id: str = inp.get("cycle_id", "")
        ivf_stage_raw: str = inp.get("ivf_stage", "baseline")
        tests: list[str] = inp.get("tests", [])

        try:
            ivf_stage = IVFStage(ivf_stage_raw)
        except ValueError:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="VALIDATION_ERROR",
                    message=f"Invalid IVF stage: {ivf_stage_raw!r}",
                ).model_dump_json(),
            )

        # Check for stage-inappropriate tests (warning only — order still proceeds)
        warnings: list[str] = []
        for test in tests:
            if _is_stage_inappropriate(ivf_stage, test):
                warnings.append(
                    f"Test '{test}' may be inappropriate at stage '{ivf_stage.value}'"
                )

        order = await self._db.create_pathology_order(
            patient_id=patient_id,
            cycle_id=cycle_id,
            ivf_stage=ivf_stage,
            tests=tests,
            workflow_id=inp.get("workflow_id"),
        )

        output = order.model_dump(mode="json")
        if warnings:
            output["warnings"] = warnings

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=output,
        )

    async def _update_sample_status(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        order_id: str = inp.get("order_id", "")
        new_status: str = inp.get("status", "")

        updated = await self._db.update_pathology_order(
            order_id, collection_status=new_status
        )
        if updated is None:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="PATHOLOGY_ORDER_NOT_FOUND",
                    message=f"Pathology order {order_id!r} not found",
                ).model_dump_json(),
            )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=updated.model_dump(mode="json"),
        )

    async def _store_result(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        order_id: str = inp.get("order_id", "")
        test_name: str = inp.get("test_name", "")
        value: str = inp.get("value", "")
        unit: str = inp.get("unit", "")
        reference_range: str = inp.get("reference_range", "")

        # Determine abnormality
        abnormal = False
        parsed = _parse_reference_range(reference_range)
        if parsed is not None:
            try:
                numeric_value = float(value)
                low, high = parsed
                abnormal = numeric_value < low or numeric_value > high
            except ValueError:
                pass  # Non-numeric value — leave abnormal=False

        result = await self._db.create_pathology_result(
            order_id=order_id,
            test_name=test_name,
            value=value,
            unit=unit,
            reference_range=reference_range,
            abnormal=abnormal,
        )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=result.model_dump(mode="json"),
        )

    async def _query_results(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        patient_id: str | None = inp.get("patient_id")
        cycle_id: str | None = inp.get("cycle_id")

        results = await self._db.query_pathology_results(
            patient_id=patient_id,
            cycle_id=cycle_id,
        )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output={"results": [r.model_dump(mode="json") for r in results]},
        )
