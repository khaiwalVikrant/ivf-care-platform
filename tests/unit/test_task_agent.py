"""Unit tests for TaskManagerSubAgent."""

from __future__ import annotations

import json
import pytest

from task_manager.agents.task_manager_agent import TaskManagerSubAgent
from task_manager.db.database import Database
from task_manager.models import Priority, TaskStatus, WorkflowStatus, WorkflowStep


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
    return TaskManagerSubAgent(db=db)


# ---------------------------------------------------------------------------
# create_task
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_task_success(agent):
    step = make_step("create_task", {"title": "Buy milk"})
    result = await agent.execute(step)
    assert result.error is None
    assert result.output["title"] == "Buy milk"
    assert result.output["status"] == "pending"


@pytest.mark.asyncio
async def test_create_task_empty_title_returns_error(agent):
    step = make_step("create_task", {"title": "   "})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "VALIDATION_ERROR"
    assert "title" in err["message"]


@pytest.mark.asyncio
async def test_create_task_invalid_status_returns_error(agent):
    step = make_step("create_task", {"title": "Task", "status": "flying"})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# update_task
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_task_not_found_returns_error(agent):
    step = make_step("update_task", {"task_id": "nonexistent-id", "title": "New title"})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "TASK_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_task_partial_update_preserves_fields(agent):
    # Create a task first
    create_step = make_step("create_task", {
        "title": "Original",
        "description": "Keep this",
        "priority": "high",
    })
    create_result = await agent.execute(create_step)
    task_id = create_result.output["id"]

    # Update only the title
    update_step = make_step("update_task", {"task_id": task_id, "title": "Updated"})
    update_result = await agent.execute(update_step)

    assert update_result.error is None
    assert update_result.output["title"] == "Updated"
    assert update_result.output["description"] == "Keep this"
    assert update_result.output["priority"] == "high"


@pytest.mark.asyncio
async def test_update_task_missing_task_id_returns_error(agent):
    step = make_step("update_task", {"title": "No ID"})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# query_tasks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_query_tasks_returns_list(agent):
    await agent.execute(make_step("create_task", {"title": "Task A"}))
    await agent.execute(make_step("create_task", {"title": "Task B"}))

    step = make_step("query_tasks", {})
    result = await agent.execute(step)
    assert result.error is None
    assert len(result.output["tasks"]) == 2


@pytest.mark.asyncio
async def test_query_tasks_filters_by_status(agent):
    await agent.execute(make_step("create_task", {"title": "Pending task", "status": "pending"}))

    # Create a done task directly via db
    db_step = make_step("create_task", {"title": "Done task", "status": "done"})
    create_result = await agent.execute(db_step)
    task_id = create_result.output["id"]
    await agent.execute(make_step("update_task", {"task_id": task_id, "status": "done"}))

    step = make_step("query_tasks", {"status": "pending"})
    result = await agent.execute(step)
    assert result.error is None
    assert all(t["status"] == "pending" for t in result.output["tasks"])


@pytest.mark.asyncio
async def test_query_tasks_invalid_status_returns_error(agent):
    step = make_step("query_tasks", {"status": "unknown_status"})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Unknown capability
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_capability_returns_error(agent):
    step = make_step("delete_task", {})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "UNKNOWN_CAPABILITY"
