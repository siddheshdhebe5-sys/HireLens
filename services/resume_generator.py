"""Resume DOCX Document Generator Service.

Generates a formatted, ATS-compliant, professional Microsoft Word (.docx) resume
incorporating the complete tailored content: summary, skills, education, experience,
internships, projects, certifications, and achievements.
"""

import io
from typing import Dict, Any, List
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


class ResumeGenerator:
    """Builds clean, professional, ATS-compatible .docx resumes."""

    # Editorial Career-Tech palette matching HireLens brand
    COLOR_PRIMARY = RGBColor(66, 107, 82)    # #426B52 – Forest green
    COLOR_TEXT = RGBColor(32, 37, 31)        # #20251F – Deep ink
    COLOR_MUTED = RGBColor(107, 112, 105)    # #6B7069 – Secondary text

    @classmethod
    def generate_docx(
        cls,
        resume_data: Dict[str, Any],
        tailored_data: Dict[str, Any],
        analysis_result: Dict[str, Any]
    ) -> io.BytesIO:
        """Creates a complete tailored resume DOCX file in an in-memory byte stream."""
        doc = docx.Document()

        # Standard professional margins (0.75 inch)
        for section in doc.sections:
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)
            section.left_margin = Inches(0.8)
            section.right_margin = Inches(0.8)

        contact = resume_data.get("contact", {})
        candidate_name = contact.get("name") or "Candidate Name"
        sections_data = resume_data.get("sections", {})

        # ==== 1. HEADER: Name ====
        p_name = doc.add_paragraph()
        p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_name.paragraph_format.space_before = Pt(0)
        p_name.paragraph_format.space_after = Pt(2)
        run_name = p_name.add_run(candidate_name.upper())
        run_name.font.name = "Calibri"
        run_name.font.size = Pt(18)
        run_name.font.bold = True
        run_name.font.color.rgb = cls.COLOR_TEXT

        # ==== 2. Contact Line ====
        contact_parts = []
        if contact.get("email"):
            contact_parts.append(contact["email"])
        if contact.get("phone"):
            contact_parts.append(contact["phone"])
        if contact.get("linkedin"):
            val = contact["linkedin"]
            if "linkedin.com" not in val:
                val = f"linkedin.com/in/{val}"
            contact_parts.append(val)
        if contact.get("github"):
            val = contact["github"]
            if "github.com" not in val:
                val = f"github.com/{val}"
            contact_parts.append(val)

        if contact_parts:
            p_contact = doc.add_paragraph()
            p_contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_contact.paragraph_format.space_before = Pt(0)
            p_contact.paragraph_format.space_after = Pt(10)
            run_contact = p_contact.add_run("  |  ".join(contact_parts))
            run_contact.font.name = "Calibri"
            run_contact.font.size = Pt(9.5)
            run_contact.font.color.rgb = cls.COLOR_MUTED

        # ==== 3. Professional Summary ====
        summary = (
            tailored_data.get("professional_summary")
            or tailored_data.get("tailored_summary")
            or sections_data.get("summary", "")
        )
        if summary and summary.strip():
            cls._add_section_heading(doc, "PROFESSIONAL SUMMARY")
            p_sum = doc.add_paragraph()
            p_sum.paragraph_format.space_before = Pt(2)
            p_sum.paragraph_format.space_after = Pt(6)
            p_sum.paragraph_format.line_spacing = 1.15
            run_sum = p_sum.add_run(summary.strip())
            run_sum.font.name = "Calibri"
            run_sum.font.size = Pt(10)
            run_sum.font.color.rgb = cls.COLOR_TEXT

        # ==== 4. Technical Skills ====
        skills_dict = tailored_data.get("skills", {})
        technical_skills = skills_dict.get("technical", [])
        soft_skills = skills_dict.get("soft", [])

        # Fall back to analysis result if tailored_data lacks skills
        if not technical_skills:
            matched = [s["name"] for s in analysis_result.get("skills", {}).get("matched", [])]
            extra = [s["name"] for s in analysis_result.get("skills", {}).get("extra", [])]
            technical_skills = list(dict.fromkeys(matched + extra))[:12]

        # Also pull from skill_emphasis if present
        if not technical_skills:
            for group in tailored_data.get("skill_emphasis", []):
                technical_skills.extend(group.get("skills", []))

        if technical_skills or soft_skills:
            cls._add_section_heading(doc, "TECHNICAL SKILLS")
            if technical_skills:
                p_ts = doc.add_paragraph()
                p_ts.paragraph_format.space_before = Pt(2)
                p_ts.paragraph_format.space_after = Pt(3)
                r_lbl = p_ts.add_run("Technical: ")
                r_lbl.font.bold = True
                r_lbl.font.name = "Calibri"
                r_lbl.font.size = Pt(10)
                r_val = p_ts.add_run(", ".join(technical_skills))
                r_val.font.name = "Calibri"
                r_val.font.size = Pt(10)
                r_val.font.color.rgb = cls.COLOR_TEXT
            if soft_skills:
                p_ss = doc.add_paragraph()
                p_ss.paragraph_format.space_before = Pt(0)
                p_ss.paragraph_format.space_after = Pt(6)
                r_lbl2 = p_ss.add_run("Professional: ")
                r_lbl2.font.bold = True
                r_lbl2.font.name = "Calibri"
                r_lbl2.font.size = Pt(10)
                r_val2 = p_ss.add_run(", ".join(soft_skills))
                r_val2.font.name = "Calibri"
                r_val2.font.size = Pt(10)
                r_val2.font.color.rgb = cls.COLOR_TEXT

        # ==== 5. Education ====
        education_entries = tailored_data.get("education", [])
        if not education_entries:
            # Parse from raw sections
            edu_raw = sections_data.get("education", "")
            if edu_raw:
                education_entries = [{"degree": edu_raw.strip(), "institution": "", "year": "", "gpa": "", "coursework": ""}]

        if education_entries:
            cls._add_section_heading(doc, "EDUCATION")
            for edu in education_entries:
                degree = edu.get("degree", "")
                institution = edu.get("institution", "")
                year = edu.get("year", "")
                gpa = edu.get("gpa", "")
                coursework = edu.get("coursework", "")

                if degree:
                    p_deg = doc.add_paragraph()
                    p_deg.paragraph_format.space_before = Pt(2)
                    p_deg.paragraph_format.space_after = Pt(1)
                    # Degree bold on left, year on right
                    r_deg = p_deg.add_run(degree)
                    r_deg.font.bold = True
                    r_deg.font.name = "Calibri"
                    r_deg.font.size = Pt(10.5)
                    r_deg.font.color.rgb = cls.COLOR_TEXT

                if institution or year:
                    p_inst = doc.add_paragraph()
                    p_inst.paragraph_format.space_before = Pt(0)
                    p_inst.paragraph_format.space_after = Pt(1)
                    inst_text = institution
                    if year:
                        inst_text = f"{institution}  |  {year}" if institution else year
                    r_inst = p_inst.add_run(inst_text)
                    r_inst.font.name = "Calibri"
                    r_inst.font.size = Pt(10)
                    r_inst.font.italic = True
                    r_inst.font.color.rgb = cls.COLOR_MUTED

                if gpa:
                    p_gpa = doc.add_paragraph()
                    p_gpa.paragraph_format.space_before = Pt(0)
                    p_gpa.paragraph_format.space_after = Pt(1)
                    r_gpa = p_gpa.add_run(f"GPA: {gpa}" if "gpa" not in gpa.lower() else gpa)
                    r_gpa.font.name = "Calibri"
                    r_gpa.font.size = Pt(10)
                    r_gpa.font.color.rgb = cls.COLOR_TEXT

                if coursework:
                    p_cw = doc.add_paragraph()
                    p_cw.paragraph_format.space_before = Pt(0)
                    p_cw.paragraph_format.space_after = Pt(4)
                    r_cw_lbl = p_cw.add_run("Relevant Coursework: ")
                    r_cw_lbl.font.bold = True
                    r_cw_lbl.font.name = "Calibri"
                    r_cw_lbl.font.size = Pt(10)
                    r_cw_val = p_cw.add_run(coursework)
                    r_cw_val.font.name = "Calibri"
                    r_cw_val.font.size = Pt(10)
                    r_cw_val.font.color.rgb = cls.COLOR_TEXT

        # ==== 6. Work Experience ====
        experience_entries = tailored_data.get("experience", [])
        # Filter out entries that look like internships (they'll be in own section)
        real_exp = [e for e in experience_entries
                    if "intern" not in (e.get("title") or "").lower()]
        if real_exp:
            cls._add_section_heading(doc, "WORK EXPERIENCE")
            for exp in real_exp:
                cls._add_role_entry(doc, exp)

        # ==== 7. Internships ====
        internship_entries = tailored_data.get("internships", [])
        # Also check experience for intern roles
        intern_from_exp = [e for e in experience_entries
                           if "intern" in (e.get("title") or "").lower()]
        all_internships = internship_entries + [e for e in intern_from_exp if e not in internship_entries]
        if all_internships:
            cls._add_section_heading(doc, "INTERNSHIPS")
            for intern in all_internships:
                cls._add_role_entry(doc, intern)

        # ==== 8. Projects ====
        project_entries = tailored_data.get("projects", [])
        # Also fall back to bullet_improvements from older format
        if not project_entries:
            bullet_improvements = tailored_data.get("bullet_improvements", [])
            if bullet_improvements:
                project_entries = [
                    {"name": b.get("original_context", "Project"), "bullets": [b.get("tailored_bullet", "")]}
                    for b in bullet_improvements
                ]
        # Fall back to raw section text
        if not project_entries:
            proj_raw = sections_data.get("projects", "")
            if proj_raw:
                project_entries = [{"name": "Projects", "technologies": "", "bullets": [
                    l.strip().lstrip("-•*– ")
                    for l in proj_raw.split("\n")
                    if l.strip() and not l.strip().isdigit()
                ]}]

        if project_entries:
            cls._add_section_heading(doc, "PROJECTS")
            for proj in project_entries:
                name = proj.get("name", "")
                tech = proj.get("technologies", "")
                bullets = proj.get("bullets", [])

                if name:
                    p_proj_title = doc.add_paragraph()
                    p_proj_title.paragraph_format.space_before = Pt(4)
                    p_proj_title.paragraph_format.space_after = Pt(1)
                    r_pn = p_proj_title.add_run(name)
                    r_pn.font.bold = True
                    r_pn.font.name = "Calibri"
                    r_pn.font.size = Pt(10.5)
                    r_pn.font.color.rgb = cls.COLOR_TEXT
                    if tech:
                        r_tech = p_proj_title.add_run(f"  |  {tech}")
                        r_tech.font.name = "Calibri"
                        r_tech.font.size = Pt(10)
                        r_tech.font.italic = True
                        r_tech.font.color.rgb = cls.COLOR_MUTED

                for bullet in bullets:
                    if bullet and bullet.strip():
                        p_b = doc.add_paragraph(style="List Bullet")
                        p_b.paragraph_format.space_before = Pt(0)
                        p_b.paragraph_format.space_after = Pt(2)
                        p_b.paragraph_format.line_spacing = 1.1
                        run_b = p_b.add_run(bullet.strip())
                        run_b.font.name = "Calibri"
                        run_b.font.size = Pt(10)
                        run_b.font.color.rgb = cls.COLOR_TEXT

        # ==== 9. Certifications ====
        cert_entries = tailored_data.get("certifications", [])
        if not cert_entries:
            cert_raw = sections_data.get("certifications", "")
            if cert_raw:
                cert_entries = [l.strip() for l in cert_raw.split("\n") if l.strip()]

        if cert_entries:
            cls._add_section_heading(doc, "CERTIFICATIONS")
            for cert in cert_entries:
                p_cert = doc.add_paragraph(style="List Bullet")
                p_cert.paragraph_format.space_before = Pt(0)
                p_cert.paragraph_format.space_after = Pt(2)
                r_cert = p_cert.add_run(cert.strip().lstrip("-•*– "))
                r_cert.font.name = "Calibri"
                r_cert.font.size = Pt(10)
                r_cert.font.color.rgb = cls.COLOR_TEXT

        # ==== 10. Achievements / Awards ====
        achievement_entries = tailored_data.get("achievements", [])
        if not achievement_entries:
            ach_raw = sections_data.get("achievements", "")
            if ach_raw:
                achievement_entries = [l.strip() for l in ach_raw.split("\n") if l.strip()]

        if achievement_entries:
            cls._add_section_heading(doc, "ACHIEVEMENTS & AWARDS")
            for ach in achievement_entries:
                p_ach = doc.add_paragraph(style="List Bullet")
                p_ach.paragraph_format.space_before = Pt(0)
                p_ach.paragraph_format.space_after = Pt(2)
                r_ach = p_ach.add_run(ach.strip().lstrip("-•*– "))
                r_ach.font.name = "Calibri"
                r_ach.font.size = Pt(10)
                r_ach.font.color.rgb = cls.COLOR_TEXT

        # Save to memory stream
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        return output

    @classmethod
    def _add_role_entry(cls, doc: docx.Document, entry: Dict[str, Any]) -> None:
        """Add a work experience or internship entry with title, company, duration and bullets."""
        title = entry.get("title", "")
        company = entry.get("company", "")
        duration = entry.get("duration", "")
        bullets = entry.get("bullets", [])

        # Title + Company + Duration on one or two lines
        if title or company:
            p_title = doc.add_paragraph()
            p_title.paragraph_format.space_before = Pt(4)
            p_title.paragraph_format.space_after = Pt(1)

            if title:
                r_title = p_title.add_run(title)
                r_title.font.bold = True
                r_title.font.name = "Calibri"
                r_title.font.size = Pt(10.5)
                r_title.font.color.rgb = cls.COLOR_TEXT

            if company:
                r_sep = p_title.add_run(" — ")
                r_sep.font.name = "Calibri"
                r_sep.font.size = Pt(10)
                r_sep.font.color.rgb = cls.COLOR_MUTED
                r_comp = p_title.add_run(company)
                r_comp.font.name = "Calibri"
                r_comp.font.size = Pt(10)
                r_comp.font.color.rgb = cls.COLOR_TEXT

        if duration:
            p_dur = doc.add_paragraph()
            p_dur.paragraph_format.space_before = Pt(0)
            p_dur.paragraph_format.space_after = Pt(1)
            r_dur = p_dur.add_run(duration)
            r_dur.font.name = "Calibri"
            r_dur.font.size = Pt(10)
            r_dur.font.italic = True
            r_dur.font.color.rgb = cls.COLOR_MUTED

        for bullet in bullets:
            if bullet and bullet.strip():
                p_b = doc.add_paragraph(style="List Bullet")
                p_b.paragraph_format.space_before = Pt(0)
                p_b.paragraph_format.space_after = Pt(2)
                p_b.paragraph_format.line_spacing = 1.1
                run_b = p_b.add_run(bullet.strip())
                run_b.font.name = "Calibri"
                run_b.font.size = Pt(10)
                run_b.font.color.rgb = cls.COLOR_TEXT

    @classmethod
    def _add_section_heading(cls, doc: docx.Document, title: str) -> None:
        """Append a clean styled section heading with a horizontal rule below it."""
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        run = p.add_run(title)
        run.font.name = "Calibri"
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = cls.COLOR_PRIMARY

        # Add bottom border (horizontal rule) to the heading paragraph
        try:
            pPr = p._p.get_or_add_pPr()
            pBdr = OxmlElement("w:pBdr")
            bottom = OxmlElement("w:bottom")
            bottom.set(qn("w:val"), "single")
            bottom.set(qn("w:sz"), "6")
            bottom.set(qn("w:space"), "1")
            bottom.set(qn("w:color"), "426B52")
            pBdr.append(bottom)
            pPr.append(pBdr)
        except Exception:
            pass  # Gracefully skip border if XML manipulation fails
