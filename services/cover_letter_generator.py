"""Cover Letter PDF Document Generator Service.

Generates a formatted, clean, professional PDF cover letter using ReportLab.
"""

import io
from datetime import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable


class CoverLetterGenerator:
    """Builds clean, professional PDF cover letters."""

    COLOR_PRIMARY = colors.HexColor("#1A2B4C")
    COLOR_SECONDARY = colors.HexColor("#4F46E5")
    COLOR_TEXT = colors.HexColor("#1E293B")
    COLOR_MUTED = colors.HexColor("#64748B")

    @classmethod
    def generate_pdf(
        cls,
        cover_letter_data: Dict[str, Any],
        resume_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> io.BytesIO:
        """Generates a styled PDF cover letter into an in-memory byte stream."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        style_name = ParagraphStyle(
            'ApplicantName',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=cls.COLOR_PRIMARY,
            alignment=0  # Left aligned
        )

        style_contact = ParagraphStyle(
            'ApplicantContact',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13,
            textColor=cls.COLOR_MUTED,
            alignment=0
        )

        style_date = ParagraphStyle(
            'LetterDate',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=13,
            textColor=cls.COLOR_TEXT
        )

        style_recipient = ParagraphStyle(
            'RecipientBlock',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=14,
            textColor=cls.COLOR_PRIMARY
        )

        style_body = ParagraphStyle(
            'LetterBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=15,
            textColor=cls.COLOR_TEXT,
            spaceAfter=10
        )

        style_signoff = ParagraphStyle(
            'Signoff',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10.5,
            leading=15,
            textColor=cls.COLOR_PRIMARY
        )

        story = []

        contact = resume_data.get("contact", {})
        candidate_name = contact.get("name") or "Applicant"
        email = contact.get("email") or "applicant@email.com"
        phone = contact.get("phone") or "(555) 019-2834"

        # 1. Applicant Header
        story.append(Paragraph(candidate_name, style_name))
        contact_line = f"{email}  •  {phone}"
        if contact.get("linkedin"):
            contact_line += f"  •  linkedin.com/in/{contact['linkedin']}"
        story.append(Paragraph(contact_line, style_contact))
        story.append(Spacer(1, 10))

        # Divider rule
        story.append(HRFlowable(width="100%", thickness=1, color=cls.COLOR_SECONDARY, spaceBefore=2, spaceAfter=15))

        # 2. Date
        current_date_str = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(current_date_str, style_date))
        story.append(Spacer(1, 12))

        # 3. Recipient Information
        company = cover_letter_data.get("company") or analysis_result.get("job_meta", {}).get("company", "Hiring Team")
        job_title = cover_letter_data.get("job_title") or analysis_result.get("job_meta", {}).get("title", "Target Role")
        recipient = cover_letter_data.get("recipient") or f"Hiring Manager / {company} Team"

        story.append(Paragraph(recipient, style_recipient))
        story.append(Paragraph(company, style_date))
        story.append(Spacer(1, 12))

        # 4. Subject line
        style_subject = ParagraphStyle(
            'SubjectLine',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10.5,
            leading=14,
            textColor=cls.COLOR_SECONDARY
        )
        story.append(Paragraph(f"RE: Application for {job_title} Position", style_subject))
        story.append(Spacer(1, 12))

        # 5. Letter Content Paragraphs
        raw_letter_text = cover_letter_data.get("letter_content", "")
        # Clean potential greetings and signature duplicate lines if formatting
        paragraphs = [p.strip() for p in raw_letter_text.split('\n\n') if p.strip()]

        for p_text in paragraphs:
            # Escape HTML characters for ReportLab XML parser safely
            safe_text = (
                p_text.replace('&', '&amp;')
                      .replace('<', '&lt;')
                      .replace('>', '&gt;')
            )
            story.append(Paragraph(safe_text, style_body))
            story.append(Spacer(1, 4))

        doc.build(story)
        buffer.seek(0)
        return buffer
