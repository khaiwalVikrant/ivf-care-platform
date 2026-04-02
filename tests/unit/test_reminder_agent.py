"""Unit tests for ReminderSubAgent."""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from task_manager.agents.reminder_agent import ReminderSubAgent
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


REMINDER_INPUT = {
    "patient_id": "p1",
    "linked_record_id": "visit-1",
    "linked_record_type": "nurse_visit",
    "scheduled_at": BASE_TIME.isoformat(),
    "criticality": "normal",
}


@pytest.fixture
async def agent(tmp_path):
    db = Database(url=f"sqlite+aiosqlite:///{tmp_path}/test.db")
    await db.init_db()
    return ReminderSubAgent(db=db)


# ---------------------------------------------------------------------------
# schedule_reminder
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_schedule_reminder_creates_with_acknowledged_false(agent):
    step = make_step("schedule_reminder", REMINDER_INPUT)
    result = await agent.execute(step)
    assert result.error is None
    assert result.output["acknowledged"] is False
    assert result.output["escalation_count"] == 0
    assert result.output["patient_id"] == "p1"
    assert result.output["linked_record_id"] == "visit-1"


@pytest.mark.asyncio
async def test_schedule_critical_reminder(agent):
    inp = {**REMINDER_INPUT, "criticality": "critical"}
    step = make_step("schedule_reminder", inp)
    result = await agent.execute(step)
    assert result.error is None
    assert result.output["criticality"] == "critical"
    assert result.output["acknowledged"] is False


# ---------------------------------------------------------------------------
# acknowledge_reminder
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_acknowledge_reminder_sets_acknowledged_and_timestamp(agent):
    # Schedule first
    schedule_step = make_step("schedule_reminder", REMINDER_INPUT, step_id="step-sched")
    r = await agent.execute(schedule_step)
    reminder_id = r.output["id"]

    ack_step = make_step("acknowledge_reminder", {"reminder_id": reminder_id})
    result = await agent.execute(ack_step)
    assert result.error is None
    assert result.output["acknowledged"] is True
    assert result.output["acknowledged_at"] is not None


@pytest.mark.asyncio
async def test_acknowledge_reminder_not_found(agent):
    step = make_step("acknowledge_reminder", {"reminder_id": "nonexistent"})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "REMINDER_NOT_FOUND"


# ---------------------------------------------------------------------------
# escalate_reminder
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_escalate_reminder_increments_escalation_count(agent):
    schedule_step = make_step("schedule_reminder", REMINDER_INPUT, step_id="step-sched")
    r = await agent.execute(schedule_step)
    reminder_id = r.output["id"]

    escalate_step = make_step("escalate_reminder", {"reminder_id": reminder_id})
    result = await agent.execute(escalate_step)
    assert result.error is None
    assert result.output["escalation_count"] == 1


@pytest.mark.asyncio
async def test_escalate_reminder_twice_increments_to_two(agent):
    schedule_step = make_step("schedule_reminder", REMINDER_INPUT, step_id="step-sched")
    r = await agent.execute(schedule_step)
    reminder_id = r.output["id"]

    await agent.execute(make_step("escalate_reminder", {"reminder_id": reminder_id}, step_id="esc-1"))
    result = await agent.execute(make_step("escalate_reminder", {"reminder_id": reminder_id}, step_id="esc-2"))
    assert result.output["escalation_count"] == 2


@pytest.mark.asyncio
async def test_escalate_reminder_not_found(agent):
    step = make_step("escalate_reminder", {"reminder_id": "nonexistent"})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "REMINDER_NOT_FOUND"


# ---------------------------------------------------------------------------
# deliver_reminder
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deliver_reminder_returns_all_channels(agent):
    schedule_step = make_step("schedule_reminder", REMINDER_INPUT, step_id="step-sched")
    r = await agent.execute(schedule_step)
    reminder_id = r.output["id"]

    deliver_step = make_step("deliver_reminder", {"reminder_id": reminder_id})
    result = await agent.execute(deliver_step)
    assert result.error is None
    assert set(result.output["channels"]) == {"in_app", "email", "sms"}
    assert result.output["patient_id"] == "p1"
