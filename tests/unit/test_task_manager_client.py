"""Unit tests for task_manager_client tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ivf_advisor.tools.task_manager_client import (
    book_appointment_tool,
    book_nurse_visit_tool,
    create_task_tool,
    get_cost_summary_tool,
    get_schedule_tool,
    get_workflow_status_tool,
    schedule_reminder_tool,
    submit_workflow_tool,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(json_data: dict, status_code: int = 200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


def _mock_error_response():
    resp = MagicMock()
    resp.raise_for_status.side_effect = Exception("HTTP 500")
    return resp


# ---------------------------------------------------------------------------
# create_task_tool
# ---------------------------------------------------------------------------

def test_create_task_tool_success():
    expected = {"id": "abc", "title": "Take Gonal-F", "status": "pending"}
    with patch("ivf_advisor.tools.task_manager_client._client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = _mock_response(expected)
        result = create_task_tool("Take Gonal-F", priority="high")
    assert result["title"] == "Take Gonal-F"
    assert result["id"] == "abc"


def test_create_task_tool_returns_error_on_exception():
    with patch("ivf_advisor.tools.task_manager_client._client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.side_effect = Exception("connection error")
        result = create_task_tool("Task")
    assert "error" in result


# ---------------------------------------------------------------------------
# schedule_reminder_tool
# ---------------------------------------------------------------------------

def test_schedule_reminder_tool_success():
    expected = {"id": "rem-1", "patient_id": "p1", "acknowledged": False}
    with patch("ivf_advisor.tools.task_manager_client._client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = _mock_response(expected)
        result = schedule_reminder_tool(
            patient_id="p1",
            linked_record_id="rec-1",
            linked_record_type="medication",
            scheduled_at="2026-04-05T21:00:00",
            criticality="critical",
        )
    assert result["id"] == "rem-1"
    assert result["acknowledged"] is False


def test_schedule_reminder_tool_returns_error_on_exception():
    with patch("ivf_advisor.tools.task_manager_client._client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.side_effect = Exception("timeout")
        result = schedule_reminder_tool("p1", "rec-1", "medication", "2026-04-05T21:00:00")
    assert "error" in result


# ---------------------------------------------------------------------------
# book_appointment_tool
# ---------------------------------------------------------------------------

def test_book_appointment_tool_success():
    expected = {"id": "appt-1", "type": "consultation", "checklist": ["Bring ID"]}
    with patch("ivf_advisor.tools.task_manager_client._client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = _mock_response(expected)
        result = book_appointment_tool("p1", "consultation", "2026-04-10T10:00:00", "City Clinic")
    assert result["type"] == "consultation"
    assert "checklist" in result


def test_book_appointment_tool_returns_error_on_exception():
    with patch("ivf_advisor.tools.task_manager_client._client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.side_effect = Exception("error")
        result = book_appointment_tool("p1", "ultrasound", "2026-04-10T10:00:00", "Clinic")
    assert "error" in result


# ---------------------------------------------------------------------------
# book_nurse_visit_tool
# ---------------------------------------------------------------------------

def test_book_nurse_visit_tool_success():
    expected = {"id": "visit-1", "nurse_id": "nurse-001", "status": "scheduled"}
    with patch("ivf_advisor.tools.task_manager_client._client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = _mock_response(expected)
        result = book_nurse_visit_tool("p1", "2026-04-05T21:00:00")
    assert result["status"] == "scheduled"
    assert result["nurse_id"] == "nurse-001"


# ---------------------------------------------------------------------------
# get_cost_summary_tool
# ---------------------------------------------------------------------------

def test_get_cost_summary_tool_success():
    expected = {"grand_total": 145000.0, "breakdown": {"medication": 80000.0}}
    with patch("ivf_advisor.tools.task_manager_client._client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = _mock_response(expected)
        result = get_cost_summary_tool("p1", "cycle-1")
    assert result["grand_total"] == 145000.0


def test_get_cost_summary_tool_returns_error_on_exception():
    with patch("ivf_advisor.tools.task_manager_client._client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.side_effect = Exception("error")
        result = get_cost_summary_tool("p1", "cycle-1")
    assert "error" in result


# ---------------------------------------------------------------------------
# get_schedule_tool
# ---------------------------------------------------------------------------

def test_get_schedule_tool_returns_tasks_and_events():
    tasks = [{"id": "t1", "title": "Take medication"}]
    events = [{"id": "e1", "title": "Ultrasound scan"}]

    mock_tasks_resp = _mock_response(tasks)
    mock_events_resp = _mock_response(events)

    with patch("ivf_advisor.tools.task_manager_client._client") as mock_client:
        mock_get = mock_client.return_value.__enter__.return_value.get
        mock_get.side_effect = [mock_tasks_resp, mock_events_resp]
        result = get_schedule_tool("p1")

    assert len(result["tasks"]) == 1
    assert len(result["events"]) == 1
    assert "Found 1 tasks and 1 events" in result["summary"]


def test_get_schedule_tool_returns_error_on_exception():
    with patch("ivf_advisor.tools.task_manager_client._client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.side_effect = Exception("error")
        result = get_schedule_tool("p1")
    assert "error" in result


# ---------------------------------------------------------------------------
# get_workflow_status_tool
# ---------------------------------------------------------------------------

def test_get_workflow_status_tool_success():
    expected = {
        "workflow_id": "f7ea6610",
        "status": "completed",
        "steps": [{"step_id": "s1", "capability": "create_task", "status": "completed"}],
    }
    with patch("ivf_advisor.tools.task_manager_client._client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = _mock_response(expected)
        result = get_workflow_status_tool("f7ea6610")
    assert result["status"] == "completed"
    assert result["workflow_id"] == "f7ea6610"


def test_get_workflow_status_tool_not_found():
    with patch("ivf_advisor.tools.task_manager_client._client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.side_effect = Exception("404")
        result = get_workflow_status_tool("nonexistent-id")
    assert "error" in result


# ---------------------------------------------------------------------------
# submit_workflow_tool
# ---------------------------------------------------------------------------

def test_submit_workflow_tool_success():
    expected = {"workflow_id": "wf-123"}
    with patch("ivf_advisor.tools.task_manager_client._client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = _mock_response(expected)
        result = submit_workflow_tool("Book a nurse for my trigger shot tonight")
    assert result["workflow_id"] == "wf-123"


def test_submit_workflow_tool_returns_error_on_exception():
    with patch("ivf_advisor.tools.task_manager_client._client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.side_effect = Exception("error")
        result = submit_workflow_tool("some request")
    assert "error" in result
