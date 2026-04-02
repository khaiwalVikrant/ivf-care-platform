"""Unit tests for MedicationSubAgent."""

from __future__ import annotations

import json
from datetime import date, datetime

import pytest

from task_manager.agents.medication_agent import MedicationSubAgent
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


BASE_DATE = date(2024, 6, 1)
BASE_TIME = datetime(2024, 6, 1, 10, 0, 0)

SCHEDULE_INPUT = {
    "patient_id": "p1",
    "cycle_id": "c1",
    "drug_name": "Gonal-F",
    "dose": "150 IU",
    "frequency": "daily",
    "route": "subcutaneous",
    "start_date": BASE_DATE.isoformat(),
    "end_date": date(2024, 6, 14).isoformat(),
}


@pytest.fixture
async def agent(tmp_path):
    db = Database(url=f"sqlite+aiosqlite:///{tmp_path}/test.db")
    await db.init_db()
    return MedicationSubAgent(db=db)


# ---------------------------------------------------------------------------
# create_schedule
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_schedule_success(agent):
    step = make_step("create_schedule", SCHEDULE_INPUT)
    result = await agent.execute(step)
    assert result.error is None
    assert result.output["drug_name"] == "Gonal-F"
    assert result.output["dose"] == "150 IU"
    assert result.output["patient_id"] == "p1"
    assert result.output["dose_history"] == []


# ---------------------------------------------------------------------------
# adjust_dose
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_adjust_dose_preserves_history(agent):
    # Create schedule
    create_step = make_step("create_schedule", SCHEDULE_INPUT, step_id="step-create")
    r = await agent.execute(create_step)
    schedule_id = r.output["id"]

    # Adjust dose
    adjust_step = make_step("adjust_dose", {
        "schedule_id": schedule_id,
        "new_dose": "225 IU",
    })
    result = await agent.execute(adjust_step)
    assert result.error is None
    assert result.output["dose"] == "225 IU"
    # Prior dose should be in history
    history = result.output["dose_history"]
    assert len(history) == 1
    assert history[0]["dose"] == "150 IU"
    assert "effective_from" in history[0]


@pytest.mark.asyncio
async def test_adjust_dose_multiple_times_accumulates_history(agent):
    create_step = make_step("create_schedule", SCHEDULE_INPUT, step_id="step-create")
    r = await agent.execute(create_step)
    schedule_id = r.output["id"]

    # First adjustment
    await agent.execute(make_step("adjust_dose", {
        "schedule_id": schedule_id,
        "new_dose": "225 IU",
    }, step_id="step-adj1"))

    # Second adjustment
    result = await agent.execute(make_step("adjust_dose", {
        "schedule_id": schedule_id,
        "new_dose": "300 IU",
    }, step_id="step-adj2"))

    assert result.error is None
    assert result.output["dose"] == "300 IU"
    history = result.output["dose_history"]
    assert len(history) == 2
    doses_in_history = [h["dose"] for h in history]
    assert "150 IU" in doses_in_history
    assert "225 IU" in doses_in_history


@pytest.mark.asyncio
async def test_adjust_dose_not_found(agent):
    step = make_step("adjust_dose", {
        "schedule_id": "nonexistent",
        "new_dose": "225 IU",
    })
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "MEDICATION_SCHEDULE_NOT_FOUND"


# ---------------------------------------------------------------------------
# record_administration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_administration_success(agent):
    create_step = make_step("create_schedule", SCHEDULE_INPUT, step_id="step-create")
    r = await agent.execute(create_step)
    schedule_id = r.output["id"]

    admin_step = make_step("record_administration", {
        "schedule_id": schedule_id,
        "administered_by": "Nurse Jane",
        "administered_at": BASE_TIME.isoformat(),
        "actual_dose": "150 IU",
    })
    result = await agent.execute(admin_step)
    assert result.error is None
    assert result.output["schedule_id"] == schedule_id
    assert result.output["administered_by"] == "Nurse Jane"
    assert result.output["nurse_visit_id"] is None


@pytest.mark.asyncio
async def test_record_administration_with_nurse_visit_id(agent):
    create_step = make_step("create_schedule", SCHEDULE_INPUT, step_id="step-create")
    r = await agent.execute(create_step)
    schedule_id = r.output["id"]

    admin_step = make_step("record_administration", {
        "schedule_id": schedule_id,
        "administered_by": "Nurse Jane",
        "administered_at": BASE_TIME.isoformat(),
        "actual_dose": "150 IU",
        "nurse_visit_id": "visit-123",
    })
    result = await agent.execute(admin_step)
    assert result.error is None
    assert result.output["nurse_visit_id"] == "visit-123"


# ---------------------------------------------------------------------------
# query_medication_history
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query_medication_history_returns_schedules_and_administrations(agent):
    # Create schedule
    create_step = make_step("create_schedule", SCHEDULE_INPUT, step_id="step-create")
    r = await agent.execute(create_step)
    schedule_id = r.output["id"]

    # Record administration
    admin_step = make_step("record_administration", {
        "schedule_id": schedule_id,
        "administered_by": "Nurse Jane",
        "administered_at": BASE_TIME.isoformat(),
        "actual_dose": "150 IU",
    }, step_id="step-admin")
    await agent.execute(admin_step)

    # Query history
    query_step = make_step("query_medication_history", {
        "patient_id": "p1",
        "cycle_id": "c1",
    })
    result = await agent.execute(query_step)
    assert result.error is None
    assert len(result.output["schedules"]) == 1
    assert len(result.output["administrations"]) == 1
    assert result.output["schedules"][0]["drug_name"] == "Gonal-F"


@pytest.mark.asyncio
async def test_query_medication_history_empty(agent):
    query_step = make_step("query_medication_history", {
        "patient_id": "unknown",
        "cycle_id": "unknown",
    })
    result = await agent.execute(query_step)
    assert result.error is None
    assert result.output["schedules"] == []
    assert result.output["administrations"] == []


# ---------------------------------------------------------------------------
# Unknown capability
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_capability_returns_error(agent):
    step = make_step("delete_schedule", {})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "UNKNOWN_CAPABILITY"
