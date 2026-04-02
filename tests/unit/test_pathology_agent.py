"""Unit tests for PathologySubAgent."""

from __future__ import annotations

import json

import pytest

from task_manager.agents.pathology_agent import PathologySubAgent
from task_manager.db.database import Database
from task_manager.models import WorkflowStatus, WorkflowStep


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
    return PathologySubAgent(db=db)


# ---------------------------------------------------------------------------
# order_test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_order_test_success(agent):
    step = make_step("order_test", {
        "patient_id": "p1",
        "cycle_id": "c1",
        "ivf_stage": "stimulation",
        "tests": ["FSH", "LH", "E2"],
    })
    result = await agent.execute(step)
    assert result.error is None
    assert result.output["patient_id"] == "p1"
    assert result.output["cycle_id"] == "c1"
    assert result.output["tests"] == ["FSH", "LH", "E2"]
    assert result.output["collection_status"] == "pending"


@pytest.mark.asyncio
async def test_order_test_stage_inappropriate_warning(agent):
    """Ordering an embryo-related test at baseline stage should produce a warning."""
    step = make_step("order_test", {
        "patient_id": "p1",
        "cycle_id": "c1",
        "ivf_stage": "baseline",
        "tests": ["FSH", "embryo grading"],
    })
    result = await agent.execute(step)
    assert result.error is None
    # Order still created
    assert result.output["id"] is not None
    # Warning present
    assert "warnings" in result.output
    assert any("embryo" in w.lower() for w in result.output["warnings"])


@pytest.mark.asyncio
async def test_order_test_no_warning_for_appropriate_tests(agent):
    step = make_step("order_test", {
        "patient_id": "p1",
        "cycle_id": "c1",
        "ivf_stage": "baseline",
        "tests": ["FSH", "LH"],
    })
    result = await agent.execute(step)
    assert result.error is None
    assert "warnings" not in result.output


# ---------------------------------------------------------------------------
# update_sample_status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_sample_status_success(agent):
    # Create an order first
    order_step = make_step("order_test", {
        "patient_id": "p2",
        "cycle_id": "c2",
        "ivf_stage": "stimulation",
        "tests": ["FSH"],
    })
    r = await agent.execute(order_step)
    order_id = r.output["id"]

    # Update status
    update_step = make_step("update_sample_status", {
        "order_id": order_id,
        "status": "collected",
    })
    result = await agent.execute(update_step)
    assert result.error is None
    assert result.output["collection_status"] == "collected"


@pytest.mark.asyncio
async def test_update_sample_status_not_found(agent):
    step = make_step("update_sample_status", {
        "order_id": "nonexistent",
        "status": "collected",
    })
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "PATHOLOGY_ORDER_NOT_FOUND"


# ---------------------------------------------------------------------------
# store_result — abnormality flagging
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_store_result_normal_value(agent):
    # Create order
    order_step = make_step("order_test", {
        "patient_id": "p3",
        "cycle_id": "c3",
        "ivf_stage": "stimulation",
        "tests": ["FSH"],
    }, step_id="step-order")
    r = await agent.execute(order_step)
    order_id = r.output["id"]

    # Store result within range
    result_step = make_step("store_result", {
        "order_id": order_id,
        "test_name": "FSH",
        "value": "5.0",
        "unit": "mIU/mL",
        "reference_range": "2.5-10.0",
    })
    result = await agent.execute(result_step)
    assert result.error is None
    assert result.output["abnormal"] is False


@pytest.mark.asyncio
async def test_store_result_high_value_flagged_abnormal(agent):
    order_step = make_step("order_test", {
        "patient_id": "p4",
        "cycle_id": "c4",
        "ivf_stage": "stimulation",
        "tests": ["FSH"],
    }, step_id="step-order")
    r = await agent.execute(order_step)
    order_id = r.output["id"]

    result_step = make_step("store_result", {
        "order_id": order_id,
        "test_name": "FSH",
        "value": "15.0",
        "unit": "mIU/mL",
        "reference_range": "2.5-10.0",
    })
    result = await agent.execute(result_step)
    assert result.error is None
    assert result.output["abnormal"] is True


@pytest.mark.asyncio
async def test_store_result_low_value_flagged_abnormal(agent):
    order_step = make_step("order_test", {
        "patient_id": "p5",
        "cycle_id": "c5",
        "ivf_stage": "stimulation",
        "tests": ["FSH"],
    }, step_id="step-order")
    r = await agent.execute(order_step)
    order_id = r.output["id"]

    result_step = make_step("store_result", {
        "order_id": order_id,
        "test_name": "FSH",
        "value": "1.0",
        "unit": "mIU/mL",
        "reference_range": "2.5-10.0",
    })
    result = await agent.execute(result_step)
    assert result.error is None
    assert result.output["abnormal"] is True


# ---------------------------------------------------------------------------
# query_results
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query_results_by_patient_and_cycle(agent):
    # Create order and result
    order_step = make_step("order_test", {
        "patient_id": "p6",
        "cycle_id": "c6",
        "ivf_stage": "stimulation",
        "tests": ["LH"],
    }, step_id="step-order")
    r = await agent.execute(order_step)
    order_id = r.output["id"]

    result_step = make_step("store_result", {
        "order_id": order_id,
        "test_name": "LH",
        "value": "8.0",
        "unit": "mIU/mL",
        "reference_range": "2.0-15.0",
    }, step_id="step-result")
    await agent.execute(result_step)

    query_step = make_step("query_results", {
        "patient_id": "p6",
        "cycle_id": "c6",
    })
    result = await agent.execute(query_step)
    assert result.error is None
    assert len(result.output["results"]) == 1
    assert result.output["results"][0]["test_name"] == "LH"


# ---------------------------------------------------------------------------
# Unknown capability
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_capability_returns_error(agent):
    step = make_step("delete_order", {})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "UNKNOWN_CAPABILITY"
