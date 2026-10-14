"""Unit tests for Skill Extraction and Resume Alignment Analyzer."""

import pytest
from services.skill_extractor import SkillExtractor
from services.resume_analyzer import ResumeAnalyzer
from services.resume_parser import ResumeParser
from utils.helpers import get_sample_candidate, get_sample_job_description


def test_skill_extractor_exact_matches():
    sample_text = "Experienced in Python, C, SQL, Pandas, Git, and Machine Learning. Also proficient in Power BI."
    skills = SkillExtractor.extract_skill_names(sample_text)

    assert "Python" in skills
    assert "C" in skills
    assert "SQL" in skills
    assert "Pandas" in skills
    assert "Git" in skills
    assert "Machine Learning" in skills
    assert "Power BI" in skills


def test_skill_extractor_word_boundary_safety():
    # Make sure words containing 'c' or 'r' don't trigger false positives
    text_without_skills = "The cat ran across the street and found a red car."
    skills = SkillExtractor.extract_skill_names(text_without_skills)
    assert "C" not in skills
    assert "R" not in skills
    assert "Go" not in skills


def test_resume_analyzer_sample_match():
    sample_cand = get_sample_candidate()
    sample_job = get_sample_job_description()

    resume_data = ResumeParser.parse_raw_text(sample_cand["raw_text"])
    analysis = ResumeAnalyzer.analyze(resume_data, sample_job["raw_text"])

    assert "score" in analysis
    assert 0 <= analysis["score"] <= 100

    # Alex Chen has Python, SQL, Pandas, GitHub, C
    # Job requires Python, SQL, Excel, Power BI, Data Analysis, Statistics, Data Visualization
    matched_names = {s["name"] for s in analysis["skills"]["matched"]}
    missing_names = {s["name"] for s in analysis["skills"]["missing"]}

    assert "Python" in matched_names
    assert "SQL" in matched_names
    assert "Power BI" in missing_names
    assert "Excel" in missing_names

    # Check breakdown components
    assert "breakdown" in analysis
    assert 0 <= analysis["breakdown"]["skill_score"] <= 100
    assert 0 <= analysis["breakdown"]["keyword_score"] <= 100
    assert 0 <= analysis["breakdown"]["semantic_score"] <= 100
    assert 0 <= analysis["breakdown"]["evidence_score"] <= 100

    # Check recommendations and ethical notice
    assert len(analysis["recommendations"]) > 0
    ethical_found = any("ONLY if you genuinely possess" in r["description"] for r in analysis["recommendations"])
    assert ethical_found


def test_analyzer_empty_inputs():
    with pytest.raises(ValueError):
        ResumeAnalyzer.analyze({"raw_text": ""}, "Some job description")
