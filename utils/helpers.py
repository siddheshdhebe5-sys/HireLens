"""Helper utilities for ResumeAI application."""

import os
import re
from typing import Dict, Any

ALLOWED_EXTENSIONS = {'pdf', 'docx'}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has a permitted extension."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def sanitize_text(text: str) -> str:
    """Clean and normalize raw extracted text from resumes or job postings."""
    if not text:
        return ""
    # Normalize multiple whitespace and clean non-printable characters while preserving newlines
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def get_sample_candidate() -> Dict[str, Any]:
    """Returns sample candidate resume data for testing and demonstrations."""
    sample_text = """Alex Chen
Email: alex.chen@email.com | Phone: (555) 019-2834 | Location: Boston, MA
LinkedIn: linkedin.com/in/alexchen-demo | GitHub: github.com/alexchen-dev

OBJECTIVE / SUMMARY
Motivated Computer Science (Data Science) undergraduate with strong foundation in statistical programming, algorithm design, and exploratory data analysis. Passionate about leveraging data insights to solve real-world problems.

EDUCATION
Bachelor of Science in Computer Science (Specialization: Data Science)
State University | Expected Graduation: May 2026 | GPA: 3.82 / 4.00
Relevant Coursework: Data Structures, Database Systems, Applied Statistics, Machine Learning Fundamentals.

TECHNICAL SKILLS
- Programming Languages: Python, C, SQL
- Libraries & Tools: Pandas, NumPy, Scikit-learn, Git, GitHub, Jupyter Notebook
- Core Competencies: Data Science, Exploratory Data Analysis (EDA), Relational Databases, Problem Solving

ACADEMIC & PERSONAL PROJECTS
1. Student Performance Analysis
- Developed an exploratory data pipeline in Python using Pandas to analyze demographic and academic indicators across 1,000+ student records.
- Identified critical factors influencing exam scores with statistical correlation analysis and visualized findings using Matplotlib.
- Maintained structured codebase and version control on GitHub.

2. River Cleaning Boat (Autonomous IoT Prototype)
- Collaborated in a team of 4 to design an embedded prototype boat for surface debris collection in urban waterways.
- Programmed core navigation and sensor telemetry scripts in C.
- Integrated fail-safe logic ensuring 99% operational uptime during field trials.

EXPERIENCE / LEADERSHIP
Peer Tutor - Department of Computer Science
State University | Sep 2024 - Present
- Conducted weekly mentoring sessions in Python and Introduction to C programming for 35+ undergraduate students.
- Assisted students in debugging algorithms, understanding memory management, and writing clean, documented code.
"""
    return {
        "name": "Alex Chen",
        "email": "alex.chen@email.com",
        "phone": "(555) 019-2834",
        "raw_text": sample_text
    }


def get_sample_job_description() -> Dict[str, Any]:
    """Returns a sample Data Analyst Intern job posting for testing and demonstrations."""
    sample_text = """Position: Data Analyst Intern
Company: Apex Insights Analytics
Location: Hybrid / Boston, MA
Employment Type: Internship (Summer 2026)

About the Role:
Apex Insights is seeking a driven Data Analyst Intern to join our Analytics & Business Intelligence team. You will work alongside senior analysts to turn complex datasets into actionable business dashboards and strategic reports.

Key Responsibilities:
- Extract, clean, and validate data from multiple relational databases using SQL.
- Perform exploratory data analysis using Python and statistical techniques to uncover trends.
- Build and maintain interactive dashboards in Power BI and Excel for executive stakeholders.
- Collaborate with cross-functional teams to translate business questions into quantitative metrics and data visualizations.
- Document data definitions, analytical methodologies, and maintain project repositories on GitHub.

Qualifications & Requirements:
- Enrolled in Bachelor's or Master's degree in Computer Science, Data Science, Statistics, Mathematics, or related field.
- Proficiency in Python and SQL for data manipulation and querying.
- Hands-on experience with Microsoft Excel (VLOOKUP, Pivot Tables) and Power BI.
- Strong grounding in Data Analysis, Statistics, and Data Visualization principles.
- Experience with Git and version control practices.
- Excellent written and verbal communication skills with ability to explain data findings clearly.
"""
    return {
        "title": "Data Analyst Intern",
        "company": "Apex Insights Analytics",
        "raw_text": sample_text
    }
