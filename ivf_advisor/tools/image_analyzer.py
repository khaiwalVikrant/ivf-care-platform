"""Image analysis tool for medical report interpretation using Google Cloud Vision API."""

from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel, Field


class ImageAnalysisOutput(BaseModel):
    """Output from image analysis."""
    success: bool
    extracted_text: Optional[str] = None
    interpretation: Optional[str] = None
    error_message: Optional[str] = None


def analyze_medical_report_image(image_path: str) -> ImageAnalysisOutput:
    """Analyze a medical report image using Google Cloud Vision API OCR.
    
    This tool extracts text from medical report images (lab results, prescriptions, etc.)
    and provides a structured interpretation of the values found.
    
    Args:
        image_path: Path to the uploaded image file
        
    Returns:
        ImageAnalysisOutput with extracted text and interpretation
    """
    try:
        from google.cloud import vision
        
        # Initialize Vision API client
        client = vision.ImageAnnotatorClient()
        
        # Read the image file
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        # Perform text detection
        response = client.text_detection(image=image)
        texts = response.text_annotations
        
        if response.error.message:
            return ImageAnalysisOutput(
                success=False,
                error_message=f"Vision API error: {response.error.message}"
            )
        
        if not texts:
            return ImageAnalysisOutput(
                success=False,
                error_message="No text found in the image. Please ensure the image is clear and contains readable text."
            )
        
        # First annotation contains the full extracted text
        extracted_text = texts[0].description
        
        # Parse common lab values
        interpretation = _interpret_lab_values(extracted_text)
        
        return ImageAnalysisOutput(
            success=True,
            extracted_text=extracted_text,
            interpretation=interpretation
        )
        
    except Exception as e:
        import logging
        logging.exception("Failed to analyze medical report image")
        return ImageAnalysisOutput(
            success=False,
            error_message=f"Image analysis failed: {str(e)}"
        )


def _interpret_lab_values(text: str) -> str:
    """Parse and interpret common fertility lab values from extracted text."""
    import re
    
    text_lower = text.lower()
    interpretations = []
    
    # AMH (Anti-Müllerian Hormone)
    amh_match = re.search(r'amh[:\s]+([0-9.]+)', text_lower)
    if amh_match:
        amh_value = float(amh_match.group(1))
        if amh_value < 1.0:
            amh_interp = f"AMH: {amh_value} ng/mL (Low ovarian reserve)"
        elif amh_value < 3.0:
            amh_interp = f"AMH: {amh_value} ng/mL (Normal ovarian reserve)"
        else:
            amh_interp = f"AMH: {amh_value} ng/mL (Good ovarian reserve)"
        interpretations.append(amh_interp)
    
    # FSH (Follicle Stimulating Hormone)
    fsh_match = re.search(r'fsh[:\s]+([0-9.]+)', text_lower)
    if fsh_match:
        fsh_value = float(fsh_match.group(1))
        if fsh_value < 10:
            fsh_interp = f"FSH: {fsh_value} mIU/mL (Normal range)"
        elif fsh_value < 15:
            fsh_interp = f"FSH: {fsh_value} mIU/mL (Borderline - may indicate reduced ovarian reserve)"
        else:
            fsh_interp = f"FSH: {fsh_value} mIU/mL (Elevated - suggests diminished ovarian reserve)"
        interpretations.append(fsh_interp)
    
    # AFC (Antral Follicle Count)
    afc_match = re.search(r'afc[:\s]+([0-9]+)', text_lower)
    if afc_match:
        afc_value = int(afc_match.group(1))
        if afc_value < 5:
            afc_interp = f"AFC: {afc_value} follicles (Low - poor ovarian reserve)"
        elif afc_value < 15:
            afc_interp = f"AFC: {afc_value} follicles (Normal range)"
        else:
            afc_interp = f"AFC: {afc_value} follicles (High - good ovarian reserve, possible PCOS)"
        interpretations.append(afc_interp)
    
    # Sperm Count
    sperm_count_match = re.search(r'(?:sperm count|concentration)[:\s]+([0-9.]+)\s*(?:million|mil)', text_lower)
    if sperm_count_match:
        count_value = float(sperm_count_match.group(1))
        if count_value < 15:
            count_interp = f"Sperm Count: {count_value} million/mL (Low - oligospermia)"
        else:
            count_interp = f"Sperm Count: {count_value} million/mL (Normal range)"
        interpretations.append(count_interp)
    
    # Motility
    motility_match = re.search(r'motility[:\s]+([0-9.]+)\s*%', text_lower)
    if motility_match:
        motility_value = float(motility_match.group(1))
        if motility_value < 40:
            motility_interp = f"Motility: {motility_value}% (Low - asthenospermia)"
        else:
            motility_interp = f"Motility: {motility_value}% (Normal range)"
        interpretations.append(motility_interp)
    
    if interpretations:
        return "\n".join(["**Interpreted Values:**"] + [f"• {i}" for i in interpretations])
    else:
        return "No standard fertility lab values detected. Please share the specific values you'd like me to interpret."


# Register as ADK tool
analyze_medical_report_image_tool = analyze_medical_report_image
