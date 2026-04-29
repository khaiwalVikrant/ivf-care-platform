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
    scheduled_at: str,
    linked_record_id: str = "general",
    linked_record_type: str = "general",
    criticality: str = "normal",
) -> dict:
    """Schedule a reminder for a patient.

    Use this when a patient asks to be reminded about a medication, appointment,
    injection, or any time-sensitive IVF event.

    Args:
        patient_id: The patient's identifier.
        scheduled_at: ISO 8601 datetime string e.g. '2026-04-03T21:00:00'.
        linked_record_id: ID of the record this reminder is linked to (optional, defaults to 'general').
        linked_record_type: Type of record e.g. 'medication', 'appointment', 'nurse_visit' (optional).
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
                    "patient_id": patient_id or "anonymous",
                    "linked_record_id": linked_record_id or "general",
                    "linked_record_type": linked_record_type or "general",
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


def get_schedule_tool(patient_id: str) -> dict:
    """Get all upcoming tasks, reminders and appointments for a patient.

    Use this when a patient asks 'what is my schedule', 'show my reminders',
    'what do I have coming up', or any question about their upcoming activities.

    Args:
        patient_id: Patient identifier (REQUIRED). Must be extracted from patient context.

    Returns:
        Dictionary with tasks, events, and reminders lists filtered by patient_id.
    """
    if not patient_id or patient_id == "":
        return {
            "error": "patient_id is required. Cannot retrieve schedule without patient identification.",
            "tasks": [],
            "events": [],
            "reminders": [],
            "appointments": [],
        }
    
    try:
        with _client() as client:
            # Fetch tasks filtered by patient_id
            tasks_resp = client.get(
                f"{_BASE_URL}/tasks",
                headers=_headers(),
                params={"patient_id": patient_id},
            )
            tasks = tasks_resp.json() if tasks_resp.status_code == 200 else []

            # NOTE: Events endpoint does not support patient_id filtering in the backend.
            # Events are system-wide, not patient-specific. Excluding from patient schedule.
            # If patient-specific events are needed, the backend must be updated to:
            # 1. Add patient_id column to events table
            # 2. Update API to accept and filter by patient_id
            events = []

            # Fetch reminders filtered by patient_id
            reminders_resp = client.get(
                f"{_BASE_URL}/reminders",
                headers=_headers(),
                params={"patient_id": patient_id},
            )
            reminders = reminders_resp.json() if reminders_resp.status_code == 200 else []

            # Fetch appointments filtered by patient_id
            appointments_resp = client.get(
                f"{_BASE_URL}/appointments",
                headers=_headers(),
                params={"patient_id": patient_id},
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
                f"Found {len(tasks)} tasks, {len(reminders)} reminders, "
                f"and {len(appointments)} appointments."
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
    patient_id: str,
    search_type: str = "notes",
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
        patient_id: Patient identifier (REQUIRED). Must be extracted from patient context.
        search_type: 'notes' to search notes, 'pathology' to search test results.
        limit: Maximum number of results (default 5).

    Returns:
        List of matching records ordered by semantic similarity.
    """
    if not patient_id or patient_id == "":
        return {
            "error": "patient_id is required. Cannot search patient records without patient identification.",
            "results": [],
            "count": 0,
        }
    
    try:
        with _client() as client:
            params = {"query": query, "limit": limit, "patient_id": patient_id}
            
            if search_type == "pathology":
                resp = client.get(
                    f"{_BASE_URL}/pathology/semantic-search",
                    headers=_headers(),
                    params=params,
                )
            else:
                resp = client.get(
                    f"{_BASE_URL}/notes/semantic-search",
                    headers=_headers(),
                    params=params,
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


def track_expense_tool(
    category: str,
    amount: float,
    description: str,
    patient_id: str = "",
    cycle_id: str = "",
    currency: str = "INR",
) -> dict:
    """Record an expense for a patient's IVF cycle.

    Use this when a patient mentions spending money on anything related to
    their IVF treatment — consultations, medications, tests, procedures,
    nurse visits, or any other expense.

    Args:
        category: Type of expense. Use one of: 'consultation', 'medication',
                  'test', 'procedure', 'nurse_visit'. If unsure, use 'consultation'.
        amount: Amount spent as a number (e.g. 2500 not '2500').
        description: Brief description e.g. 'Initial consultation at CK Birla'.
        patient_id: The patient's identifier (auto-injected from session context).
        cycle_id: The IVF cycle identifier (auto-injected from session context).
        currency: Currency code, default 'INR'.

    Returns:
        The created cost record.
    """
    # Normalise category
    valid_categories = {"consultation", "medication", "test", "procedure", "nurse_visit"}
    cat_lower = category.lower().strip()
    if cat_lower not in valid_categories:
        # Map common variations
        if any(w in cat_lower for w in ["consult", "doctor", "visit", "appointment"]):
            cat_lower = "consultation"
        elif any(w in cat_lower for w in ["drug", "medicine", "injection", "tablet"]):
            cat_lower = "medication"
        elif any(w in cat_lower for w in ["test", "scan", "blood", "ultrasound", "lab"]):
            cat_lower = "test"
        elif any(w in cat_lower for w in ["nurse", "home visit"]):
            cat_lower = "nurse_visit"
        else:
            cat_lower = "procedure"

    if not patient_id or not cycle_id:
        return {
            "status": "noted",
            "message": f"Expense noted: {description} — {currency} {amount} ({cat_lower}). "
                       "Complete your profile setup to save expenses to your account.",
            "amount": amount,
            "category": cat_lower,
        }
    try:
        with _client() as client:
            resp = client.post(
                f"{_BASE_URL}/costs/records",
                headers=_headers(),
                json={
                    "patient_id": patient_id,
                    "cycle_id": cycle_id,
                    "category": cat_lower,
                    "amount": float(amount),
                    "linked_record_id": description,
                    "currency": currency,
                },
            )
            if resp.status_code in (200, 201):
                return resp.json()
            logger.error("track_expense_tool HTTP %s: %s", resp.status_code, resp.text)
            return {"error": f"API returned {resp.status_code}: {resp.text}"}
    except Exception as exc:
        logger.error("track_expense_tool failed: %s", exc)
        return {"error": str(exc)}
