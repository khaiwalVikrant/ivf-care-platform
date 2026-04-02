"""Unit tests for NurseSubAgent."""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from task_manager.agents.nurse_agent import NurseSubAgent
from task_manager.db.database import Database
from task_manager.models import WorkflowStatus, WorkflowStep

BASE_TIME = datetime(2024, 6, 1, 10, 0, 0)


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
    return NurseSubAgent(db=db)


# ---------------------------------------------------------------------------
# book_nurse_visit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_book_nurse_visit_assigns_nurse(agent):
    step = make_step("book_nurse_visit", {
        "patient_id": "p1",
        "medication_administration_id": "med-admin-1",
        "scheduled_at": BASE_TIME.isoformat(),
    })
    result = await agent.execute(step)
    assert result.error is None
    assert result.output["patient_id"] == "p1"
    assert result.output["nurse_id"] in ["nurse-001", "nurse-002", "nurse-003"]
    assert result.output["status"] == "scheduled"


@pytest.mark.asyncio
async def test_book_nurse_visit_no_nurse_available(agent):
    """Fill all nurses at the same time slot, then expect NO_NURSE_AVAILABLE."""
    from task_manager.agents.nurse_agent import NURSE_POOL

    # Book all nurses at the same time
    for i, nurse_id in enumerate(NURSE_POOL):
        db = agent._db
        await db.create_nurse_visit(
            patient_id=f"p{i}",
            nurse_id=nurse_id,
            scheduled_at=BASE_TIME,
            medication_administration_id=f"med-{i}",
        )

    step = make_step("book_nurse_visit", {
        "patient_id": "p-new",
        "medication_administration_id": "med-new",
        "scheduled_at": BASE_TIME.isoformat(),
    })
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "NO_NURSE_AVAILABLE"
    assert "nearest_slot" in err["detail"]


# ---------------------------------------------------------------------------
# confirm_visit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_visit_updates_status(agent):
    # Book a visit first
    book_step = make_step("book_nurse_visit", {
        "patient_id": "p1",
        "medication_administration_id": "med-1",
        "scheduled_at": BASE_TIME.isoformat(),
    }, step_id="step-book")
    book_result = await agent.execute(book_step)
    visit_id = book_result.output["id"]

    confirm_step = make_step("confirm_visit", {"visit_id": visit_id})
    result = await agent.execute(confirm_step)
    assert result.error is None
    assert result.output["status"] == "confirmed"


@pytest.mark.asyncio
async def test_confirm_visit_not_found(agent):
    step = make_step("confirm_visit", {"visit_id": "nonexistent"})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "NURSE_VISIT_NOT_FOUND"


# ---------------------------------------------------------------------------
# escalate_visit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_escalate_visit_updates_status_and_escalated_at(agent):
    book_step = make_step("book_nurse_visit", {
        "patient_id": "p1",
        "medication_administration_id": "med-1",
        "scheduled_at": BASE_TIME.isoformat(),
    }, step_id="step-book")
    book_result = await agent.execute(book_step)
    visit_id = book_result.output["id"]

    escalate_step = make_step("escalate_visit", {"visit_id": visit_id})
    result = await agent.execute(escalate_step)
    assert result.error is None
    assert result.output["status"] == "escalated"
    assert result.output["escalated_at"] is not None


@pytest.mark.asyncio
async def test_escalate_visit_not_found(agent):
    step = make_step("escalate_visit", {"visit_id": "nonexistent"})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "NURSE_VISIT_NOT_FOUND"


# ---------------------------------------------------------------------------
# assign_nurse
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assign_nurse_updates_nurse_id(agent):
    book_step = make_step("book_nurse_visit", {
        "patient_id": "p1",
        "medication_administration_id": "med-1",
        "scheduled_at": BASE_TIME.isoformat(),
    }, step_id="step-book")
    book_result = await agent.execute(book_step)
    visit_id = book_result.output["id"]

    assign_step = make_step("assign_nurse", {
        "visit_id": visit_id,
        "nurse_id": "nurse-002",
    })
    result = await agent.execute(assign_step)
    assert result.error is None
    assert result.output["nurse_id"] == "nurse-002"


@pytest.mark.asyncio
async def test_assign_nurse_not_found(agent):
    step = make_step("assign_nurse", {"visit_id": "nonexistent", "nurse_id": "nurse-001"})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "NURSE_VISIT_NOT_FOUND"
