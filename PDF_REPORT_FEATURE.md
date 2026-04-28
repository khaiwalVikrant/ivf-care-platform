# PDF Report Generation Feature

## Overview

The IVF Advisor now generates professional, personalized PDF reports that patients can download, print, and share with their partners or doctors.

## How It Works

### For Users
1. Chat with the IVF Advisor about your treatment (costs, timeline, lab results, etc.)
2. Click the **"📄 Download My IVF Plan (PDF)"** button that appears after your first conversation
3. The agent will generate a comprehensive PDF with all discussed topics
4. Download the PDF from the provided link

### For Developers

**Tool**: `generate_report_tool` in `ivf_advisor/tools/report_generator.py`

**Agent Integration**: The agent automatically calls this tool when:
- User explicitly asks to download/save their plan
- User clicks the "Download My IVF Plan" button in the UI

**PDF Sections** (included based on conversation):
- Patient Profile Summary
- Lab Results Interpretation (AMH, FSH, AFC)
- Treatment Timeline (week-by-week schedule)
- Cost Breakdown (city-specific INR ranges for India)
- Wellness & Lifestyle Guide (diet, exercise, supplements)
- Injection Administration Guide (step-by-step instructions)

**Storage**: PDFs are uploaded to Google Cloud Storage and a public URL is returned.

## Setup

### 1. Install Dependencies
```bash
pip install reportlab google-cloud-storage
```

### 2. Configure Cloud Storage Bucket
```bash
# Set environment variable (optional - defaults to {PROJECT_ID}-ivf-reports)
export REPORT_BUCKET_NAME="your-bucket-name"
```

The bucket will be created automatically on first use if it doesn't exist.

### 3. Test the Feature
```python
from ivf_advisor.tools.report_generator import generate_report_tool

result = generate_report_tool(
    patient_name="Sarah Johnson",
    patient_id="P-12345",
    cycle_id="C-67890",
    include_timeline=True,
    include_costs=True,
)

print(result.report_url)  # Download link
```

## Demo Script

**For the Google Cloud Gen AI Academy presentation:**

1. **Setup** (before demo):
   - Have a conversation covering multiple topics (lab results, costs, timeline)
   - Show the "Download My IVF Plan" button appearing

2. **Demo flow**:
   - "Sarah has been chatting with the IVF Advisor for a few minutes..."
   - "She's learned about her lab results, Mumbai costs, and her treatment timeline"
   - "Now she wants something tangible to share with her partner"
   - *Click "Download My IVF Plan" button*
   - "The agent generates a professional PDF with everything we discussed"
   - *Show the PDF opening* (clean, branded, comprehensive)
   - "Sarah can now print this, email it to her doctor, or share it with her family"

3. **Key talking points**:
   - "This isn't just a chat transcript - it's a structured, actionable plan"
   - "Stored in Google Cloud Storage for reliability"
   - "Generated on-demand with only relevant sections"
   - "Professional formatting makes it clinic-ready"

## Technical Details

### PDF Generation
- **Library**: ReportLab (industry-standard Python PDF library)
- **Styling**: Custom purple/pink gradient theme matching the UI
- **Layout**: Professional document with headers, sections, tables, and disclaimer
- **Size**: Typically 2-4 pages depending on content

### Cloud Storage Integration
- **Bucket**: Auto-created in `us-central1` region
- **Access**: Public URLs for easy sharing
- **Naming**: `IVF_Plan_{PatientName}_{Timestamp}.pdf`
- **Fallback**: Base64-encoded data URL if upload fails

### Performance
- **Generation time**: ~500ms for typical report
- **Upload time**: ~200ms to Cloud Storage
- **Total**: <1 second end-to-end

## Future Enhancements

Potential additions for post-competition:
- Email delivery integration
- WhatsApp sharing
- Multi-language support (Hindi PDFs)
- Clinic branding customization
- Appointment calendar integration (add .ics file)
- Progress tracking (update PDF as treatment progresses)

## Troubleshooting

**PDF generation fails**:
- Check `reportlab` is installed: `pip install reportlab`
- Check logs for specific error

**Upload to Cloud Storage fails**:
- Verify `GOOGLE_CLOUD_PROJECT` environment variable is set
- Check Cloud Storage API is enabled
- Verify service account has `storage.objects.create` permission
- Fallback: PDF will be returned as base64 data URL

**Button doesn't appear**:
- Check browser console for JavaScript errors
- Verify `download_report_btn` is in all `outputs=` lists
- Check CSS class `.download-report-btn` is defined

## Files Modified

- `ivf_advisor/tools/report_generator.py` - New tool implementation
- `ivf_advisor/agent.py` - Tool registration and system instruction
- `ivf_advisor/ui.py` - Download button UI and event wiring
- `pyproject.toml` - Added `reportlab` and `google-cloud-storage` dependencies
