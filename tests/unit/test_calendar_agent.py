"""Unit tests for CalendarSubAgent."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

import pytest

from task_manager.agents.calendar_agent import CalendarSubAgent
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
    return CalendarSubAgent(db=db)


# ---------------------------------------------------------------------------
# create_event
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_event_success(agent):
    step = make_step("create_event", {
        "title": "Team standup",
        "start_time": BASE_TIME.isoformat(),
        "end_time": (BASE_TIME + timedelta(hours=1)).isoformat(),
    })
    result = await agent.execute(step)
    assert result.error is None
    assert result.output["title"] == "Team standup"


@pytest.mark.asyncio
async def test_create_event_start_equals_end_is_accepted(agent):
    """Boundary: start_time == end_time should be valid."""
    step = make_step("create_event", {
        "title": "Instant event",
        "start_time": BASE_TIME.isoformat(),
        "end_time": BASE_TIME.isoformat(),
    })
    result = await agent.execute(step)
    assert result.error is None
    assert result.output["start_time"] == result.output["end_time"]


@pytest.mark.asyncio
async def test_create_event_start_after_end_returns_error(agent):
    step = make_step("create_event", {
        "title": "Bad event",
        "start_time": (BASE_TIME + timedelta(hours=1)).isoformat(),
        "end_time": BASE_TIME.isoformat(),
    })
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "INVALID_TIME_RANGE"


@pytest.mark.asyncio
async def test_create_event_with_recurrence_rule(agent):
    step = make_step("create_event", {
        "title": "Weekly sync",
        "start_time": BASE_TIME.isoformat(),
        "end_time": (BASE_TIME + timedelta(hours=1)).isoformat(),
        "recurrence_rule": "FREQ=WEEKLY;BYDAY=MO",
    })
    result = await agent.execute(step)
    assert result.error is None
    assert result.output["recurrence_rule"] == "FREQ=WEEKLY;BYDAY=MO"


# ---------------------------------------------------------------------------
# query_events
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query_events_returns_list(agent):
    for i in range(3):
        t = BASE_TIME + timedelta(days=i)
        await agent.execute(make_step("create_event", {
            "title": f"Event {i}",
            "start_time": t.isoformat(),
            "end_time": (t + timedelta(hours=1)).isoformat(),
        }, step_id=f"step-{i}"))

    result = await agent.execute(make_step("query_events", {}))
    assert result.error is None
    assert len(result.output["events"]) == 3


@pytest.mark.asyncio
async def test_query_events_filters_by_range(agent):
    # Create events on day 1, 5, 10
    for day in (1, 5, 10):
        t = BASE_TIME + timedelta(days=day)
        await agent.execute(make_step("create_event", {
            "title": f"Day {day}",
            "start_time": t.isoformat(),
            "end_time": (t + timedelta(hours=1)).isoformat(),
        }, step_id=f"step-{day}"))

    # Query only days 1–6
    start_from = BASE_TIME + timedelta(days=0)
    start_to = BASE_TIME + timedelta(days=6)
    result = await agent.execute(make_step("query_events", {
        "start_from": start_from.isoformat(),
        "start_to": start_to.isoformat(),
    }))
    assert result.error is None
    titles = {e["title"] for e in result.output["events"]}
    assert "Day 1" in titles
    assert "Day 5" in titles
    assert "Day 10" not in titles


# ---------------------------------------------------------------------------
# Unknown capability
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_capability_returns_error(agent):
    step = make_step("delete_event", {})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "UNKNOWN_CAPABILITY"
