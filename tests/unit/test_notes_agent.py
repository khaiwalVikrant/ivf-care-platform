"""Unit tests for NotesSubAgent."""

from __future__ import annotations

import json

import pytest

from task_manager.agents.notes_agent import NotesSubAgent
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
    return NotesSubAgent(db=db)


# ---------------------------------------------------------------------------
# create_note
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_note_success(agent):
    step = make_step("create_note", {"title": "My note", "body": "Some content here"})
    result = await agent.execute(step)
    assert result.error is None
    assert result.output["title"] == "My note"
    assert result.output["body"] == "Some content here"


@pytest.mark.asyncio
async def test_create_note_empty_body_returns_error(agent):
    step = make_step("create_note", {"title": "Empty", "body": ""})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "VALIDATION_ERROR"
    assert "body" in err["message"]


@pytest.mark.asyncio
async def test_create_note_whitespace_body_returns_error(agent):
    step = make_step("create_note", {"title": "Whitespace", "body": "   \t\n  "})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_create_note_with_tags(agent):
    step = make_step("create_note", {
        "title": "Tagged note",
        "body": "Content",
        "tags": ["ivf", "medication"],
    })
    result = await agent.execute(step)
    assert result.error is None
    assert "ivf" in result.output["tags"]
    assert "medication" in result.output["tags"]


# ---------------------------------------------------------------------------
# search_notes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_notes_by_keyword_in_title(agent):
    await agent.execute(make_step("create_note", {"title": "Trigger shot", "body": "At 11pm"}, "s1"))
    await agent.execute(make_step("create_note", {"title": "Unrelated", "body": "Nothing"}, "s2"))

    result = await agent.execute(make_step("search_notes", {"keyword": "trigger"}))
    assert result.error is None
    titles = [n["title"] for n in result.output["notes"]]
    assert "Trigger shot" in titles
    assert "Unrelated" not in titles


@pytest.mark.asyncio
async def test_search_notes_by_keyword_in_body(agent):
    await agent.execute(make_step("create_note", {"title": "Note A", "body": "Contains estrogen info"}, "s1"))
    await agent.execute(make_step("create_note", {"title": "Note B", "body": "Nothing relevant"}, "s2"))

    result = await agent.execute(make_step("search_notes", {"keyword": "estrogen"}))
    assert result.error is None
    titles = [n["title"] for n in result.output["notes"]]
    assert "Note A" in titles
    assert "Note B" not in titles


@pytest.mark.asyncio
async def test_search_notes_no_false_positives(agent):
    await agent.execute(make_step("create_note", {"title": "Alpha", "body": "Alpha content"}, "s1"))
    await agent.execute(make_step("create_note", {"title": "Beta", "body": "Beta content"}, "s2"))

    result = await agent.execute(make_step("search_notes", {"keyword": "alpha"}))
    assert result.error is None
    titles = [n["title"] for n in result.output["notes"]]
    assert "Alpha" in titles
    assert "Beta" not in titles


@pytest.mark.asyncio
async def test_search_notes_by_tag(agent):
    await agent.execute(make_step("create_note", {
        "title": "Tagged", "body": "Content", "tags": ["ivf"]
    }, "s1"))
    await agent.execute(make_step("create_note", {
        "title": "Untagged", "body": "Content", "tags": []
    }, "s2"))

    result = await agent.execute(make_step("search_notes", {"tag": "ivf"}))
    assert result.error is None
    titles = [n["title"] for n in result.output["notes"]]
    assert "Tagged" in titles
    assert "Untagged" not in titles


@pytest.mark.asyncio
async def test_search_notes_tag_excludes_non_matching(agent):
    await agent.execute(make_step("create_note", {
        "title": "Note 1", "body": "Body", "tags": ["alpha"]
    }, "s1"))
    await agent.execute(make_step("create_note", {
        "title": "Note 2", "body": "Body", "tags": ["beta"]
    }, "s2"))

    result = await agent.execute(make_step("search_notes", {"tag": "alpha"}))
    assert result.error is None
    titles = [n["title"] for n in result.output["notes"]]
    assert "Note 1" in titles
    assert "Note 2" not in titles


@pytest.mark.asyncio
async def test_search_notes_no_filters_returns_all(agent):
    for i in range(3):
        await agent.execute(make_step("create_note", {
            "title": f"Note {i}", "body": "Body"
        }, f"s{i}"))

    result = await agent.execute(make_step("search_notes", {}))
    assert result.error is None
    assert len(result.output["notes"]) == 3


# ---------------------------------------------------------------------------
# Unknown capability
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_capability_returns_error(agent):
    step = make_step("delete_note", {})
    result = await agent.execute(step)
    assert result.output is None
    err = json.loads(result.error)
    assert err["error_code"] == "UNKNOWN_CAPABILITY"
