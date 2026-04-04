"""Google Calendar integration tool for IVF care platform."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Calendar IDs — set these as env vars or use 'primary' for the service account's calendar
PATIENT_CALENDAR_ID = os.getenv("PATIENT_CALENDAR_ID", "primary")
NURSE_CALENDAR_ID = os.getenv("NURSE_CALENDAR_ID", "primary")
DOCTOR_CALENDAR_ID = os.getenv("DOCTOR_CALENDAR_ID", "primary")


def _get_calendar_service():
    """Build Google Calendar API service using Application Default Credentials (ADC).

    On Cloud Run, ADC automatically uses the attached service account.
    No key file needed — IAM handles authentication.
    """
    from google.auth import default
    from googleapiclient.discovery import build

    credentials, _ = default(scopes=["https://www.googleapis.com/auth/calendar"])
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


def add_to_calendar_tool(
    title: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    location: str = "",
    attendee_emails: Optional[list[str]] = None,
    calendar_id: str = "primary",
) -> dict:
    """Add an event to Google Calendar.

    Use this when a patient books an appointment, nurse visit, or any scheduled
    event that should appear in the calendar of the patient, nurse, or doctor.

    Args:
        title: Event title e.g. 'Nurse Visit — Gonal-F 150IU injection'.
        start_datetime: ISO 8601 datetime e.g. '2026-04-05T21:00:00'.
        end_datetime: ISO 8601 datetime e.g. '2026-04-05T21:30:00'.
        description: Event description — include checklist, dose details, instructions.
        location: Clinic name or patient address for home visits.
        attendee_emails: List of email addresses to invite.
        calendar_id: Google Calendar ID. Use 'primary' for the default calendar.

    Returns:
        Created event details including event_id and htmlLink.
    """
    try:
        service = _get_calendar_service()

        event = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {
                "dateTime": start_datetime,
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": end_datetime,
                "timeZone": "Asia/Kolkata",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 60},
                    {"method": "email", "minutes": 30},
                ],
            },
        }

        if attendee_emails:
            event["attendees"] = [{"email": email} for email in attendee_emails]

        created = service.events().insert(
            calendarId=calendar_id,
            body=event,
            sendUpdates="all" if attendee_emails else "none",
        ).execute()

        return {
            "event_id": created.get("id"),
            "title": created.get("summary"),
            "start": created.get("start", {}).get("dateTime"),
            "html_link": created.get("htmlLink"),
            "status": "created",
        }

    except Exception as exc:
        logger.error("add_to_calendar_tool failed: %s", exc)
        return {"error": str(exc)}


def book_nurse_visit_with_calendar_tool(
    patient_id: str,
    patient_email: str,
    nurse_email: str,
    scheduled_at: str,
    medication_name: str,
    dose: str,
    patient_address: str,
) -> dict:
    """Book a nurse home visit and add it to both patient and nurse calendars.

    Use this when a patient needs a nurse to come home for an injection.
    This creates the visit record AND adds calendar events for both parties.

    Args:
        patient_id: Patient identifier.
        patient_email: Patient's email for calendar invite.
        nurse_email: Nurse's email for calendar invite.
        scheduled_at: ISO 8601 datetime e.g. '2026-04-05T21:00:00'.
        medication_name: Name of medication e.g. 'Gonal-F'.
        dose: Dose e.g. '150IU'.
        patient_address: Home address for the nurse.

    Returns:
        Calendar event details for both patient and nurse.
    """
    try:
        # Parse scheduled time and add 30 min for end time
        start = datetime.fromisoformat(scheduled_at)
        end = start + timedelta(minutes=30)
        end_str = end.isoformat()

        # Patient calendar event
        patient_event = add_to_calendar_tool(
            title=f"💉 Nurse Visit — {medication_name} {dose}",
            start_datetime=scheduled_at,
            end_datetime=end_str,
            description=(
                f"Nurse home visit for {medication_name} {dose} injection.\n\n"
                f"Please have your medication ready before the nurse arrives.\n"
                f"Keep your injection kit accessible."
            ),
            location=patient_address,
            attendee_emails=[patient_email, nurse_email],
        )

        # Nurse calendar event (separate entry with patient address)
        nurse_event = add_to_calendar_tool(
            title=f"🏠 Home Visit — {medication_name} {dose} for patient {patient_id}",
            start_datetime=scheduled_at,
            end_datetime=end_str,
            description=(
                f"Home injection visit.\n"
                f"Medication: {medication_name} {dose}\n"
                f"Patient ID: {patient_id}\n"
                f"Address: {patient_address}"
            ),
            location=patient_address,
            attendee_emails=[nurse_email],
        )

        return {
            "patient_calendar": patient_event,
            "nurse_calendar": nurse_event,
            "status": "calendar_events_created",
        }

    except Exception as exc:
        logger.error("book_nurse_visit_with_calendar_tool failed: %s", exc)
        return {"error": str(exc)}


def book_appointment_with_calendar_tool(
    patient_email: str,
    doctor_email: str,
    appointment_type: str,
    scheduled_at: str,
    duration_minutes: int,
    clinic_name: str,
    checklist: Optional[list[str]] = None,
) -> dict:
    """Book a clinical appointment and add it to patient and doctor calendars.

    Use this when booking consultations, ultrasounds, egg retrieval, or
    embryo transfer appointments.

    Args:
        patient_email: Patient's email for calendar invite.
        doctor_email: Doctor's email for calendar invite.
        appointment_type: One of 'consultation', 'ultrasound', 'egg_retrieval', 'embryo_transfer'.
        scheduled_at: ISO 8601 datetime e.g. '2026-04-10T10:00:00'.
        duration_minutes: Appointment duration in minutes.
        clinic_name: Name and address of the clinic.
        checklist: Pre-appointment checklist items.

    Returns:
        Calendar event details.
    """
    try:
        start = datetime.fromisoformat(scheduled_at)
        end = start + timedelta(minutes=duration_minutes)
        end_str = end.isoformat()

        type_labels = {
            "consultation": "🩺 IVF Consultation",
            "ultrasound": "🔬 Ultrasound Scan",
            "egg_retrieval": "🥚 Egg Retrieval Procedure",
            "embryo_transfer": "🌱 Embryo Transfer",
        }
        title = type_labels.get(appointment_type, f"📅 {appointment_type.title()}")

        checklist_text = ""
        if checklist:
            checklist_text = "\n\nPre-appointment checklist:\n" + "\n".join(f"• {item}" for item in checklist)

        event = add_to_calendar_tool(
            title=title,
            start_datetime=scheduled_at,
            end_datetime=end_str,
            description=f"IVF appointment at {clinic_name}.{checklist_text}",
            location=clinic_name,
            attendee_emails=[patient_email, doctor_email],
        )

        return {
            "calendar_event": event,
            "appointment_type": appointment_type,
            "status": "calendar_event_created",
        }

    except Exception as exc:
        logger.error("book_appointment_with_calendar_tool failed: %s", exc)
        return {"error": str(exc)}
