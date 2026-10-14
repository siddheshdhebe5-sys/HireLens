"""Integration tests for Flask application routes, downloads, and fallback modes."""

import io
import pytest
from app import app
from utils.helpers import get_sample_candidate, get_sample_job_description


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    with app.test_client() as client:
        yield client


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"HireLens" in response.data
    assert b"stronger resume" in response.data or b"Tailor your resume" in response.data


def test_analyzer_page(client):
    response = client.get("/analyzer")
    assert response.status_code == 200
    assert b"Your Master Resume" in response.data
    assert b"Target Job Description" in response.data


def test_about_page(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert b"The HireLens Venture Story" in response.data or b"HireLens" in response.data
    assert b"Target Customer Segments" in response.data


def test_analyze_flow_and_results(client):
    sample_cand = get_sample_candidate()
    sample_job = get_sample_job_description()

    # Submit analysis
    response = client.post(
        "/analyze",
        data={
            "resume_text": sample_cand["raw_text"],
            "job_description": sample_job["raw_text"]
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Alignment Score" in response.data or b"Resume-Job Alignment" in response.data
    assert b"Matched Skills" in response.data
    assert b"Missing / Critical Job Skills" in response.data


def test_tailored_resume_page(client):
    sample_cand = get_sample_candidate()
    sample_job = get_sample_job_description()

    # Prime session
    client.post(
        "/analyze",
        data={
            "resume_text": sample_cand["raw_text"],
            "job_description": sample_job["raw_text"]
        }
    )

    response = client.get("/tailor")
    assert response.status_code == 200
    assert b"AI-Tailored Resume Optimization" in response.data
    assert b"Targeted Professional Summary" in response.data


def test_cover_letter_page(client):
    sample_cand = get_sample_candidate()
    sample_job = get_sample_job_description()

    # Prime session
    client.post(
        "/analyze",
        data={
            "resume_text": sample_cand["raw_text"],
            "job_description": sample_job["raw_text"]
        }
    )

    response = client.get("/cover-letter")
    assert response.status_code == 200
    assert b"Customized Application Letter" in response.data
    assert b"RE: Application for" in response.data


def test_download_resume_docx(client):
    sample_cand = get_sample_candidate()
    sample_job = get_sample_job_description()

    # Prime session
    client.post(
        "/analyze",
        data={
            "resume_text": sample_cand["raw_text"],
            "job_description": sample_job["raw_text"]
        }
    )

    response = client.get("/download/resume")
    assert response.status_code == 200
    assert response.headers["Content-Disposition"].startswith("attachment;")
    assert "Tailored_Resume.docx" in response.headers["Content-Disposition"]
    assert len(response.data) > 1000  # Non-empty docx binary


def test_download_cover_letter_pdf(client):
    sample_cand = get_sample_candidate()
    sample_job = get_sample_job_description()

    # Prime session
    client.post(
        "/analyze",
        data={
            "resume_text": sample_cand["raw_text"],
            "job_description": sample_job["raw_text"]
        }
    )

    response = client.get("/download/cover-letter")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert response.headers["Content-Disposition"].startswith("attachment;")
    assert "Cover_Letter.pdf" in response.headers["Content-Disposition"]
    assert response.data.startswith(b"%PDF")  # Valid PDF header


def test_analyze_missing_input_error(client):
    response = client.post(
        "/analyze",
        data={
            "resume_text": "",
            "job_description": ""
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Please paste a valid job description" in response.data
