"""Task Manager API client tools for the IVF Treatment Advisor agent."""

from __future__ import annotations

import os
import logging

import httpx

logger = logging.getLogger(__name__)

_BASE_URL = os.getenv(
    "TASK_MANAGER_URL",
    "https://task-manager-api-100876575377.us-central1.run.app",
)
_SECRET_KEY = os.getenv("TASK_MANAGER_SECRET_KEY", "")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_SECRET_KEY}", "Content-Type": "application/json"}


def _client() -> httpx.Client:
    return httpx.Client(timeout=15.0)


def create_task_tool(
    title: str,
    priority: str = "medium",
    description: str = "",
) -> dict:
    """Create a task in the IVF care platform.

    Use this when a patient wants to track a to-do item, action, or follow-up
    related to their IVF treatment (e.g. 'remind me to call the clinic',
    'track my medication pickup').

    Args:
        title: Short description of the task (required, non-empty).
        priority: One of 'low', 'medium', 'high'. Default 'medium'.
        description: Optional longer description.

    Returns:
        The created task record with id, title, status, priority.
    """
    try:
        with _client() as client:
            resp = client.post(
                f"{_BASE_URL}/tasks",
                headers=_headers(),
                json={"title": title, "priority": priority, "description": description},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("create_task_tool failed: %s", exc)
        return {"error": str(exc)}


def schedule_reminder_tool(
    patient_id: str,
    linked_record_id: str,
    linked_record_type: str,
    scheduled_at: str,
    criticality: str = "normal",
) -> dict:
    """Schedule a reminder for a patient.

    Use this when a patient asks to be reminded about a medication, appointment,
    injection, or any time-sensitive IVF event.

    Args:
        patient_id: The patient's identifier.
        linked_record_id: ID of the record this reminder is linked to.
        linked_record_type: Type of record e.g. 'medication', 'appointment', 'nurse_visit'.
        scheduled_at: ISO 8601 datetime string e.g. '2026-04-03T21:00:00'.
        criticality: 'normal' or 'critical'. Use 'critical' for trigger shots and
                     time-sensitive medications.

    Returns:
        The created reminder record.
    """
    try:
        with _client() as client:
            resp = client.post(
                f"{_BASE_URL}/reminders",
                headers=_headers(),
                json={
                    "patient_id": patient_id,
                    "linked_record_id": linked_record_id,
                    "linked_record_type": linked_record_type,
                    "scheduled_at": scheduled_at,
                    "criticality": criticality,
                },
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("schedule_reminder_tool failed: %s", exc)
        return {"error": str(exc)}


def book_appointment_tool(
    patient_id: str,
    appointment_type: str,
    scheduled_at: str,
    location: str,
) -> dict:
    """Book a clinical appointment for a patient.

    Use this when a patient wants to schedule a consultation, ultrasound scan,
    egg retrieval, or embryo transfer appointment.

    Args:
        patient_id: The patient's identifier.
        appointment_type: One of 'consultation', 'ultrasound', 'egg_retrieval',
                          'embryo_transfer'.
        scheduled_at: ISO 8601 datetime string e.g. '2026-04-05T10:00:00'.
        location: Clinic name or address.

    Returns:
        The created appointment record with checklist.
    """
    try:
        with _client() as client:
            resp = client.post(
                f"{_BASE_URL}/appointments",
                headers=_headers(),
                json={
                    "patient_id": patient_id,
                    "type": appointment_type,
                    "scheduled_at": scheduled_at,
                    "location": location,
                },
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("book_appointment_tool failed: %s", exc)
        return {"error": str(exc)}


def book_nurse_visit_tool(
    patient_id: str,
    scheduled_at: str,
    medication_administration_id: str = "pending",
) -> dict:
    """Book a nurse home visit for injection administration.

    Use this when a patient cannot travel to the clinic and needs a nurse
    to come home for their daily injection (e.g. Gonal-F, Menopur, trigger shot).

    Args:
        patient_id: The patient's identifier.
        scheduled_at: ISO 8601 datetime string for the visit e.g. '2026-04-03T21:00:00'.
        medication_administration_id: ID of the medication administration record.
                                      Use 'pending' if not yet created.

    Returns:
        The created nurse visit record with assigned nurse details.
    """
    try:
        with _client() as client:
            resp = client.post(
                f"{_BASE_URL}/nurse-visits",
                headers=_headers(),
                json={
                    "patient_id": patient_id,
                    "nurse_id": "auto-assign",
                    "scheduled_at": scheduled_at,
                    "medication_administration_id": medication_administration_id,
                },
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("book_nurse_visit_tool failed: %s", exc)
        return {"error": str(exc)}


def get_cost_summary_tool(patient_id: str, cycle_id: str) -> dict:
    """Get a cost breakdown for a patient's IVF cycle.

    Use this when a patient asks about their total spending, what they've been
    charged, or wants a financial summary of their current cycle.

    Args:
        patient_id: The patient's identifier.
        cycle_id: The IVF cycle identifier.

    Returns:
        Cost breakdown by category with grand total in INR.
    """
    try:
        with _client() as client:
            resp = client.get(
                f"{_BASE_URL}/costs/summary",
                headers=_headers(),
                params={"patient_id": patient_id, "cycle_id": cycle_id},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("get_cost_summary_tool failed: %s", exc)
        return {"error": str(exc)}


def submit_workflow_tool(request: str) -> dict:
    """Submit a natural-language request to the multi-agent task manager.

    Use this for complex multi-step requests that involve coordination across
    multiple domains (e.g. 'book a nurse for my trigger shot and set a reminder').
    The orchestrator will automatically route to the appropriate sub-agents.

    Args:
        request: Natural language description of what needs to be done.

    Returns:
        workflow_id that can be used to track progress.
    """
    try:
        with _client() as client:
            resp = client.post(
                f"{_BASE_URL}/requests",
                headers=_headers(),
                json={"request": request},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("submit_workflow_tool failed: %s", exc)
        return {"error": str(exc)}


def get_schedule_tool(patient_id: str = "") -> dict:
    """Get all upcoming tasks, reminders and appointments for a patient.

    Use this when a patient asks 'what is my schedule', 'show my reminders',
    'what do I have coming up', or any question about their upcoming activities.

    Args:
        patient_id: Optional patient identifier. Leave empty to get all records.

    Returns:
        Dictionary with tasks, events, and reminders lists.
    """
    try:
        with _client() as client:
            tasks_resp = client.get(
                f"{_BASE_URL}/tasks",
                headers=_headers(),
            )
            tasks = tasks_resp.json() if tasks_resp.status_code == 200 else []

            events_resp = client.get(
                f"{_BASE_URL}/events",
                headers=_headers(),
            )
            events = events_resp.json() if events_resp.status_code == 200 else []

            # Fetch reminders — query all reminders (no patient filter on GET /reminders yet)
            reminders_resp = client.get(
                f"{_BASE_URL}/reminders",
                headers=_headers(),
                params={"patient_id": patient_id} if patient_id else {},
            )
            reminders = reminders_resp.json() if reminders_resp.status_code == 200 else []

            # Fetch appointments
            appointments_resp = client.get(
                f"{_BASE_URL}/appointments",
                headers=_headers(),
                params={"patient_id": patient_id} if patient_id else {},
            )
            appointments = appointments_resp.json() if appointments_resp.status_code == 200 else []
            # Filter to only future appointments
            from datetime import datetime as dt
            now = dt.utcnow().isoformat()
            appointments = [a for a in appointments if isinstance(a, dict) and a.get("datetime", "") >= now]

        return {
            "tasks": tasks,
            "events": events,
            "reminders": reminders,
            "appointments": appointments,
            "summary": (
                f"Found {len(tasks)} tasks, {len(events)} events, "
                f"{len(reminders)} reminders, and {len(appointments)} appointments."
            )
        }
    except Exception as exc:
        logger.error("get_schedule_tool failed: %s", exc)
        return {"error": str(exc)}


def get_workflow_status_tool(workflow_id: str) -> dict:
    """Get the status and results of a submitted workflow.

    Use this when a patient asks about the status of a previously submitted
    request, or when you need to check if a workflow completed successfully
    and retrieve its results.

    Args:
        workflow_id: The workflow identifier returned by submit_workflow_tool.

    Returns:
        Workflow status (pending/running/completed/failed) and step results.
    """
    try:
        with _client() as client:
            resp = client.get(
                f"{_BASE_URL}/workflows/{workflow_id}",
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("get_workflow_status_tool failed: %s", exc)
        return {"error": str(exc)}


def semantic_search_tool(
    query: str,
    search_type: str = "notes",
    patient_id: str = "",
    limit: int = 5,
) -> dict:
    """Search patient records using semantic similarity (AlloyDB vector search).

    Use this when a patient asks questions like:
    - 'Find my notes about side effects'
    - 'Show me abnormal test results'
    - 'What did my doctor say about my AMH levels?'
    - 'Find anything related to my stimulation phase'

    This uses AI embeddings to find semantically similar records, not just
    exact keyword matches.

    Args:
        query: Natural language search query.
        search_type: 'notes' to search notes, 'pathology' to search test results.
        patient_id: Optional patient ID to filter results.
        limit: Maximum number of results (default 5).

    Returns:
        List of matching records ordered by semantic similarity.
    """
    try:
        with _client() as client:
            if search_type == "pathology":
                params = {"query": query, "limit": limit}
                if patient_id:
                    params["patient_id"] = patient_id
                resp = client.get(
                    f"{_BASE_URL}/pathology/semantic-search",
                    headers=_headers(),
                    params=params,
                )
            else:
                resp = client.get(
                    f"{_BASE_URL}/notes/semantic-search",
                    headers=_headers(),
                    params={"query": query, "limit": limit},
                )
            resp.raise_for_status()
            results = resp.json()
            return {
                "results": results,
                "count": len(results),
                "search_type": search_type,
                "query": query,
            }
    except Exception as exc:
        logger.error("semantic_search_tool failed: %s", exc)
        return {"error": str(exc)}
