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


def _validate_section_data(section_name: str, data: str) -> bool:
    """Validate that section data contains actual personalized content, not generic descriptions.
    
    Args:
        section_name: Name of the section being validated
        data: The content to validate
        
    Returns:
        True if data appears to be personalized, False if it contains generic phrases
    """
    if not data or not data.strip():
        return False
    
    # Generic phrases that should NOT appear in personalized reports
    # These are from the welcome message and indicate the agent is hallucinating
    generic_phrases = [
        "Build a personalised treatment timeline",
        "Break down IVF costs in your city",
        "Interpret lab results — AMH, FSH, AFC",
        "Guide you through injections and medications",
        "Answer clinical questions with evidence",
        "Provide emotional support when you need it",
        "I can help you:",
        "Just tell me what you need",
    ]
    
    data_lower = data.lower()
    for phrase in generic_phrases:
        if phrase.lower() in data_lower:
            import logging
            logging.error(
                f"❌ PDF VALIDATION FAILED: Section '{section_name}' contains generic phrase: '{phrase}'. "
                f"This should be actual personalized data from the conversation, not feature descriptions. "
                f"Data preview: {data[:200]}..."
            )
            return False
    
    # Additional validation: Check for minimum content length
    # Real personalized data should be substantial
    if len(data.strip()) < 50:
        import logging
        logging.warning(
            f"⚠️ PDF VALIDATION WARNING: Section '{section_name}' has very short content ({len(data)} chars). "
            f"Consider providing more detailed information."
        )
    
    return True


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
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.6*inch,
        bottomMargin=0.6*inch,
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom color palette (matching UI theme)
    purple_primary = colors.HexColor('#7c3aed')
    purple_light = colors.HexColor('#f5f3ff')
    purple_medium = colors.HexColor('#ede9fe')
    gray_dark = colors.HexColor('#374151')
    gray_medium = colors.HexColor('#6b7280')
    gray_light = colors.HexColor('#e5e7eb')
    pink_accent = colors.HexColor('#db2777')
    yellow_bg = colors.HexColor('#fffbeb')
    yellow_border = colors.HexColor('#fcd34d')
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=purple_primary,
        spaceAfter=8,
        spaceBefore=0,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=32,
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=gray_medium,
        spaceAfter=24,
        alignment=TA_CENTER,
        fontName='Helvetica',
        leading=16,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=purple_primary,
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        leading=20,
        leftIndent=0,
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=gray_dark,
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        leading=16,
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor=gray_dark,
        spaceAfter=8,
        alignment=TA_LEFT,
        fontName='Helvetica',
        leading=16,
        leftIndent=0,
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=11,
        textColor=gray_dark,
        spaceAfter=6,
        alignment=TA_LEFT,
        fontName='Helvetica',
        leading=15,
        leftIndent=20,
        bulletIndent=10,
    )
    
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#92400e'),
        spaceAfter=10,
        spaceBefore=10,
        alignment=TA_JUSTIFY,
        fontName='Helvetica',
        leading=13,
        leftIndent=12,
        rightIndent=12,
    )
    
    # Header with decorative line
    elements.append(Paragraph("🌸 Your Personalized IVF Plan", title_style))
    elements.append(Spacer(1, 0.05*inch))
    
    # Decorative line under title (using table for compatibility)
    line_table = Table([['']], colWidths=[6.5*inch])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 2, purple_primary),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 0.08*inch))
    
    elements.append(Paragraph(
        f"Prepared for <b>{report_data.patient_name}</b> • {report_data.generated_date}",
        subtitle_style
    ))
    elements.append(Spacer(1, 0.15*inch))
    
    # Patient Information Box with enhanced styling
    if report_data.patient_id or report_data.cycle_id or report_data.profile:
        patient_info_data = []
        if report_data.patient_id:
            patient_info_data.append(['Patient ID:', report_data.patient_id])
        if report_data.cycle_id:
            patient_info_data.append(['Cycle ID:', report_data.cycle_id])
        if report_data.profile:
            if report_data.profile.age:
                patient_info_data.append(['Age:', f"{report_data.profile.age} years"])
            if report_data.profile.diagnosis:
                patient_info_data.append(['Diagnosis:', report_data.profile.diagnosis])
        
        if patient_info_data:
            patient_table = Table(patient_info_data, colWidths=[1.8*inch, 4.5*inch])
            patient_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), purple_light),
                ('TEXTCOLOR', (0, 0), (0, -1), purple_primary),
                ('TEXTCOLOR', (1, 0), (1, -1), gray_dark),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, gray_light),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ('BOX', (0, 0), (-1, -1), 2, purple_primary),
            ]))
            elements.append(patient_table)
            elements.append(Spacer(1, 0.3*inch))
    
    # Report Sections with enhanced formatting
    for idx, section in enumerate(report_data.sections):
        # Section header with icon and decorative line
        section_title = section.title
        if section.icon:
            section_title = f"{section.icon}  {section.title}"
        
        elements.append(Paragraph(section_title, heading_style))
        
        # Decorative line under section heading (using table for compatibility)
        section_line = Table([['']], colWidths=[2*inch])
        section_line.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1.5, purple_primary),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(section_line)
        
        # Split content by paragraphs and format
        paragraphs = section.content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                # Handle different content types
                lines = para.split('\n')
                
                # Check if this is a list of items
                is_list = all(line.strip().startswith(('•', '-', '*')) or not line.strip() for line in lines if line.strip())
                
                if is_list:
                    # Format as bullet list
                    for line in lines:
                        if line.strip():
                            clean_line = line.strip().lstrip('•-*').strip()
                            if clean_line:
                                elements.append(Paragraph(f"• {clean_line}", bullet_style))
                else:
                    # Check for subheadings (lines ending with colon)
                    for line in lines:
                        if line.strip():
                            if line.strip().endswith(':') and len(line.strip()) < 60:
                                # This is a subheading
                                elements.append(Paragraph(f"<b>{line.strip()}</b>", subheading_style))
                            elif line.strip().startswith(('•', '-', '*')):
                                # Bullet point
                                clean_line = line.strip().lstrip('•-*').strip()
                                elements.append(Paragraph(f"• {clean_line}", bullet_style))
                            else:
                                # Regular paragraph
                                elements.append(Paragraph(line.strip(), body_style))
        
        # Add spacing between sections
        if idx < len(report_data.sections) - 1:
            elements.append(Spacer(1, 0.25*inch))
    
    # Disclaimer box with enhanced styling
    elements.append(Spacer(1, 0.35*inch))
    
    # Decorative line before disclaimer (using table for compatibility)
    divider_line = Table([['']], colWidths=[6.5*inch])
    divider_line.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, gray_light),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    elements.append(divider_line)
    
    disclaimer_text = (
        "<b>⚠️ Medical Disclaimer:</b> This document provides general educational information "
        "about IVF and fertility treatments. It is not a substitute for professional medical advice, "
        "diagnosis, or treatment. Always seek the guidance of your doctor or qualified fertility "
        "specialist with any questions you may have. Never disregard professional medical advice or "
        "delay seeking it because of information in this document."
    )
    
    # Create disclaimer box
    disclaimer_table = Table([[Paragraph(disclaimer_text, disclaimer_style)]], colWidths=[6.5*inch])
    disclaimer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), yellow_bg),
        ('BOX', (0, 0), (-1, -1), 1.5, yellow_border),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
    ]))
    elements.append(disclaimer_table)
    
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
        textColor=gray_medium,
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
        
        # HARD BLOCK: Check if ANY actual data was provided
        # Count how many sections have data that could potentially be valid
        sections_with_data = 0
        if include_profile and profile_data and profile_data.strip():
            sections_with_data += 1
        if include_lab_results and lab_results_data and lab_results_data.strip():
            sections_with_data += 1
        if include_timeline and timeline_data and timeline_data.strip():
            sections_with_data += 1
        if include_costs and costs_data and costs_data.strip():
            sections_with_data += 1
        if include_wellness and wellness_data and wellness_data.strip():
            sections_with_data += 1
        if include_injection_guide and injection_data and injection_data.strip():
            sections_with_data += 1
        
        # If no sections have data, refuse to generate PDF
        if sections_with_data == 0:
            import logging
            logging.error(
                "❌ PDF GENERATION BLOCKED: No actual data provided for any section. "
                "Agent attempted to generate PDF without discussing any topics with the patient. "
                "This would result in an empty PDF."
            )
            return ReportOutput(
                success=False,
                error_message=(
                    "Cannot generate PDF: No information has been discussed yet. "
                    "Please ask about costs, timeline, lab results, wellness, or injection guidance first, "
                    "then I can create a personalized PDF with that information."
                )
            )
        
        # Build report data
        report_data = ReportData(
            patient_name=final_patient_name,
            patient_id=patient_id,
            cycle_id=cycle_id,
        )
        
        # Add sections based on flags and actual data
        # IMPORTANT: Validate that data is personalized, not generic
        if include_profile and profile_data:
            if _validate_section_data("Profile", profile_data):
                report_data.sections.append(ReportSection(
                    title="Your Profile Summary",
                    icon="👤",
                    content=profile_data
                ))
            else:
                import logging
                logging.error("Skipping Profile section - contains generic content instead of actual patient data")
        
        if include_lab_results and lab_results_data:
            if _validate_section_data("Lab Results", lab_results_data):
                report_data.sections.append(ReportSection(
                    title="Lab Results Interpretation",
                    icon="🧬",
                    content=lab_results_data
                ))
            else:
                import logging
                logging.error("Skipping Lab Results section - contains generic content instead of actual lab values")
        
        if include_timeline and timeline_data:
            if _validate_section_data("Timeline", timeline_data):
                report_data.sections.append(ReportSection(
                    title="Your Treatment Timeline",
                    icon="📅",
                    content=timeline_data
                ))
            else:
                import logging
                logging.error("Skipping Timeline section - contains generic content instead of actual dates/events")
        
        if include_costs and costs_data:
            if _validate_section_data("Costs", costs_data):
                report_data.sections.append(ReportSection(
                    title="Cost Breakdown",
                    icon="💰",
                    content=costs_data
                ))
            else:
                import logging
                logging.error("Skipping Costs section - contains generic content instead of actual cost amounts")
        
        if include_wellness and wellness_data:
            if _validate_section_data("Wellness", wellness_data):
                report_data.sections.append(ReportSection(
                    title="Wellness & Lifestyle Guide",
                    icon="🥗",
                    content=wellness_data
                ))
            else:
                import logging
                logging.error("Skipping Wellness section - contains generic content instead of actual recommendations")
        
        if include_injection_guide and injection_data:
            if _validate_section_data("Injection Guide", injection_data):
                report_data.sections.append(ReportSection(
                    title="Injection Administration Guide",
                    icon="💉",
                    content=injection_data
                ))
            else:
                import logging
                logging.error("Skipping Injection Guide section - contains generic content instead of actual instructions")
        
        # SECOND HARD BLOCK: Check if ANY sections passed validation
        if len(report_data.sections) == 0:
            import logging
            logging.error(
                "❌ PDF GENERATION BLOCKED: All sections failed validation. "
                "Agent provided generic/welcome message content instead of actual conversation data. "
                f"Attempted sections: profile={include_profile}, lab_results={include_lab_results}, "
                f"timeline={include_timeline}, costs={include_costs}, wellness={include_wellness}, "
                f"injection_guide={include_injection_guide}"
            )
            return ReportOutput(
                success=False,
                error_message=(
                    "Cannot generate PDF: The information provided was too generic. "
                    "I need to discuss specific details with you first (actual costs, dates, lab values, etc.) "
                    "before I can create a meaningful PDF. What would you like to know about?"
                )
            )
        
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
