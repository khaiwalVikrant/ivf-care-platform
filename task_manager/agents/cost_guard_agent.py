"""CostGuard Sub-Agent — handles price benchmarking, cost tracking, bill auditing, and insurance summaries."""

from __future__ import annotations

from task_manager.db.database import Database
from task_manager.models import ErrorResponse, IVFStage, StepResult, WorkflowStep

# Tests appropriate per IVF stage (simple lookup)
_STAGE_APPROPRIATE_TESTS: dict[str, list[str]] = {
    IVFStage.baseline.value: ["AMH blood test", "FSH blood test", "Antral follicle count ultrasound", "Semen analysis"],
    IVFStage.stimulation.value: ["Antral follicle count ultrasound", "FSH blood test"],
    IVFStage.trigger.value: ["Antral follicle count ultrasound"],
    IVFStage.retrieval.value: ["Semen analysis"],
    IVFStage.fertilisation.value: [],
    IVFStage.transfer.value: [],
    IVFStage.luteal_support.value: [],
    IVFStage.pregnancy_test.value: [],
}


class CostGuardSubAgent:
    """Sub-agent that manages cost records and price benchmarks via the Database facade."""

    capabilities: list[str] = [
        "benchmark_price",
        "validate_test_necessity",
        "track_cost",
        "audit_bill",
        "generate_insurance_summary",
    ]

    def __init__(self, db: Database) -> None:
        self._db = db

    async def execute(self, step: WorkflowStep) -> StepResult:
        cap = step.capability

        if cap == "benchmark_price":
            return await self._benchmark_price(step)
        if cap == "validate_test_necessity":
            return await self._validate_test_necessity(step)
        if cap == "track_cost":
            return await self._track_cost(step)
        if cap == "audit_bill":
            return await self._audit_bill(step)
        if cap == "generate_insurance_summary":
            return await self._generate_insurance_summary(step)

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

    async def _benchmark_price(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        item_name: str = inp.get("item_name", "")
        quoted_price: float = float(inp.get("quoted_price", 0))

        benchmark = await self._db.get_price_benchmark(item_name)
        if benchmark is None:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                output={
                    "item_name": item_name,
                    "price_alert": False,
                    "message": "No benchmark available for this item",
                },
            )

        threshold = benchmark.benchmark_price * 1.15
        if quoted_price > threshold:
            overage_percent = ((quoted_price - benchmark.benchmark_price) / benchmark.benchmark_price) * 100
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                output={
                    "item_name": item_name,
                    "price_alert": True,
                    "quoted_price": quoted_price,
                    "benchmark_price": benchmark.benchmark_price,
                    "overage_percent": round(overage_percent, 2),
                    "suggested_price": benchmark.benchmark_price,
                },
            )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output={
                "item_name": item_name,
                "price_alert": False,
                "quoted_price": quoted_price,
                "benchmark_price": benchmark.benchmark_price,
            },
        )

    async def _validate_test_necessity(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        test_name: str = inp.get("test_name", "")
        ivf_stage: str = inp.get("ivf_stage", "")

        appropriate_tests = _STAGE_APPROPRIATE_TESTS.get(ivf_stage, [])
        if test_name not in appropriate_tests:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                output={
                    "test_name": test_name,
                    "ivf_stage": ivf_stage,
                    "flagged": True,
                    "reason": f"Test '{test_name}' is not typically indicated at stage '{ivf_stage}'",
                },
            )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output={
                "test_name": test_name,
                "ivf_stage": ivf_stage,
                "flagged": False,
            },
        )

    async def _track_cost(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        patient_id: str = inp.get("patient_id", "")
        cycle_id: str = inp.get("cycle_id", "")

        if not patient_id or not cycle_id:
            return StepResult(
                step_id=step.step_id,
                capability=step.capability,
                error=ErrorResponse(
                    error_code="COST_RECORD_LINK_ERROR",
                    message="patient_id and cycle_id are required to create a cost record",
                ).model_dump_json(),
            )

        record = await self._db.create_cost_record(
            patient_id=patient_id,
            cycle_id=cycle_id,
            category=inp.get("category", ""),
            amount=float(inp.get("amount", 0)),
            linked_record_id=inp.get("linked_record_id", ""),
            currency=inp.get("currency", "INR"),
            flagged_unnecessary=bool(inp.get("flagged_unnecessary", False)),
            workflow_id=inp.get("workflow_id"),
        )

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output=record.model_dump(mode="json"),
        )

    async def _audit_bill(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        patient_id: str = inp.get("patient_id", "")
        cycle_id: str = inp.get("cycle_id", "")
        # line_items: list of {"linked_record_id": str, "billed_amount": float}
        line_items: list[dict] = inp.get("line_items", [])

        records = await self._db.query_cost_records(patient_id=patient_id, cycle_id=cycle_id)
        records_by_id = {r.linked_record_id: r for r in records}

        discrepancies = []
        for item in line_items:
            record_id = item.get("linked_record_id", "")
            billed = float(item.get("billed_amount", 0))
            record = records_by_id.get(record_id)
            if record is None:
                discrepancies.append({
                    "linked_record_id": record_id,
                    "billed_amount": billed,
                    "recorded_amount": None,
                    "discrepancy": billed,
                    "flagged": True,
                    "reason": "No matching cost record found",
                })
            elif billed != record.amount:
                discrepancies.append({
                    "linked_record_id": record_id,
                    "billed_amount": billed,
                    "recorded_amount": record.amount,
                    "discrepancy": billed - record.amount,
                    "flagged": True,
                })

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output={
                "patient_id": patient_id,
                "cycle_id": cycle_id,
                "total_line_items": len(line_items),
                "discrepancies": discrepancies,
                "clean": len(discrepancies) == 0,
            },
        )

    async def _generate_insurance_summary(self, step: WorkflowStep) -> StepResult:
        inp = dict(step.input)
        patient_id: str = inp.get("patient_id", "")
        cycle_id: str = inp.get("cycle_id", "")

        records = await self._db.query_cost_records(patient_id=patient_id, cycle_id=cycle_id)

        # Group by category
        by_category: dict[str, list] = {}
        for r in records:
            by_category.setdefault(r.category, []).append(r)

        summary = []
        grand_total = 0.0
        for category, items in by_category.items():
            subtotal = sum(i.amount for i in items)
            grand_total += subtotal
            summary.append({
                "category": category,
                "items": [i.model_dump(mode="json") for i in items],
                "subtotal": subtotal,
                "currency": items[0].currency if items else "INR",
            })

        return StepResult(
            step_id=step.step_id,
            capability=step.capability,
            output={
                "patient_id": patient_id,
                "cycle_id": cycle_id,
                "categories": summary,
                "grand_total": grand_total,
                "currency": "INR",
            },
        )
