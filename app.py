"""ResumeAI - AI-Powered Resume & Cover Letter Tailoring Agent.

Flask Application Module — Full SaaS Platform.

Architecture:
  - Flask-Login for session management
  - Flask-SQLAlchemy with SQLite (upgradeable to PostgreSQL via DATABASE_URL)
  - Three Blueprints: auth (public auth), user (protected), admin (admin-only)
  - All existing resume-analysis routes preserved unchanged
  - Analysis results persisted to DB when user is authenticated
"""

import os
import io
import uuid
import click
from typing import Dict, Any

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, send_file, jsonify
)
from flask_login import LoginManager, current_user, login_required
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from models import db, User, ResumeAnalysis
from services.resume_parser import ResumeParser, ResumeParsingError
from services.resume_analyzer import ResumeAnalyzer
from services.ai_service import AIService
from services.resume_generator import ResumeGenerator
from services.cover_letter_generator import CoverLetterGenerator
from utils.helpers import (
    allowed_file, sanitize_text, get_sample_candidate,
    get_sample_job_description, MAX_FILE_SIZE_BYTES
)

# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------

load_dotenv()

app = Flask(__name__)

# Core config
app.secret_key = os.getenv("SECRET_KEY", "resumeai-dev-secret-key-2026-change-me")
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH_MB", 5)) * 1024 * 1024

# Database
database_url = os.getenv("DATABASE_URL", "sqlite:///resumeai.db")
# Render / cloud compatibility: SQLAlchemy 1.4+ requires postgresql:// instead of postgres://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Ensure instance directory exists for SQLite
try:
    os.makedirs(app.instance_path, exist_ok=True)
except OSError:
    pass

# Initialize extensions
db.init_app(app)

# Ensure database tables are created safely during application startup
with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

# ---------------------------------------------------------------------------
# In-memory server session store (preserves existing analyze UX)
# ---------------------------------------------------------------------------

SESSION_STORE: Dict[str, Dict[str, Any]] = {}


def get_user_store() -> Dict[str, Any]:
    """Retrieves or creates the user's isolated in-memory session store."""
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    sid = session["session_id"]
    if sid not in SESSION_STORE:
        SESSION_STORE[sid] = {}
    return SESSION_STORE[sid]


# ---------------------------------------------------------------------------
# Flask-Login user loader
# ---------------------------------------------------------------------------

@login_manager.user_loader
def load_user(user_id: str):
    """Load user from DB by ID for Flask-Login."""
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Register Blueprints
# ---------------------------------------------------------------------------

from blueprints.auth import auth_bp
from blueprints.user import user_bp
from blueprints.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)


# ---------------------------------------------------------------------------
# Global Template Context & Response Headers
# ---------------------------------------------------------------------------

@app.context_processor
def inject_global_context():
    """Injects global template variables."""
    return {
        "is_ai_live": AIService.is_ai_available(),
        "app_name": "HireLens",
        "app_tagline": "Your Skills. A Brighter Tomorrow.",
    }


@app.after_request
def add_security_and_cache_headers(response):
    """Prevent browsers from caching authenticated HTML responses and exposing stale auth states."""
    if response.content_type and "text/html" in response.content_type:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# ---------------------------------------------------------------------------
# Main Blueprint (public pages)
# ---------------------------------------------------------------------------

from flask import Blueprint
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Landing page."""
    return render_template("index.html")


@main_bp.route("/how-it-works")
def how_it_works():
    """How It Works page."""
    return render_template("pages/how_it_works.html")


@main_bp.route("/features")
def features():
    """Features page."""
    return render_template("pages/features.html")


@main_bp.route("/pricing")
def pricing():
    """Pricing page."""
    return render_template("pages/pricing.html")


@main_bp.route("/about")
def about():
    """About / Venture page."""
    return render_template("about.html")


app.register_blueprint(main_bp)


# ---------------------------------------------------------------------------
# Resume Analysis Routes (preserved from original, with DB persistence)
# ---------------------------------------------------------------------------

@app.route("/analyzer")
def analyzer():
    """Main input interface for resume upload + job description."""
    sample_candidate = get_sample_candidate()
    sample_job = get_sample_job_description()
    return render_template(
        "analyzer.html",
        sample_candidate=sample_candidate,
        sample_job=sample_job
    )


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    """Handles resume extraction, job description analysis, and score calculation."""
    if request.method == "GET":
        return redirect(url_for("analyzer"))
    try:
        job_text = request.form.get("job_description", "").strip()
        if not job_text or len(job_text) < 20:
            flash("Please paste a valid job description (at least 20 characters) to analyze against.", "warning")
            return redirect(url_for("analyzer"))

        resume_text_manual = request.form.get("resume_text", "").strip()
        uploaded_file = request.files.get("resume_file")
        resume_name = "Text Input"

        # Process file upload or manual text
        if uploaded_file and uploaded_file.filename:
            if not allowed_file(uploaded_file.filename):
                flash("Unsupported file type. Please upload a .pdf or .docx resume file.", "danger")
                return redirect(url_for("analyzer"))

            filename = secure_filename(uploaded_file.filename)
            resume_name = filename
            file_bytes = uploaded_file.read()
            if len(file_bytes) > MAX_FILE_SIZE_BYTES:
                flash("Uploaded file exceeds 5MB limit. Please upload a smaller file.", "danger")
                return redirect(url_for("analyzer"))

            resume_data = ResumeParser.parse_file(filename, file_bytes)
        elif resume_text_manual:
            resume_data = ResumeParser.parse_raw_text(resume_text_manual)
        else:
            flash("Please upload a PDF/DOCX resume or paste your resume text.", "warning")
            return redirect(url_for("analyzer"))

        # Run multi-factor analysis
        analysis_result = ResumeAnalyzer.analyze(resume_data, job_text)

        # Store results in server-side session store (preserves existing UX)
        store = get_user_store()
        store["resume_data"] = resume_data
        store["job_text"] = job_text
        store["analysis_result"] = analysis_result
        store["resume_name"] = resume_name
        store.pop("tailored_data", None)
        store.pop("cover_letter_data", None)

        # Persist to database if user is authenticated
        if current_user.is_authenticated:
            try:
                job_meta = analysis_result.get("job_meta", {})
                skills_info = analysis_result.get("skills", {})
                breakdown = analysis_result.get("breakdown", {})
                missing_skills_raw = skills_info.get("missing", [])
                recs_raw = analysis_result.get("recommendations", [])

                record = ResumeAnalysis(
                    user_id=current_user.id,
                    job_title=job_meta.get("title", "Unknown Role") or "Unknown Role",
                    company=job_meta.get("company", "") or "",
                    resume_name=resume_name,
                    alignment_score=int(analysis_result.get("score", 0)),
                    skills_matched=int(skills_info.get("matched_count", 0)),
                    keyword_overlap=int(breakdown.get("keyword_score", 0)),
                    semantic_fit=int(breakdown.get("semantic_score", 0)),
                )
                # Serialize missing skills list
                record.missing_skills = [s.get("name", str(s)) for s in missing_skills_raw]
                # Serialize recommendations list
                record.recommendations = [r.get("title", str(r)) for r in recs_raw]

                db.session.add(record)
                db.session.commit()
            except Exception as db_err:
                # DB persistence failure should not break the analysis UX
                app.logger.warning(f"Failed to persist analysis to DB: {db_err}")

        return redirect(url_for("results"))

    except ResumeParsingError as rpe:
        flash(f"Resume Processing Error: {str(rpe)}", "danger")
        return redirect(url_for("analyzer"))
    except Exception as e:
        flash(f"Analysis Error: {str(e)}", "danger")
        return redirect(url_for("analyzer"))


@app.route("/results")
def results():
    """Displays ATS-style match score, matched skills, missing skills, and recommendations."""
    store = get_user_store()
    analysis_result = store.get("analysis_result")
    resume_data = store.get("resume_data")

    if not analysis_result or not resume_data:
        flash("No active analysis found. Please upload your resume to begin.", "info")
        return redirect(url_for("analyzer"))

    return render_template(
        "results.html",
        analysis=analysis_result,
        resume=resume_data
    )


@app.route("/tailor")
def tailor():
    """Generates and displays AI-tailored summary and bullet improvements."""
    store = get_user_store()
    resume_data = store.get("resume_data")
    job_text = store.get("job_text")
    analysis_result = store.get("analysis_result")

    if not resume_data or not job_text or not analysis_result:
        flash("Please analyze a resume first before viewing tailored recommendations.", "warning")
        return redirect(url_for("analyzer"))

    tailored_data = store.get("tailored_data")
    if not tailored_data:
        tailored_data = AIService.generate_tailored_resume(resume_data, job_text, analysis_result)
        store["tailored_data"] = tailored_data

    return render_template(
        "tailored_resume.html",
        tailored=tailored_data,
        resume=resume_data,
        analysis=analysis_result
    )


@app.route("/cover-letter")
def cover_letter():
    """Generates and displays a personalized cover letter."""
    store = get_user_store()
    resume_data = store.get("resume_data")
    job_text = store.get("job_text")
    analysis_result = store.get("analysis_result")

    if not resume_data or not job_text or not analysis_result:
        flash("Please analyze a resume first before generating a cover letter.", "warning")
        return redirect(url_for("analyzer"))

    cover_letter_data = store.get("cover_letter_data")
    if not cover_letter_data:
        cover_letter_data = AIService.generate_cover_letter(resume_data, job_text, analysis_result)
        store["cover_letter_data"] = cover_letter_data

    return render_template(
        "cover_letter.html",
        letter=cover_letter_data,
        resume=resume_data,
        analysis=analysis_result
    )


@app.route("/download/resume")
def download_resume():
    """Generates and streams tailored .docx resume document for download."""
    store = get_user_store()
    resume_data = store.get("resume_data")
    tailored_data = store.get("tailored_data")
    analysis_result = store.get("analysis_result")

    if not resume_data or not analysis_result:
        flash("No active resume session. Please analyze a resume first.", "warning")
        return redirect(url_for("analyzer"))

    if not tailored_data:
        job_text = store.get("job_text", "")
        tailored_data = AIService.generate_tailored_resume(resume_data, job_text, analysis_result)
        store["tailored_data"] = tailored_data

    docx_stream = ResumeGenerator.generate_docx(resume_data, tailored_data, analysis_result)
    candidate_name = resume_data.get("contact", {}).get("name", "Candidate").replace(" ", "_")
    filename = f"{candidate_name}_Tailored_Resume.docx"

    return send_file(
        docx_stream,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@app.route("/download/cover-letter")
def download_cover_letter():
    """Generates and streams tailored .pdf cover letter document for download."""
    store = get_user_store()
    resume_data = store.get("resume_data")
    cover_letter_data = store.get("cover_letter_data")
    analysis_result = store.get("analysis_result")

    if not resume_data or not analysis_result:
        flash("No active cover letter session. Please analyze a resume first.", "warning")
        return redirect(url_for("analyzer"))

    if not cover_letter_data:
        job_text = store.get("job_text", "")
        cover_letter_data = AIService.generate_cover_letter(resume_data, job_text, analysis_result)
        store["cover_letter_data"] = cover_letter_data

    pdf_stream = CoverLetterGenerator.generate_pdf(cover_letter_data, resume_data, analysis_result)
    candidate_name = resume_data.get("contact", {}).get("name", "Applicant").replace(" ", "_")
    filename = f"{candidate_name}_Cover_Letter.pdf"

    return send_file(
        pdf_stream,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------

@app.errorhandler(413)
def file_too_large(e):
    flash("File is too large. Maximum permitted upload size is 5MB.", "danger")
    return redirect(url_for("analyzer"))


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------

@app.cli.command("create-admin")
@click.argument("email")
@click.argument("name")
@click.password_option(prompt="Admin password", confirmation_prompt="Confirm password")
def create_admin(email: str, name: str, password: str):
    """
    Create the first admin account.

    Usage:
        flask create-admin admin@example.com "Admin Name"

    This is the ONLY way to create an admin account.
    No public UI exists for this operation.
    """
    with app.app_context():
        db.create_all()
        existing = User.query.filter_by(email=email.lower().strip()).first()
        if existing:
            if existing.is_admin():
                click.echo(f"[INFO] Admin account already exists for: {email}")
            else:
                existing.role = "admin"
                existing.set_password(password)
                db.session.commit()
                click.echo(f"[OK] Promoted existing user {email} to admin.")
            return

        admin = User(
            email=email.lower().strip(),
            full_name=name,
            role="admin",
            account_status="active"
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"[OK] Admin account created: {email} (role=admin)")
        click.echo("[INFO] Login at: /admin/login")


@app.cli.command("init-db")
def init_db():
    """Create all database tables."""
    db.create_all()
    click.echo("[OK] Database tables created.")


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
