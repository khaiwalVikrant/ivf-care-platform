"""Unit tests for CostGuardSubAgent."""

from __future__ import annotations

import json

import pytest

from task_manager.agents.cost_guard_agent import CostGuardSubAgent
from task_manager.db.database import Database
from task_manager.models import WorkflowStatus, WorkflowStep


def make_step(capability: str, input_data: dict, step_id: str = "step-1") -> WorkflowStep:
    return WorkflowStep(
        step_id=step_id,
        capability=capability,
        input=input_data,
        status=WorkflowStatus.pending,
    )


@pytest.fixture
async def agent(tmp_path):
    db = Database(url=f"sqlite+aiosqlite:///{tmp_path}/test.db")
    await db.init_db()
    # Seed a benchmark for tests
    await db.create_price_benchmark(
        item_name="AMH blood test",
        item_type="test",
        benchmark_price=1200.0,
    )
    return CostGuardSubAgent(db=db)


# ---------------------------------------------------------------------------
# benchmark_price
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_benchmark_price_exactly_115_percent_no_alert(agent):
    """Price at exactly 115% of benchmark should NOT trigger alert."""
    quoted = 1200.0 * 1.15  # exactly 1380.0
    step = make_step("benchmark_price", {
        "item_name": "AMH blood test",
        "quoted_price": quoted,
    })
    result = await agent.execute(step)
    assert result.error is None
    assert result.output["price_alert"] is False


@pytest.mark.asyncio
async def test_benchmark_price_above_115_percent_triggers_alert(agent):
    """Price at 115.01% of benchmark SHOULD trigger alert."""
    quoted = 1200.0 * 1.1501  # just above 15% threshold
    step = make_step("benchmark_price", {
        "item_name": "AMH blood test",
        "quoted_price": quoted,
    })
    result = await agent.execute(step)
    assert result.error is None
    assert result.output["price_alert"] is True
    assert result.output["suggested_price"] == 1200.0
    assert result.output["overage_percent"] > 15.0


@pytest.mark.asyncio
async def test_benchmark_price_below_threshold_no_alert(agent):
    step = make_step("benchmark_price", {
        "item_name": "AMH blood test",
        "quoted_price": 1000.0,
    })
    result = await agent.execute(step)
    assert result.error is None
    assert result.output["price_alert"] is False


@pytest.mark.asyncio
async def test_benchmark_price_no_benchmark_available(agent):
    step = make_step("benchmark_price", {
        "item_name": "Unknown Item",
        "quoted_price": 9999.0,
    })
    result = await agent.execute(step)
    assert result.error is None
    assert result.output["price_alert"] is False
    assert "No benchmark available" in result.output["message"]


# ---------------------------------------------------------------------------
# track_cost
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_track_cost_creates_cost_record(agent):
    step = make_step("track_cost", {
        "patient_id": "p1",
        "cycle_id": "c1",
        "category": "medication",
        "amount": 6200.0,
        "linked_record_id": "sched-1",
    })
    result = await agent.execute(step)
    assert result.error is None
    assert result.output["patient_id"] == "p1"
    assert result.output["cycle_id"] == "c1"
    assert result.output["amount"] == 6200.0
    assert result.output["category"] == "medication"


@pytest.mark.asyncio
async def test_track_cost_empty_patient_id_returns_error(agent):
    step = make_step("track_cost", {
        "patient_id": "",
        "cycle_id": "c1",
        "category": "medication",
        "amount": 100.0,
        "linked_record_id": "sched-1",
    })
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "COST_RECORD_LINK_ERROR"


@pytest.mark.asyncio
async def test_track_cost_empty_cycle_id_returns_error(agent):
    step = make_step("track_cost", {
        "patient_id": "p1",
        "cycle_id": "",
        "category": "medication",
        "amount": 100.0,
        "linked_record_id": "sched-1",
    })
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "COST_RECORD_LINK_ERROR"


# ---------------------------------------------------------------------------
# audit_bill
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_bill_flags_discrepancies(agent):
    # Create a cost record
    track_step = make_step("track_cost", {
        "patient_id": "p1",
        "cycle_id": "c1",
        "category": "test",
        "amount": 1200.0,
        "linked_record_id": "order-1",
    }, step_id="step-track")
    await agent.execute(track_step)

    # Audit with a different billed amount
    audit_step = make_step("audit_bill", {
        "patient_id": "p1",
        "cycle_id": "c1",
        "line_items": [
            {"linked_record_id": "order-1", "billed_amount": 1500.0},
        ],
    })
    result = await agent.execute(audit_step)
    assert result.error is None
    assert result.output["clean"] is False
    assert len(result.output["discrepancies"]) == 1
    assert result.output["discrepancies"][0]["flagged"] is True
    assert result.output["discrepancies"][0]["discrepancy"] == 300.0


@pytest.mark.asyncio
async def test_audit_bill_no_discrepancies(agent):
    track_step = make_step("track_cost", {
        "patient_id": "p1",
        "cycle_id": "c1",
        "category": "test",
        "amount": 1200.0,
        "linked_record_id": "order-1",
    }, step_id="step-track")
    await agent.execute(track_step)

    audit_step = make_step("audit_bill", {
        "patient_id": "p1",
        "cycle_id": "c1",
        "line_items": [
            {"linked_record_id": "order-1", "billed_amount": 1200.0},
        ],
    })
    result = await agent.execute(audit_step)
    assert result.error is None
    assert result.output["clean"] is True
    assert result.output["discrepancies"] == []


# ---------------------------------------------------------------------------
# generate_insurance_summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_insurance_summary_groups_by_category(agent):
    # Create two cost records in different categories
    for i, (cat, amt, rec_id) in enumerate([
        ("medication", 6200.0, "sched-1"),
        ("test", 1200.0, "order-1"),
        ("medication", 1800.0, "sched-2"),
    ]):
        await agent.execute(make_step("track_cost", {
            "patient_id": "p1",
            "cycle_id": "c1",
            "category": cat,
            "amount": amt,
            "linked_record_id": rec_id,
        }, step_id=f"step-{i}"))

    summary_step = make_step("generate_insurance_summary", {
        "patient_id": "p1",
        "cycle_id": "c1",
    })
    result = await agent.execute(summary_step)
    assert result.error is None
    categories = {c["category"]: c for c in result.output["categories"]}
    assert "medication" in categories
    assert "test" in categories
    assert categories["medication"]["subtotal"] == 8000.0
    assert categories["test"]["subtotal"] == 1200.0
    assert result.output["grand_total"] == 9200.0
