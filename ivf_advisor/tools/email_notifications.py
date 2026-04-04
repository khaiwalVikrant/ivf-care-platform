"""Email notification tool for IVF care platform using SMTP."""

from __future__ import annotations

import logging
import os
import smtplib
import uuid
from datetime import datetime, timedelta
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from typing import Optional

logger = logging.getLogger(__name__)

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587
_SENDER_EMAIL = os.getenv("NOTIFICATION_EMAIL", "")
_SENDER_PASSWORD = os.getenv("NOTIFICATION_EMAIL_PASSWORD", "")
_SENDER_NAME = "IVF Care Platform"


def _make_ics(
    title: str,
    start_dt: datetime,
    end_dt: datetime,
    location: str,
    description: str,
    organizer_email: str,
) -> bytes:
    """Generate an iCalendar (.ics) file as bytes."""
    uid = str(uuid.uuid4())
    fmt = "%Y%m%dT%H%M%SZ"
    now = datetime.utcnow().strftime(fmt)
    start = start_dt.strftime(fmt)
    end = end_dt.strftime(fmt)
    # Escape special chars in description
    desc = description.replace("\n", "\\n").replace(",", "\\,")
    loc = location.replace(",", "\\,")

    ics = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//IVF Care Platform//EN\r\n"
        "METHOD:REQUEST\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{uid}\r\n"
        f"DTSTAMP:{now}\r\n"
        f"DTSTART:{start}\r\n"
        f"DTEND:{end}\r\n"
        f"SUMMARY:{title}\r\n"
        f"DESCRIPTION:{desc}\r\n"
        f"LOCATION:{loc}\r\n"
        f"ORGANIZER:mailto:{organizer_email}\r\n"
        "BEGIN:VALARM\r\n"
        "TRIGGER:-PT60M\r\n"
        "ACTION:DISPLAY\r\n"
        "DESCRIPTION:Reminder\r\n"
        "END:VALARM\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
    return ics.encode("utf-8")


def _send_email(
    to_email: str,
    subject: str,
    html_body: str,
    ics_bytes: Optional[bytes] = None,
    ics_filename: str = "appointment.ics",
) -> bool:
    """Send an email via Gmail SMTP with optional .ics attachment."""
    if not _SENDER_EMAIL or not _SENDER_PASSWORD:
        logger.warning("Email credentials not configured — skipping email notification")
        return False

    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = f"{_SENDER_NAME} <{_SENDER_EMAIL}>"
        msg["To"] = to_email

        # HTML body
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(html_body, "html"))
        msg.attach(alt)

        # Attach .ics file if provided
        if ics_bytes:
            ics_part = MIMEBase("text", "calendar", method="REQUEST", name=ics_filename)
            ics_part.set_payload(ics_bytes)
            encoders.encode_base64(ics_part)
            ics_part.add_header("Content-Disposition", "attachment", filename=ics_filename)
            msg.attach(ics_part)

        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
            server.starttls()
            server.login(_SENDER_EMAIL, _SENDER_PASSWORD)
            server.sendmail(_SENDER_EMAIL, to_email, msg.as_string())
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to_email, exc)
        return False


def send_appointment_confirmation_tool(
    patient_email: str,
    patient_name: str,
    appointment_type: str,
    scheduled_at: str,
    clinic_name: str,
    location: str,
    checklist: Optional[list[str]] = None,
    doctor_email: Optional[str] = None,
    scheduled_at_iso: Optional[str] = None,
    duration_minutes: int = 60,
) -> dict:
    """Send appointment confirmation emails with .ics calendar attachment.

    Recipients can click 'Add to Calendar' to add the event to their
    Google Calendar, Apple Calendar, or Outlook.

    Args:
        patient_email: Patient's email address.
        patient_name: Patient's name for personalisation.
        appointment_type: e.g. 'consultation', 'ultrasound', 'egg_retrieval'.
        scheduled_at: Human-readable datetime e.g. 'Friday, April 5 at 3:30 PM'.
        clinic_name: Name of the clinic.
        location: Clinic address.
        checklist: Pre-appointment checklist items.
        doctor_email: Optional doctor email to send a copy.
        scheduled_at_iso: ISO 8601 datetime for .ics e.g. '2026-04-05T15:30:00'.
        duration_minutes: Appointment duration in minutes (default 60).

    Returns:
        Dict with sent status for patient and doctor.
    """
    type_labels = {
        "consultation": "Consultation Appointment",
        "ultrasound": "Ultrasound Scan",
        "egg_retrieval": "Egg Retrieval Procedure",
        "embryo_transfer": "Embryo Transfer",
    }
    appt_label = type_labels.get(appointment_type, appointment_type.title())

    checklist_html = ""
    checklist_text = ""
    if checklist:
        items = "".join(f"<li>{item}</li>" for item in checklist)
        checklist_html = f"""
        <div style="background:#f5f3ff;border-radius:8px;padding:16px;margin-top:16px">
            <strong style="color:#5b21b6">Pre-appointment checklist:</strong>
            <ul style="margin:8px 0 0 0;color:#374151">{items}</ul>
        </div>"""
        checklist_text = "\n\nPre-appointment checklist:\n" + "\n".join(f"• {i}" for i in checklist)

    # Generate .ics file
    ics_bytes = None
    if scheduled_at_iso:
        try:
            start_dt = datetime.fromisoformat(scheduled_at_iso)
            end_dt = start_dt + timedelta(minutes=duration_minutes)
            ics_bytes = _make_ics(
                title=f"{appt_label} — {clinic_name}",
                start_dt=start_dt,
                end_dt=end_dt,
                location=location,
                description=f"IVF appointment at {clinic_name}.{checklist_text}",
                organizer_email=_SENDER_EMAIL or "noreply@ivfcare.app",
            )
        except Exception as exc:
            logger.warning("Could not generate .ics: %s", exc)

    patient_html = f"""
    <div style="font-family:Inter,sans-serif;max-width:600px;margin:auto">
        <div style="background:linear-gradient(135deg,#7c3aed,#db2777);padding:24px;border-radius:12px 12px 0 0">
            <h1 style="color:white;margin:0;font-size:1.4rem">🌸 IVF Care Platform</h1>
            <p style="color:rgba(255,255,255,0.85);margin:4px 0 0 0">Appointment Confirmation</p>
        </div>
        <div style="background:white;padding:24px;border:1px solid #e9d5ff;border-radius:0 0 12px 12px">
            <p style="color:#374151">Dear <strong>{patient_name}</strong>,</p>
            <p style="color:#374151">Your appointment has been confirmed:</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0">
                <tr><td style="padding:8px;color:#6b7280;width:40%">Type</td>
                    <td style="padding:8px;color:#111827;font-weight:600">{appt_label}</td></tr>
                <tr style="background:#faf5ff"><td style="padding:8px;color:#6b7280">Date & Time</td>
                    <td style="padding:8px;color:#111827;font-weight:600">{scheduled_at}</td></tr>
                <tr><td style="padding:8px;color:#6b7280">Clinic</td>
                    <td style="padding:8px;color:#111827;font-weight:600">{clinic_name}</td></tr>
                <tr style="background:#faf5ff"><td style="padding:8px;color:#6b7280">Address</td>
                    <td style="padding:8px;color:#111827">{location}</td></tr>
            </table>
            {checklist_html}
            {"<p style='color:#7c3aed;margin-top:16px'>📅 <strong>Open the attached .ics file to add this appointment to your Google Calendar, Apple Calendar, or Outlook.</strong></p>" if ics_bytes else ""}
            <p style="color:#6b7280;font-size:0.85rem;margin-top:24px;border-top:1px solid #e9d5ff;padding-top:16px">
                This is an informational message from IVF Care Platform.
                Always follow your fertility specialist's guidance.
            </p>
        </div>
    </div>"""

    patient_sent = _send_email(
        patient_email,
        f"✅ Appointment Confirmed — {appt_label} at {clinic_name}",
        patient_html,
        ics_bytes=ics_bytes,
        ics_filename="appointment.ics",
    )

    doctor_sent = False
    if doctor_email:
        doctor_html = f"""
        <div style="font-family:Inter,sans-serif;max-width:600px;margin:auto">
            <div style="background:linear-gradient(135deg,#7c3aed,#db2777);padding:24px;border-radius:12px 12px 0 0">
                <h1 style="color:white;margin:0;font-size:1.4rem">🌸 IVF Care Platform</h1>
                <p style="color:rgba(255,255,255,0.85);margin:4px 0 0 0">New Appointment Booking</p>
            </div>
            <div style="background:white;padding:24px;border:1px solid #e9d5ff;border-radius:0 0 12px 12px">
                <p style="color:#374151">A new appointment has been booked:</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0">
                    <tr><td style="padding:8px;color:#6b7280;width:40%">Patient</td>
                        <td style="padding:8px;color:#111827;font-weight:600">{patient_name}</td></tr>
                    <tr style="background:#faf5ff"><td style="padding:8px;color:#6b7280">Type</td>
                        <td style="padding:8px;color:#111827;font-weight:600">{appt_label}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280">Date & Time</td>
                        <td style="padding:8px;color:#111827;font-weight:600">{scheduled_at}</td></tr>
                    <tr style="background:#faf5ff"><td style="padding:8px;color:#6b7280">Clinic</td>
                        <td style="padding:8px;color:#111827">{clinic_name}</td></tr>
                </table>
                {"<p style='color:#7c3aed'>📅 Open the attached .ics file to add to your calendar.</p>" if ics_bytes else ""}
            </div>
        </div>"""
        doctor_sent = _send_email(
            doctor_email,
            f"📅 New Appointment — {patient_name} — {appt_label}",
            doctor_html,
            ics_bytes=ics_bytes,
            ics_filename="appointment.ics",
        )

    return {
        "patient_email_sent": patient_sent,
        "doctor_email_sent": doctor_sent,
        "ics_attached": ics_bytes is not None,
        "appointment_type": appt_label,
        "scheduled_at": scheduled_at,
    }
    """Send appointment confirmation emails to patient and optionally doctor.

    Use this after booking an appointment to notify the patient and doctor
    via email with appointment details and pre-appointment checklist.

    Args:
        patient_email: Patient's email address.
        patient_name: Patient's name for personalisation.
        appointment_type: e.g. 'consultation', 'ultrasound', 'egg_retrieval'.
        scheduled_at: Human-readable datetime e.g. 'Friday, April 5 at 3:30 PM'.
        clinic_name: Name of the clinic.
        location: Clinic address.
        checklist: Pre-appointment checklist items.
        doctor_email: Optional doctor email to send a copy.

    Returns:
        Dict with sent status for patient and doctor.
    """
    type_labels = {
        "consultation": "Consultation Appointment",
        "ultrasound": "Ultrasound Scan",
        "egg_retrieval": "Egg Retrieval Procedure",
        "embryo_transfer": "Embryo Transfer",
    }
    appt_label = type_labels.get(appointment_type, appointment_type.title())

    checklist_html = ""
    if checklist:
        items = "".join(f"<li>{item}</li>" for item in checklist)
        checklist_html = f"""
        <div style="background:#f5f3ff;border-radius:8px;padding:16px;margin-top:16px">
            <strong style="color:#5b21b6">Pre-appointment checklist:</strong>
            <ul style="margin:8px 0 0 0;color:#374151">{items}</ul>
        </div>"""

    patient_html = f"""
    <div style="font-family:Inter,sans-serif;max-width:600px;margin:auto">
        <div style="background:linear-gradient(135deg,#7c3aed,#db2777);padding:24px;border-radius:12px 12px 0 0">
            <h1 style="color:white;margin:0;font-size:1.4rem">🌸 IVF Care Platform</h1>
            <p style="color:rgba(255,255,255,0.85);margin:4px 0 0 0">Appointment Confirmation</p>
        </div>
        <div style="background:white;padding:24px;border:1px solid #e9d5ff;border-radius:0 0 12px 12px">
            <p style="color:#374151">Dear <strong>{patient_name}</strong>,</p>
            <p style="color:#374151">Your appointment has been confirmed:</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0">
                <tr><td style="padding:8px;color:#6b7280;width:40%">Type</td>
                    <td style="padding:8px;color:#111827;font-weight:600">{appt_label}</td></tr>
                <tr style="background:#faf5ff"><td style="padding:8px;color:#6b7280">Date & Time</td>
                    <td style="padding:8px;color:#111827;font-weight:600">{scheduled_at}</td></tr>
                <tr><td style="padding:8px;color:#6b7280">Clinic</td>
                    <td style="padding:8px;color:#111827;font-weight:600">{clinic_name}</td></tr>
                <tr style="background:#faf5ff"><td style="padding:8px;color:#6b7280">Address</td>
                    <td style="padding:8px;color:#111827">{location}</td></tr>
            </table>
            {checklist_html}
            <p style="color:#6b7280;font-size:0.85rem;margin-top:24px;border-top:1px solid #e9d5ff;padding-top:16px">
                This is an informational message from IVF Care Platform.
                Always follow your fertility specialist's guidance.
            </p>
        </div>
    </div>"""

    patient_sent = _send_email(
        patient_email,
        f"✅ Appointment Confirmed — {appt_label} at {clinic_name}",
        patient_html,
    )

    doctor_sent = False
    if doctor_email:
        doctor_html = f"""
        <div style="font-family:Inter,sans-serif;max-width:600px;margin:auto">
            <div style="background:linear-gradient(135deg,#7c3aed,#db2777);padding:24px;border-radius:12px 12px 0 0">
                <h1 style="color:white;margin:0;font-size:1.4rem">🌸 IVF Care Platform</h1>
                <p style="color:rgba(255,255,255,0.85);margin:4px 0 0 0">New Appointment Booking</p>
            </div>
            <div style="background:white;padding:24px;border:1px solid #e9d5ff;border-radius:0 0 12px 12px">
                <p style="color:#374151">A new appointment has been booked:</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0">
                    <tr><td style="padding:8px;color:#6b7280;width:40%">Patient</td>
                        <td style="padding:8px;color:#111827;font-weight:600">{patient_name}</td></tr>
                    <tr style="background:#faf5ff"><td style="padding:8px;color:#6b7280">Type</td>
                        <td style="padding:8px;color:#111827;font-weight:600">{appt_label}</td></tr>
                    <tr><td style="padding:8px;color:#6b7280">Date & Time</td>
                        <td style="padding:8px;color:#111827;font-weight:600">{scheduled_at}</td></tr>
                    <tr style="background:#faf5ff"><td style="padding:8px;color:#6b7280">Clinic</td>
                        <td style="padding:8px;color:#111827">{clinic_name}</td></tr>
                </table>
            </div>
        </div>"""
        doctor_sent = _send_email(
            doctor_email,
            f"📅 New Appointment — {patient_name} — {appt_label}",
            doctor_html,
        )

    return {
        "patient_email_sent": patient_sent,
        "doctor_email_sent": doctor_sent,
        "appointment_type": appt_label,
        "scheduled_at": scheduled_at,
    }


def send_nurse_visit_notification_tool(
    patient_email: str,
    patient_name: str,
    nurse_email: str,
    scheduled_at: str,
    medication_name: str,
    dose: str,
    patient_address: str,
    scheduled_at_iso: Optional[str] = None,
) -> dict:
    """Send nurse visit notifications with .ics calendar attachment.

    Args:
        patient_email: Patient's email address.
        patient_name: Patient's name.
        nurse_email: Nurse's email address.
        scheduled_at: Human-readable datetime e.g. 'Tomorrow at 9:00 PM'.
        medication_name: Medication name e.g. 'Gonal-F'.
        dose: Dose e.g. '150IU'.
        patient_address: Home address for the nurse.
        scheduled_at_iso: ISO 8601 datetime for .ics e.g. '2026-04-05T21:00:00'.

    Returns:
        Dict with sent status for patient and nurse.
    """
    # Generate .ics
    ics_bytes = None
    if scheduled_at_iso:
        try:
            start_dt = datetime.fromisoformat(scheduled_at_iso)
            end_dt = start_dt + timedelta(minutes=30)
            ics_bytes = _make_ics(
                title=f"💉 Nurse Visit — {medication_name} {dose}",
                start_dt=start_dt,
                end_dt=end_dt,
                location=patient_address,
                description=f"Nurse home visit for {medication_name} {dose} injection.\nPatient: {patient_name}\nAddress: {patient_address}",
                organizer_email=_SENDER_EMAIL or "noreply@ivfcare.app",
            )
        except Exception as exc:
            logger.warning("Could not generate .ics: %s", exc)
    patient_html = f"""
    <div style="font-family:Inter,sans-serif;max-width:600px;margin:auto">
        <div style="background:linear-gradient(135deg,#7c3aed,#db2777);padding:24px;border-radius:12px 12px 0 0">
            <h1 style="color:white;margin:0;font-size:1.4rem">🌸 IVF Care Platform</h1>
            <p style="color:rgba(255,255,255,0.85);margin:4px 0 0 0">Nurse Visit Confirmed</p>
        </div>
        <div style="background:white;padding:24px;border:1px solid #e9d5ff;border-radius:0 0 12px 12px">
            <p style="color:#374151">Dear <strong>{patient_name}</strong>,</p>
            <p style="color:#374151">Your nurse home visit has been arranged:</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0">
                <tr><td style="padding:8px;color:#6b7280;width:40%">Date & Time</td>
                    <td style="padding:8px;color:#111827;font-weight:600">{scheduled_at}</td></tr>
                <tr style="background:#faf5ff"><td style="padding:8px;color:#6b7280">Medication</td>
                    <td style="padding:8px;color:#111827;font-weight:600">{medication_name} {dose}</td></tr>
            </table>
            <div style="background:#fef3c7;border-radius:8px;padding:12px;margin-top:8px">
                💡 Please have your medication and injection kit ready before the nurse arrives.
            </div>
        </div>
    </div>"""

    nurse_html = f"""
    <div style="font-family:Inter,sans-serif;max-width:600px;margin:auto">
        <div style="background:linear-gradient(135deg,#7c3aed,#db2777);padding:24px;border-radius:12px 12px 0 0">
            <h1 style="color:white;margin:0;font-size:1.4rem">🌸 IVF Care Platform</h1>
            <p style="color:rgba(255,255,255,0.85);margin:4px 0 0 0">Home Visit Assignment</p>
        </div>
        <div style="background:white;padding:24px;border:1px solid #e9d5ff;border-radius:0 0 12px 12px">
            <p style="color:#374151">You have been assigned a home visit:</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0">
                <tr><td style="padding:8px;color:#6b7280;width:40%">Patient</td>
                    <td style="padding:8px;color:#111827;font-weight:600">{patient_name}</td></tr>
                <tr style="background:#faf5ff"><td style="padding:8px;color:#6b7280">Date & Time</td>
                    <td style="padding:8px;color:#111827;font-weight:600">{scheduled_at}</td></tr>
                <tr><td style="padding:8px;color:#6b7280">Medication</td>
                    <td style="padding:8px;color:#111827;font-weight:600">{medication_name} {dose}</td></tr>
                <tr style="background:#faf5ff"><td style="padding:8px;color:#6b7280">Address</td>
                    <td style="padding:8px;color:#111827">{patient_address}</td></tr>
            </table>
        </div>
    </div>"""

    patient_sent = _send_email(
        patient_email,
        f"💉 Nurse Visit Confirmed — {scheduled_at}",
        patient_html,
        ics_bytes=ics_bytes,
        ics_filename="nurse_visit.ics",
    )
    nurse_sent = _send_email(
        nurse_email,
        f"🏠 Home Visit Assignment — {patient_name} — {scheduled_at}",
        nurse_html,
        ics_bytes=ics_bytes,
        ics_filename="nurse_visit.ics",
    )

    return {
        "patient_email_sent": patient_sent,
        "nurse_email_sent": nurse_sent,
        "ics_attached": ics_bytes is not None,
        "scheduled_at": scheduled_at,
        "medication": f"{medication_name} {dose}",
    }
