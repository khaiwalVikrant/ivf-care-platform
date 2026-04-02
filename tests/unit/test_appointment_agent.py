"""Unit tests for AppointmentSubAgent."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest

from task_manager.agents.appointment_agent import AppointmentSubAgent
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


BASE_TIME = datetime(2024, 6, 1, 10, 0, 0)


@pytest.fixture
async def agent(tmp_path):
    db = Database(url=f"sqlite+aiosqlite:///{tmp_path}/test.db")
    await db.init_db()
    return AppointmentSubAgent(db=db)


# ---------------------------------------------------------------------------
# book_appointment — checklist generation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_book_consultation_checklist(agent):
    step = make_step("book_appointment", {
        "patient_id": "p1",
        "type": "consultation",
        "datetime": BASE_TIME.isoformat(),
        "location": "Clinic A",
    })
    result = await agent.execute(step)
    assert result.error is None
    checklist = result.output["checklist"]
    assert "Bring previous medical records" in checklist
    assert "Bring ID proof" in checklist
    assert "List current medications" in checklist


@pytest.mark.asyncio
async def test_book_ultrasound_checklist(agent):
    step = make_step("book_appointment", {
        "patient_id": "p1",
        "type": "ultrasound",
        "datetime": BASE_TIME.isoformat(),
        "location": "Clinic A",
    })
    result = await agent.execute(step)
    assert result.error is None
    checklist = result.output["checklist"]
    assert "Drink 1 litre of water 1 hour before" in checklist
    assert "Bring previous scan reports" in checklist


@pytest.mark.asyncio
async def test_book_egg_retrieval_checklist(agent):
    step = make_step("book_appointment", {
        "patient_id": "p1",
        "type": "egg_retrieval",
        "datetime": BASE_TIME.isoformat(),
        "location": "Clinic A",
    })
    result = await agent.execute(step)
    assert result.error is None
    checklist = result.output["checklist"]
    assert "Fast for 6 hours before procedure" in checklist
    assert "Arrange transport home" in checklist
    assert "Bring companion" in checklist


@pytest.mark.asyncio
async def test_book_embryo_transfer_checklist(agent):
    step = make_step("book_appointment", {
        "patient_id": "p1",
        "type": "embryo_transfer",
        "datetime": BASE_TIME.isoformat(),
        "location": "Clinic A",
    })
    result = await agent.execute(step)
    assert result.error is None
    checklist = result.output["checklist"]
    assert "Full bladder required" in checklist
    assert "Bring embryo transfer consent form" in checklist
    assert "Wear comfortable clothing" in checklist


# ---------------------------------------------------------------------------
# book_appointment — conflict detection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_conflict_within_one_hour_returns_error(agent):
    # Book first appointment
    first = make_step("book_appointment", {
        "patient_id": "p2",
        "type": "consultation",
        "datetime": BASE_TIME.isoformat(),
        "location": "Clinic A",
    }, step_id="step-1")
    r1 = await agent.execute(first)
    assert r1.error is None

    # Book second appointment 30 minutes later — should conflict
    second = make_step("book_appointment", {
        "patient_id": "p2",
        "type": "ultrasound",
        "datetime": (BASE_TIME + timedelta(minutes=30)).isoformat(),
        "location": "Clinic B",
    }, step_id="step-2")
    r2 = await agent.execute(second)
    assert r2.output is None
    err = json.loads(r2.error)
    assert err["error_code"] == "APPOINTMENT_CONFLICT"
    assert "conflicting_id" in err["detail"]


@pytest.mark.asyncio
async def test_no_conflict_beyond_one_hour(agent):
    # Book first appointment
    first = make_step("book_appointment", {
        "patient_id": "p3",
        "type": "consultation",
        "datetime": BASE_TIME.isoformat(),
        "location": "Clinic A",
    }, step_id="step-1")
    r1 = await agent.execute(first)
    assert r1.error is None

    # Book second appointment 2 hours later — no conflict
    second = make_step("book_appointment", {
        "patient_id": "p3",
        "type": "ultrasound",
        "datetime": (BASE_TIME + timedelta(hours=2)).isoformat(),
        "location": "Clinic B",
    }, step_id="step-2")
    r2 = await agent.execute(second)
    assert r2.error is None


# ---------------------------------------------------------------------------
# cancel_appointment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancel_appointment_not_found(agent):
    step = make_step("cancel_appointment", {"appointment_id": "nonexistent"})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "APPOINTMENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_cancel_appointment_success(agent):
    # Book first
    book = make_step("book_appointment", {
        "patient_id": "p4",
        "type": "consultation",
        "datetime": BASE_TIME.isoformat(),
        "location": "Clinic A",
    })
    r = await agent.execute(book)
    appt_id = r.output["id"]

    # Cancel it
    cancel = make_step("cancel_appointment", {"appointment_id": appt_id})
    result = await agent.execute(cancel)
    assert result.error is None


# ---------------------------------------------------------------------------
# reschedule_appointment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reschedule_updates_datetime(agent):
    # Book first
    book = make_step("book_appointment", {
        "patient_id": "p5",
        "type": "consultation",
        "datetime": BASE_TIME.isoformat(),
        "location": "Clinic A",
    })
    r = await agent.execute(book)
    appt_id = r.output["id"]

    new_dt = BASE_TIME + timedelta(days=1)
    reschedule = make_step("reschedule_appointment", {
        "appointment_id": appt_id,
        "new_datetime": new_dt.isoformat(),
    })
    result = await agent.execute(reschedule)
    assert result.error is None
    assert result.output["id"] == appt_id
    # The datetime in output should reflect the new time
    from datetime import datetime as dt
    returned_dt = dt.fromisoformat(result.output["datetime"])
    assert returned_dt == new_dt


@pytest.mark.asyncio
async def test_reschedule_not_found(agent):
    step = make_step("reschedule_appointment", {
        "appointment_id": "nonexistent",
        "new_datetime": BASE_TIME.isoformat(),
    })
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "APPOINTMENT_NOT_FOUND"


# ---------------------------------------------------------------------------
# get_appointment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_appointment_not_found(agent):
    step = make_step("get_appointment", {"appointment_id": "nonexistent"})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "APPOINTMENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_appointment_success(agent):
    book = make_step("book_appointment", {
        "patient_id": "p6",
        "type": "ultrasound",
        "datetime": BASE_TIME.isoformat(),
        "location": "Clinic A",
    })
    r = await agent.execute(book)
    appt_id = r.output["id"]

    get = make_step("get_appointment", {"appointment_id": appt_id})
    result = await agent.execute(get)
    assert result.error is None
    assert result.output["id"] == appt_id


# ---------------------------------------------------------------------------
# Unknown capability
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_capability_returns_error(agent):
    step = make_step("delete_appointment", {})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "UNKNOWN_CAPABILITY"
