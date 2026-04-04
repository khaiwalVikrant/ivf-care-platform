"""Email notification tool for IVF care platform using SMTP."""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587
_SENDER_EMAIL = os.getenv("NOTIFICATION_EMAIL", "")
_SENDER_PASSWORD = os.getenv("NOTIFICATION_EMAIL_PASSWORD", "")
_SENDER_NAME = "IVF Care Platform"


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send an email via Gmail SMTP."""
    if not _SENDER_EMAIL or not _SENDER_PASSWORD:
        logger.warning("Email credentials not configured — skipping email notification")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{_SENDER_NAME} <{_SENDER_EMAIL}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

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
) -> dict:
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
) -> dict:
    """Send nurse visit notifications to both patient and nurse.

    Use this after booking a nurse home visit to notify both parties.

    Args:
        patient_email: Patient's email address.
        patient_name: Patient's name.
        nurse_email: Nurse's email address.
        scheduled_at: Human-readable datetime e.g. 'Tomorrow at 9:00 PM'.
        medication_name: Medication name e.g. 'Gonal-F'.
        dose: Dose e.g. '150IU'.
        patient_address: Home address for the nurse.

    Returns:
        Dict with sent status for patient and nurse.
    """
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
    )
    nurse_sent = _send_email(
        nurse_email,
        f"🏠 Home Visit Assignment — {patient_name} — {scheduled_at}",
        nurse_html,
    )

    return {
        "patient_email_sent": patient_sent,
        "nurse_email_sent": nurse_sent,
        "scheduled_at": scheduled_at,
        "medication": f"{medication_name} {dose}",
    }
