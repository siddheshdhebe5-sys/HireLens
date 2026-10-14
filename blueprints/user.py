"""User Blueprint.

Protected routes for authenticated users:
  /dashboard  — overview stats + recent analyses
  /history    — full analysis history
  /profile    — view and update profile, change password

Security:
  - All routes require @login_required.
  - All DB queries filter strictly by current_user.id.
  - The 'role' field is NEVER writable via any form here.
  - Password changes require current password verification.
"""

from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash
)
from flask_login import login_required, current_user
from sqlalchemy import desc

from models import db, User, ResumeAnalysis

user_bp = Blueprint("user", __name__)


# ---------------------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------------------

@user_bp.route("/dashboard")
@login_required
def dashboard():
    """User dashboard: welcome, quick stats, recent analyses."""
    # Latest 5 analyses for this user only
    recent = (
        ResumeAnalysis.query
        .filter_by(user_id=current_user.id)
        .order_by(desc(ResumeAnalysis.created_at))
        .limit(5)
        .all()
    )
    total_analyses = ResumeAnalysis.query.filter_by(user_id=current_user.id).count()
    latest_score = recent[0].alignment_score if recent else None

    return render_template(
        "dashboard.html",
        recent_analyses=recent,
        total_analyses=total_analyses,
        latest_score=latest_score,
    )


# ---------------------------------------------------------------------------
# HISTORY
# ---------------------------------------------------------------------------

@user_bp.route("/history")
@login_required
def history():
    """Full analysis history — ONLY this user's records, never other users'."""
    page = request.args.get("page", 1, type=int)
    per_page = 10

    # Strictly filtered by current_user.id — users cannot access each other's data
    pagination = (
        ResumeAnalysis.query
        .filter_by(user_id=current_user.id)
        .order_by(desc(ResumeAnalysis.created_at))
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return render_template(
        "history.html",
        analyses=pagination.items,
        pagination=pagination,
    )


# ---------------------------------------------------------------------------
# PROFILE
# ---------------------------------------------------------------------------

@user_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    """View user profile."""
    analysis_count = ResumeAnalysis.query.filter_by(user_id=current_user.id).count()
    return render_template("profile.html", analysis_count=analysis_count)


@user_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    """Update full name only. Role is NEVER writable here."""
    full_name = request.form.get("full_name", "").strip()

    if not full_name or len(full_name) < 2:
        flash("Please enter a valid name (at least 2 characters).", "warning")
        return redirect(url_for("user.profile"))

    current_user.full_name = full_name
    current_user.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    flash("Profile updated successfully!", "success")
    return redirect(url_for("user.profile"))


@user_bp.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    """Change password — requires current password verification."""
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_user.check_password(current_password):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for("user.profile"))

    if len(new_password) < 8:
        flash("New password must be at least 8 characters.", "warning")
        return redirect(url_for("user.profile"))

    if new_password != confirm_password:
        flash("New passwords do not match.", "danger")
        return redirect(url_for("user.profile"))

    current_user.set_password(new_password)
    current_user.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    flash("Password changed successfully!", "success")
    return redirect(url_for("user.profile"))
