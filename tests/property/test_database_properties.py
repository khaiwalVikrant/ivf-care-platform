"""Property-based tests for the Database layer — Task 1 sub-tasks.

Properties covered:
  - Property 27: Unique identifiers at creation (Requirement 8.4)
  - Property 25: Write confirmation before success return (Requirement 8.2)
  - Property 26: Failed write leaves no partial record (Requirement 8.3)
"""

from __future__ import annotations

import asyncio
import pytest
from datetime import datetime, timezone
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from task_manager.db.database import Database
from task_manager.models import Priority, TaskStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(coro):
    """Run a coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


def make_db() -> Database:
    """Create a fresh in-memory SQLite database for each test."""
    db = Database(url="sqlite+aiosqlite:///:memory:")
    run(db.init_db())
    return db


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

valid_title = st.text(min_size=1).filter(lambda s: s.strip())
valid_body = st.text(min_size=1).filter(lambda s: s.strip())
valid_status = st.sampled_from(TaskStatus)
valid_priority = st.sampled_from(Priority)


# ---------------------------------------------------------------------------
# Property 27: Unique identifiers at creation
# ---------------------------------------------------------------------------

# Feature: multi-agent-task-manager, Property 27: Unique identifiers at creation
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    titles=st.lists(valid_title, min_size=2, max_size=10),
    bodies=st.lists(valid_body, min_size=2, max_size=10),
)
def test_unique_identifiers_at_creation(titles, bodies):
    """All IDs assigned across Task, Event, and Note records must be globally unique.

    Validates: Requirements 8.4
    """
    db = make_db()
    ids = []

    # Create tasks
    for title in titles:
        task = run(db.create_task(title=title, status=TaskStatus.pending, priority=Priority.medium))
        ids.append(task.id)

    # Create notes
    for body in bodies:
        note = run(db.create_note(title="t", body=body))
        ids.append(note.id)

    # Create events
    now = datetime(2024, 1, 1, 12, 0, 0)
    for i in range(min(len(titles), len(bodies))):
        event = run(db.create_event(title=f"e{i}", start_time=now, end_time=now))
        ids.append(event.id)

    assert len(ids) == len(set(ids)), "Duplicate IDs found across records"


# ---------------------------------------------------------------------------
# Property 25: Write confirmation before success return
# ---------------------------------------------------------------------------

# Feature: multi-agent-task-manager, Property 25: Write confirmation before success return
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    title=valid_title,
    body=valid_body,
)
def test_write_confirmation_before_success_return(title, body):
    """After a write call returns success, the record must be immediately readable.

    Validates: Requirements 8.2
    """
    db = make_db()
    now = datetime(2024, 6, 1, 10, 0, 0)

    # Task
    task = run(db.create_task(title=title, status=TaskStatus.pending, priority=Priority.low))
    retrieved_task = run(db.get_task(task.id))
    assert retrieved_task is not None, "Task not readable immediately after creation"
    assert retrieved_task.id == task.id
    assert retrieved_task.title == task.title

    # Note
    note = run(db.create_note(title=title, body=body))
    retrieved_note = run(db.get_note(note.id))
    assert retrieved_note is not None, "Note not readable immediately after creation"
    assert retrieved_note.id == note.id
    assert retrieved_note.body == note.body

    # Event
    event = run(db.create_event(title=title, start_time=now, end_time=now))
    retrieved_event = run(db.get_event(event.id))
    assert retrieved_event is not None, "Event not readable immediately after creation"
    assert retrieved_event.id == event.id
    assert retrieved_event.title == event.title


# ---------------------------------------------------------------------------
# Property 26: Failed write leaves no partial record
# ---------------------------------------------------------------------------

# Feature: multi-agent-task-manager, Property 26: Failed write leaves no partial record
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    whitespace_title=st.text(alphabet=" \t\n", min_size=0, max_size=20),
    whitespace_body=st.text(alphabet=" \t\n", min_size=0, max_size=20),
)
def test_failed_write_leaves_no_partial_record(whitespace_title, whitespace_body):
    """A write that fails due to validation must not leave any partial record.

    Validates: Requirements 8.3
    """
    db = make_db()

    # Attempt to create a task with empty/whitespace title — must fail
    with pytest.raises((ValueError, Exception)):
        run(db.create_task(
            title=whitespace_title,
            status=TaskStatus.pending,
            priority=Priority.medium,
        ))

    # No tasks should exist
    tasks = run(db.query_tasks())
    assert len(tasks) == 0, "Partial task record found after failed write"

    # Attempt to create a note with empty/whitespace body — must fail
    with pytest.raises((ValueError, Exception)):
        run(db.create_note(title="some title", body=whitespace_body))

    # No notes should exist
    notes = run(db.search_notes())
    assert len(notes) == 0, "Partial note record found after failed write"
