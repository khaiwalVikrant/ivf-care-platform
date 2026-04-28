"""PDF report generation tool for personalized IVF plans."""

from __future__ import annotations

import io
import os
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from ivf_advisor.models import PatientProfile


class ReportSection(BaseModel):
    """A section of the PDF report."""
    title: str
    content: str
    icon: Optional[str] = None


class ReportData(BaseModel):
    """Data structure for generating a personalized IVF report."""
    patient_name: str = Field(description="Patient's full name")
    patient_id: Optional[str] = Field(default=None, description="Patient ID")
    cycle_id: Optional[str] = Field(default=None, description="Current cycle ID")
    profile: Optional[PatientProfile] = Field(default=None, description="Patient profile data")
    sections: list[ReportSection] = Field(default_factory=list, description="Report sections to include")
    generated_date: str = Field(default_factory=lambda: datetime.now().strftime("%B %d, %Y"))


class ReportOutput(BaseModel):
    """Output from report generation."""
    success: bool
    report_url: Optional[str] = None
    report_filename: Optional[str] = None
    error_message: Optional[str] = None


def generate_pdf_report(report_data: ReportData) -> bytes:
    """Generate a professional PDF report using reportlab.
    
    Args:
        report_data: The structured data for the report
        
    Returns:
        PDF bytes
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#7c3aed'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#6b7280'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica',
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#7c3aed'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderColor=colors.HexColor('#e5e7eb'),
        borderPadding=6,
        backColor=colors.HexColor('#f5f3ff'),
        borderRadius=4,
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#374151'),
        spaceAfter=10,
        alignment=TA_JUSTIFY,
        fontName='Helvetica',
        leading=14,
    )
    
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#92400e'),
        spaceAfter=10,
        alignment=TA_LEFT,
        fontName='Helvetica-Oblique',
        backColor=colors.HexColor('#fffbeb'),
        borderWidth=1,
        borderColor=colors.HexColor('#fcd34d'),
        borderPadding=8,
        borderRadius=4,
    )
    
    # Header
    elements.append(Paragraph("🌸 Your Personalized IVF Plan", title_style))
    elements.append(Paragraph(
        f"Prepared for {report_data.patient_name} • {report_data.generated_date}",
        subtitle_style
    ))
    elements.append(Spacer(1, 0.2*inch))
    
    # Patient Information Box
    if report_data.patient_id or report_data.cycle_id or report_data.profile:
        patient_info_data = []
        if report_data.patient_id:
            patient_info_data.append(['Patient ID:', report_data.patient_id])
        if report_data.cycle_id:
            patient_info_data.append(['Cycle ID:', report_data.cycle_id])
        if report_data.profile:
            if report_data.profile.age:
                patient_info_data.append(['Age:', str(report_data.profile.age)])
            if report_data.profile.diagnosis:
                patient_info_data.append(['Diagnosis:', report_data.profile.diagnosis])
        
        if patient_info_data:
            patient_table = Table(patient_info_data, colWidths=[1.5*inch, 4*inch])
            patient_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f3ff')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7c3aed')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#374151')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            elements.append(patient_table)
            elements.append(Spacer(1, 0.3*inch))
    
    # Report Sections
    for section in report_data.sections:
        section_title = section.title
        if section.icon:
            section_title = f"{section.icon} {section.title}"
        
        elements.append(Paragraph(section_title, heading_style))
        
        # Split content by paragraphs and format
        paragraphs = section.content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                # Handle bullet points
                if para.strip().startswith('•') or para.strip().startswith('-'):
                    lines = para.split('\n')
                    for line in lines:
                        if line.strip():
                            clean_line = line.strip().lstrip('•-').strip()
                            elements.append(Paragraph(f"• {clean_line}", body_style))
                else:
                    elements.append(Paragraph(para.strip(), body_style))
        
        elements.append(Spacer(1, 0.15*inch))
    
    # Disclaimer
    elements.append(Spacer(1, 0.3*inch))
    disclaimer_text = (
        "<b>⚠️ Medical Disclaimer:</b> This document provides general educational information "
        "about IVF and fertility treatments. It is not a substitute for professional medical advice, "
        "diagnosis, or treatment. Always seek the guidance of your doctor or qualified fertility "
        "specialist with any questions you may have. Never disregard professional medical advice or "
        "delay seeking it because of information in this document."
    )
    elements.append(Paragraph(disclaimer_text, disclaimer_style))
    
    # Footer
    elements.append(Spacer(1, 0.2*inch))
    footer_text = (
        f"<i>Generated by IVF Care Platform • {report_data.generated_date} • "
        "For informational purposes only</i>"
    )
    footer_style_obj = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#9ca3af'),
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique',
    )
    elements.append(Paragraph(footer_text, footer_style_obj))
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


def upload_to_cloud_storage(pdf_bytes: bytes, filename: str) -> Optional[str]:
    """Upload PDF to Google Cloud Storage and return public URL."""
    try:
        from google.cloud import storage

        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        bucket_name = os.getenv("REPORT_BUCKET_NAME", f"{project_id}-ivf-reports")

        import logging
        logging.info(f"Uploading PDF to bucket: {bucket_name}, file: {filename}")

        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)

        blob = bucket.blob(f"reports/{filename}")
        blob.upload_from_string(pdf_bytes, content_type="application/pdf")
        # Bucket is already public via allUsers:objectViewer IAM policy
        # No need to call make_public() which requires getIamPolicy permission
        public_url = f"https://storage.googleapis.com/{bucket_name}/reports/{filename}"

        logging.info(f"PDF uploaded successfully: {public_url}")
        return public_url

    except Exception as e:
        import logging
        logging.error(f"Cloud Storage upload failed: {type(e).__name__}: {e}")
        return None


def generate_report_tool(
    patient_name: Optional[str] = None,
    patient_id: Optional[str] = None,
    cycle_id: Optional[str] = None,
    include_profile: bool = True,
    include_lab_results: bool = False,
    include_timeline: bool = False,
    include_costs: bool = False,
    include_wellness: bool = False,
    include_injection_guide: bool = False,
    profile_data: Optional[str] = None,
    lab_results_data: Optional[str] = None,
    timeline_data: Optional[str] = None,
    costs_data: Optional[str] = None,
    wellness_data: Optional[str] = None,
    injection_data: Optional[str] = None,
) -> ReportOutput:
    """Generate a personalized IVF plan PDF report for the patient.
    
    This tool creates a comprehensive PDF document that the patient can download,
    print, and share with their partner or doctor. The report includes selected
    sections based on what information has been discussed in the conversation.
    
    IMPORTANT: When including a section, you MUST provide the actual data discussed
    in the conversation. Do not just set the flag to True without providing the content.
    
    Args:
        patient_name: The patient's full name (defaults to "Patient" if not provided)
        patient_id: Optional patient ID
        cycle_id: Optional cycle ID
        include_profile: Include patient profile summary
        include_lab_results: Include lab results interpretation
        include_timeline: Include treatment timeline
        include_costs: Include cost breakdown
        include_wellness: Include wellness and lifestyle guide
        include_injection_guide: Include injection administration guide
        profile_data: Actual profile information discussed (age, diagnosis, history, etc.)
        lab_results_data: Actual lab results and interpretations discussed (AMH, FSH, AFC, sperm analysis, etc.)
        timeline_data: Actual timeline dates and events discussed
        costs_data: Actual cost breakdown discussed with specific amounts
        wellness_data: Actual wellness recommendations discussed
        injection_data: Actual injection instructions discussed
        
    Returns:
        ReportOutput with success status and download URL
    """
    try:
        # Use default values if parameters are None or empty
        final_patient_name = patient_name if patient_name and patient_name.strip() else "Patient"
        
        # Build report data
        report_data = ReportData(
            patient_name=final_patient_name,
            patient_id=patient_id,
            cycle_id=cycle_id,
        )
        
        # Add sections based on flags and actual data
        if include_profile and profile_data:
            report_data.sections.append(ReportSection(
                title="Your Profile Summary",
                icon="👤",
                content=profile_data
            ))
        
        if include_lab_results and lab_results_data:
            report_data.sections.append(ReportSection(
                title="Lab Results Interpretation",
                icon="🧬",
                content=lab_results_data
            ))
        
        if include_timeline and timeline_data:
            report_data.sections.append(ReportSection(
                title="Your Treatment Timeline",
                icon="📅",
                content=timeline_data
            ))
        
        if include_costs and costs_data:
            report_data.sections.append(ReportSection(
                title="Cost Breakdown",
                icon="💰",
                content=costs_data
            ))
        
        if include_wellness and wellness_data:
            report_data.sections.append(ReportSection(
                title="Wellness & Lifestyle Guide",
                icon="🥗",
                content=wellness_data
            ))
        
        if include_injection_guide and injection_data:
            report_data.sections.append(ReportSection(
                title="Injection Administration Guide",
                icon="💉",
                content=injection_data
            ))
        
        # Generate PDF
        pdf_bytes = generate_pdf_report(report_data)
        
        # Generate filename - sanitize to remove any invalid characters
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', patient_name.replace(" ", "_"))
        safe_name = safe_name[:30]  # limit length
        filename = f"IVF_Plan_{safe_name}_{timestamp}.pdf"
        
        # Upload to Cloud Storage
        public_url = upload_to_cloud_storage(pdf_bytes, filename)
        
        if public_url:
            return ReportOutput(
                success=True,
                report_url=public_url,
                report_filename=filename,
            )
        else:
            # Fallback: return base64 encoded PDF if upload fails
            import base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            return ReportOutput(
                success=True,
                report_url=f"data:application/pdf;base64,{pdf_base64}",
                report_filename=filename,
            )
    
    except Exception as e:
        import logging
        logging.exception("Failed to generate PDF report")
        return ReportOutput(
            success=False,
            error_message=f"Failed to generate report: {str(e)}"
        )
