"""AI Tailoring and Cover Letter Generation Service.

Integrates with Google's official Gemini API (google-genai SDK) with strict
ethical prompts (NO fabrication). Seamlessly falls back to high-quality deterministic
generation in Demo Mode when no API key is provided.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
from utils.helpers import sanitize_text


class AIService:
    """Provides AI-powered resume tailoring and cover letter generation."""

    MODEL_NAME = "gemini-2.5-flash"

    @classmethod
    def get_api_key(cls) -> Optional[str]:
        """Reads GEMINI_API_KEY from environment."""
        key = os.getenv("GEMINI_API_KEY", "").strip()
        if not key or key == "your_gemini_api_key_here":
            return None
        return key

    @classmethod
    def is_ai_available(cls) -> bool:
        """Checks if a valid Gemini API key is configured."""
        return cls.get_api_key() is not None

    @classmethod
    def generate_tailored_resume(
        cls,
        resume_data: Dict[str, Any],
        job_text: str,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generates a complete tailored resume with all applicable sections."""
        api_key = cls.get_api_key()
        if not api_key:
            return cls._generate_deterministic_resume_tailoring(resume_data, job_text, analysis_result)

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            candidate_name = resume_data.get("contact", {}).get("name", "Candidate")
            matched_skills = [s["name"] for s in analysis_result.get("skills", {}).get("matched", [])]
            missing_skills = [s["name"] for s in analysis_result.get("skills", {}).get("missing", [])]
            job_title = analysis_result.get("job_meta", {}).get("title", "Target Role")
            company = analysis_result.get("job_meta", {}).get("company", "Company")
            raw_text = resume_data.get("raw_text", "")
            sections = resume_data.get("sections", {})

            prompt = f"""
You are an expert AI Career Coach and Resume Writer.

CRITICAL ETHICAL RULES (NON-NEGOTIABLE):
1. NEVER invent or fabricate work experience, degrees, certifications, companies, projects, or metrics.
2. Do NOT claim the candidate has skills they did not mention in their resume.
3. ONLY rewrite, improve, and professionally frame what genuinely exists in the resume.
4. If a section (e.g. certifications, internships) is not present in the resume, omit it — do not fabricate.
5. Never add placeholder text or generic filler content.
6. Preserve all real dates, company names, institution names, and contact details exactly.

CANDIDATE RESUME (full text):
{raw_text}

TARGET JOB DESCRIPTION:
{job_text}

TARGET ROLE: {job_title} at {company}
MATCHED SKILLS FOUND: {', '.join(matched_skills[:10]) if matched_skills else 'see resume'}
SKILLS MISSING FROM RESUME: {', '.join(missing_skills[:5]) if missing_skills else 'none identified'}

TASK: Generate a complete, professionally structured tailored resume as a JSON object.
- Include ONLY sections where the candidate has real content.
- Rewrite descriptions into clear, action-oriented, concise professional language.
- Emphasize skills and experiences relevant to {job_title}.
- The professional_summary must be 3-4 specific sentences tied to this exact role and company.
- Each bullet point should start with a strong action verb and convey outcome/impact where the original supports it.
- Do NOT add fabricated metrics if the original resume doesn't provide them.

Respond ONLY with a valid JSON object in this exact format:
{{
  "professional_summary": "3-4 sentence tailored summary for {job_title} at {company}.",
  "skills": {{
    "technical": ["skill1", "skill2"],
    "soft": ["skill3", "skill4"]
  }},
  "education": [
    {{
      "degree": "Bachelor of ...",
      "institution": "University Name",
      "year": "Expected May 2026",
      "gpa": "3.82/4.00",
      "coursework": "Data Structures, Machine Learning, ..."
    }}
  ],
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "duration": "Sep 2024 – Present",
      "bullets": [
        "Action-oriented bullet point 1",
        "Action-oriented bullet point 2"
      ]
    }}
  ],
  "internships": [
    {{
      "title": "Intern Role",
      "company": "Company",
      "duration": "Jun 2024 – Aug 2024",
      "bullets": ["bullet 1"]
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "technologies": "Python, Pandas",
      "bullets": [
        "Action-oriented description bullet 1",
        "Action-oriented description bullet 2"
      ]
    }}
  ],
  "certifications": ["Certification Name – Issuer (Year)"],
  "achievements": ["Achievement or award description"],
  "missing_skills_advisory": [
    "SkillName: In job description but not in your resume. Add only if you genuinely have this experience."
  ]
}}

IMPORTANT: Only include keys for sections that have real content from the resume.
Return empty arrays [] for sections with no content — do NOT omit the keys but do NOT fabricate content.
"""

            response = client.models.generate_content(
                model=cls.MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.15
                )
            )

            response_json = json.loads(response.text)
            response_json["is_demo_mode"] = False
            response_json["model_used"] = cls.MODEL_NAME
            # Build backward-compatible fields for the preview template
            response_json["tailored_summary"] = response_json.get("professional_summary", "")
            response_json["skill_emphasis"] = cls._build_skill_emphasis(response_json.get("skills", {}))
            response_json["bullet_improvements"] = cls._build_bullet_improvements(
                response_json.get("experience", []) + response_json.get("projects", [])
            )
            response_json["formatting_tips"] = [
                "Position your Technical Skills section immediately after your Professional Summary.",
                "Start every bullet point with a strong past-tense action verb.",
                "Keep dates right-aligned and consistent throughout.",
            ]
            return response_json

        except Exception as e:
            fallback_result = cls._generate_deterministic_resume_tailoring(resume_data, job_text, analysis_result)
            fallback_result["warning"] = f"Gemini API call failed ({str(e)}). Running in Demo / Fallback Mode."
            return fallback_result

    @classmethod
    def _build_skill_emphasis(cls, skills_dict: Dict) -> List[Dict]:
        """Convert the skills dict into the legacy skill_emphasis format for the template."""
        result = []
        if skills_dict.get("technical"):
            result.append({"category": "Technical Skills", "skills": skills_dict["technical"]})
        if skills_dict.get("soft"):
            result.append({"category": "Professional Skills", "skills": skills_dict["soft"]})
        return result

    @classmethod
    def _build_bullet_improvements(cls, entries: List[Dict]) -> List[Dict]:
        """Build backward-compatible bullet_improvements list from experience/project entries."""
        result = []
        for entry in entries:
            bullets = entry.get("bullets", [])
            if bullets:
                name = entry.get("name") or entry.get("title", "Experience")
                result.append({
                    "original_context": name,
                    "tailored_bullet": bullets[0],
                    "rationale": "Reframed with action verbs and relevant outcomes."
                })
        return result

    @classmethod
    def generate_cover_letter(
        cls,
        resume_data: Dict[str, Any],
        job_text: str,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generates a personalized, professional cover letter matching genuine experience to the role."""
        api_key = cls.get_api_key()
        if not api_key:
            return cls._generate_deterministic_cover_letter(resume_data, job_text, analysis_result)

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            candidate_name = resume_data.get("contact", {}).get("name", "Applicant")
            job_title = analysis_result.get("job_meta", {}).get("title", "Target Role")
            company = analysis_result.get("job_meta", {}).get("company", "Hiring Team")
            matched_skills = [s["name"] for s in analysis_result.get("skills", {}).get("matched", [])]

            prompt = f"""
You are an expert career consultant drafting a tailored, authentic cover letter.

ETHICAL RULES:
1. Reference ONLY real projects, education, and skills present in the resume.
2. NEVER fabricate past employers, years of experience, or fake metrics.
3. Keep the tone professional, enthusiastic, concise, and student/graduate friendly.

CANDIDATE INFORMATION:
Name: {candidate_name}
Resume Text:
{resume_data.get('raw_text', '')}

JOB INFORMATION:
Title: {job_title}
Company: {company}
Job Text:
{job_text}

MATCHED KEY SKILLS: {', '.join(matched_skills[:8])}

Generate a concise 4-paragraph cover letter formatted as standard markdown/text:
- Paragraph 1: Purpose of application, target role ({job_title}), company interest ({company}).
- Paragraph 2: Highlighting genuine technical skills and relevant projects from the resume.
- Paragraph 3: Connecting problem-solving skills and adaptability to the company's goals.
- Paragraph 4: Enthusiastic closing and call for conversation.

Return ONLY a JSON object:
{{
  "recipient": "Hiring Manager / {company} Recruitment Team",
  "job_title": "{job_title}",
  "company": "{company}",
  "letter_content": "Full text of the cover letter with proper paragraph breaks."
}}
"""

            response = client.models.generate_content(
                model=cls.MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3
                )
            )

            response_json = json.loads(response.text)
            response_json["is_demo_mode"] = False
            response_json["model_used"] = cls.MODEL_NAME
            return response_json

        except Exception as e:
            fallback_result = cls._generate_deterministic_cover_letter(resume_data, job_text, analysis_result)
            fallback_result["warning"] = f"Gemini API call failed ({str(e)}). Running in Demo / Fallback Mode."
            return fallback_result

    @classmethod
    def _generate_deterministic_resume_tailoring(
        cls,
        resume_data: Dict[str, Any],
        job_text: str,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """High-quality deterministic fallback — builds a complete resume from parsed candidate data."""
        contact = resume_data.get("contact", {})
        candidate_name = contact.get("name", "Candidate")
        matched_skills = [s["name"] for s in analysis_result.get("skills", {}).get("matched", [])]
        missing_skills = [s["name"] for s in analysis_result.get("skills", {}).get("missing", [])]
        extra_skills = [s["name"] for s in analysis_result.get("skills", {}).get("extra", [])]
        job_meta = analysis_result.get("job_meta", {})
        job_title = job_meta.get("title", "Target Role")
        company = job_meta.get("company", "the company")
        sections = resume_data.get("sections", {})
        raw_text = resume_data.get("raw_text", "")

        matched_str = ", ".join(matched_skills[:4]) if matched_skills else "software and analytical tools"

        # ---- Professional Summary ----
        summary = (
            f"Results-oriented candidate with demonstrated proficiency in {matched_str}. "
            f"Committed to producing high-quality, well-documented solutions through structured analytical thinking and collaborative teamwork. "
            f"Eager to apply technical expertise and a strong foundation in {matched_str} "
            f"to deliver measurable impact as a {job_title} at {company}."
        )

        # ---- Skills ----
        all_technical = list(dict.fromkeys(matched_skills + extra_skills))
        technical_skills = all_technical[:12] if all_technical else ["Python", "SQL", "Data Analysis", "Problem Solving"]
        soft_skills = ["Communication", "Teamwork", "Analytical Thinking", "Attention to Detail", "Time Management"]

        # ---- Education (parsed) ----
        education_entries = []
        edu_raw = sections.get("education", "")
        if edu_raw:
            edu_lines = [l.strip() for l in edu_raw.split("\n") if l.strip()]
            if edu_lines:
                # Heuristic: first line is typically degree + institution
                entry = {"degree": edu_lines[0], "institution": "", "year": "", "gpa": "", "coursework": ""}
                for line in edu_lines[1:]:
                    low = line.lower()
                    if "gpa" in low or "cgpa" in low:
                        entry["gpa"] = line
                    elif "course" in low or "relevant" in low:
                        entry["coursework"] = line.replace("Relevant Coursework:", "").replace("Coursework:", "").strip()
                    elif not entry["institution"]:
                        entry["institution"] = line
                    elif not entry["year"] and any(c.isdigit() for c in line):
                        entry["year"] = line
                education_entries.append(entry)

        # ---- Experience ----
        experience_entries = []
        exp_raw = sections.get("experience", "")
        if exp_raw:
            experience_entries = cls._parse_experience_section(exp_raw, job_title)

        # ---- Internships ----
        internship_entries = []
        # Parse from raw text: look for 'intern' occurrences not already in experience
        intern_raw = cls._extract_internships_from_text(raw_text, sections)
        if intern_raw:
            internship_entries = intern_raw

        # ---- Projects ----
        project_entries = []
        proj_raw = sections.get("projects", "")
        if proj_raw:
            project_entries = cls._parse_projects_section(proj_raw, matched_skills)

        # ---- Certifications ----
        cert_entries = []
        cert_raw = sections.get("certifications", "")
        if cert_raw:
            cert_entries = [l.strip() for l in cert_raw.split("\n") if l.strip() and len(l.strip()) > 3]

        # ---- Achievements ----
        achievement_entries = []
        ach_raw = sections.get("achievements", "")
        if ach_raw:
            achievement_entries = [l.strip() for l in ach_raw.split("\n") if l.strip() and len(l.strip()) > 3]

        # ---- Bullet improvements (for template backward compat) ----
        bullet_improvements = []
        for proj in project_entries[:3]:
            if proj.get("bullets"):
                bullet_improvements.append({
                    "original_context": proj.get("name", "Project"),
                    "tailored_bullet": proj["bullets"][0],
                    "rationale": f"Action-oriented framing aligned with {job_title} requirements."
                })
        for exp in experience_entries[:2]:
            if exp.get("bullets"):
                bullet_improvements.append({
                    "original_context": f"{exp.get('title', 'Role')} at {exp.get('company', '')}",
                    "tailored_bullet": exp["bullets"][0],
                    "rationale": f"Highlights relevant outcomes for {job_title} role."
                })

        if not bullet_improvements:
            bullet_improvements.append({
                "original_context": "General technical work",
                "tailored_bullet": (
                    f"Applied {matched_str} to design, test, and document modular solutions, "
                    f"ensuring accurate execution and adherence to version control best practices."
                ),
                "rationale": "Reframes general technical work with action verbs aligned with the job posting."
            })

        # ---- Missing skills advisory ----
        missing_advisory = []
        for s in missing_skills[:4]:
            missing_advisory.append(
                f"{s}: Appears in the job description but not detected in your resume. "
                f"Add it ONLY if you genuinely have coursework or practical experience with this tool."
            )

        return {
            "professional_summary": summary,
            "tailored_summary": summary,  # backward compat
            "skills": {
                "technical": technical_skills,
                "soft": soft_skills
            },
            "education": education_entries,
            "experience": experience_entries,
            "internships": internship_entries,
            "projects": project_entries,
            "certifications": cert_entries,
            "achievements": achievement_entries,
            "skill_emphasis": [
                {"category": "Technical Skills", "skills": technical_skills[:6]},
                {"category": "Professional Skills", "skills": soft_skills}
            ],
            "bullet_improvements": bullet_improvements,
            "missing_skills_advisory": missing_advisory,
            "formatting_tips": [
                "Position your Technical Skills section right below the Professional Summary for ATS.",
                "Start every bullet point with a strong past-tense action verb (e.g., Engineered, Analyzed, Built).",
                "Align dates consistently to the right margin throughout the document.",
            ],
            "is_demo_mode": True,
            "model_used": "Deterministic Rule-Based Engine (Demo Mode)"
        }

    @classmethod
    def _parse_experience_section(cls, exp_raw: str, job_title: str) -> List[Dict]:
        """Parse raw experience section text into structured entries."""
        entries = []
        lines = [l.strip() for l in exp_raw.split("\n") if l.strip()]
        if not lines:
            return entries

        current_entry = None
        for line in lines:
            is_bullet = line.startswith(("-", "•", "*", "–")) or (len(line) > 2 and line[0].isdigit() and line[1] == ".")
            # Heuristic: non-bullet lines that look like titles
            if not is_bullet and len(line) < 80:
                if current_entry and (current_entry.get("title") or current_entry.get("company")):
                    entries.append(current_entry)
                current_entry = {"title": line, "company": "", "duration": "", "bullets": []}
            elif not is_bullet and current_entry:
                # Could be company name or duration
                if any(c.isdigit() for c in line) and ("-" in line or "–" in line or "present" in line.lower()):
                    current_entry["duration"] = line
                elif not current_entry["company"]:
                    current_entry["company"] = line
            elif is_bullet and current_entry is not None:
                clean = line.lstrip("-•*– ").strip()
                if clean:
                    current_entry["bullets"].append(clean)
            elif is_bullet:
                # No current entry context yet — create a generic one
                current_entry = {"title": "Role", "company": "", "duration": "", "bullets": []}
                clean = line.lstrip("-•*– ").strip()
                if clean:
                    current_entry["bullets"].append(clean)

        if current_entry and (current_entry.get("title") or current_entry.get("bullets")):
            entries.append(current_entry)

        return entries

    @classmethod
    def _parse_projects_section(cls, proj_raw: str, matched_skills: List[str]) -> List[Dict]:
        """Parse raw projects section text into structured entries."""
        entries = []
        lines = [l.strip() for l in proj_raw.split("\n") if l.strip()]
        if not lines:
            return entries

        current = None
        for line in lines:
            is_bullet = line.startswith(("-", "•", "*", "–"))
            numbered = len(line) > 2 and line[0].isdigit() and line[1] in (".", ")")

            if numbered or (not is_bullet and len(line) < 80 and not any(line.lower().startswith(x) for x in ("the ", "a ", "an ", "this "))):
                if current and (current.get("name") or current.get("bullets")):
                    entries.append(current)
                name = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
                current = {"name": name, "technologies": "", "bullets": []}
            elif is_bullet and current is not None:
                clean = line.lstrip("-•*– ").strip()
                if clean:
                    current["bullets"].append(clean)
            elif is_bullet:
                current = {"name": "Project", "technologies": "", "bullets": []}
                clean = line.lstrip("-•*– ").strip()
                if clean:
                    current["bullets"].append(clean)
            elif current is not None:
                # Could be a description line or technology list
                if not current["technologies"] and any(skill.lower() in line.lower() for skill in matched_skills):
                    current["technologies"] = line
                elif current.get("bullets") is not None:
                    current["bullets"].append(line)

        if current and (current.get("name") or current.get("bullets")):
            entries.append(current)

        return entries

    @classmethod
    def _extract_internships_from_text(cls, raw_text: str, sections: Dict) -> List[Dict]:
        """Extract internship entries from raw text if not in dedicated section."""
        internships = []
        # Look for intern keyword in experience section or other text
        exp_raw = sections.get("experience", "")
        all_text = exp_raw + "\n" + raw_text

        lines = all_text.split("\n")
        current = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            is_intern = "intern" in line.lower() and len(line) < 100
            is_bullet = line.startswith(("-", "•", "*", "–"))

            if is_intern and not is_bullet:
                if current:
                    internships.append(current)
                current = {"title": line, "company": "", "duration": "", "bullets": []}
            elif current and is_bullet:
                clean = line.lstrip("-•*– ").strip()
                if clean:
                    current["bullets"].append(clean)
            elif current and not is_bullet:
                if any(c.isdigit() for c in line) and ("-" in line or "–" in line or "present" in line.lower()):
                    current["duration"] = line
                elif not current["company"] and len(line) < 80:
                    current["company"] = line

        if current and (current.get("title") or current.get("bullets")):
            internships.append(current)

        return internships

    @classmethod
    def _generate_deterministic_cover_letter(
        cls,
        resume_data: Dict[str, Any],
        job_text: str,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """High-quality deterministic fallback cover letter generator based on candidate profile."""
        contact = resume_data.get("contact", {})
        candidate_name = contact.get("name", "Applicant")
        matched_skills = [s["name"] for s in analysis_result.get("skills", {}).get("matched", [])]
        job_meta = analysis_result.get("job_meta", {})
        job_title = job_meta.get("title", "Data Analyst Intern")
        company = job_meta.get("company", "Apex Insights Analytics")
        sections = resume_data.get("sections", {})

        skills_str = ", ".join(matched_skills[:4]) if matched_skills else "Python, SQL, and data analysis"
        proj_summary = ""
        proj_raw = sections.get("projects", "")
        if proj_raw:
            proj_lines = [l.strip().lstrip("-•*– ") for l in proj_raw.split("\n") if l.strip()]
            if proj_lines:
                proj_summary = proj_lines[0][:120]

        edu_raw = sections.get("education", "")
        edu_summary = ""
        if edu_raw:
            edu_lines = [l.strip() for l in edu_raw.split("\n") if l.strip()]
            if edu_lines:
                edu_summary = edu_lines[0]

        letter_text = f"""Dear Hiring Team at {company},

I am writing to express my enthusiastic interest in the {job_title} position at {company}. With a strong foundation in {edu_summary or 'Computer Science and Data Science'} and hands-on project experience in {skills_str}, I am excited about the opportunity to contribute meaningfully to your team's goals.

{f'In my academic and project work, I have applied {skills_str} to real-world problems. For example: {proj_summary}.' if proj_summary else f'I have developed proficiency in {skills_str} through rigorous coursework and independent project work, building a clear understanding of how to apply technical skills to practical, real-world challenges.'}

What particularly attracts me to {company} is the opportunity to work in an environment that values data-driven decision-making and analytical rigor. My experience with {skills_str}, combined with strong attention to detail and collaborative communication skills, positions me to integrate quickly and deliver value from day one.

Thank you for your time and consideration. I would welcome the opportunity to discuss how my background and enthusiasm align with the goals of {company}. I look forward to the possibility of contributing to your team.

Sincerely,
{candidate_name}
Email: {contact.get('email', 'applicant@email.com')} | Phone: {contact.get('phone', '')}"""

        return {
            "recipient": f"Hiring Manager / {company} Recruitment Team",
            "job_title": job_title,
            "company": company,
            "letter_content": letter_text.strip(),
            "is_demo_mode": True,
            "model_used": "Deterministic Rule-Based Fallback Engine (Demo Mode)"
        }
