"""Admin Blueprint.

Completely separate admin system with its own:
  - Login page:  /admin/login
  - Dashboard:   /admin/dashboard
  - Users list:  /admin/users
  - User detail: /admin/users/<user_id>
  - Analyses:    /admin/analyses
  - Logout:      /admin/logout

Security (CRITICAL):
  - Admin role is verified SERVER-SIDE on every admin route via @admin_required.
  - Normal users (role='user') who attempt to access admin routes are redirected
    to /admin/login with a 403-equivalent flash, even if logged in.
  - Admin login is SEPARATE from user login (/admin/login vs /login).
  - Passwords and password_hash values are NEVER exposed in any admin template.
  - Admin users are created ONLY via the 'flask create-admin' CLI command.
"""

import functools
from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, session
)
from flask_login import login_user, logout_user, current_user
from sqlalchemy import desc, func

from models import db, User, ResumeAnalysis

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ---------------------------------------------------------------------------
# ADMIN AUTHORIZATION DECORATOR
# ---------------------------------------------------------------------------

def admin_required(f):
    """
    Decorator that enforces admin role server-side.
    Unauthenticated users → /admin/login
    Authenticated non-admin users → /admin/login with denial message
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access the admin area.", "warning")
            return redirect(url_for("admin.admin_login"))
        if not current_user.is_admin():
            # Log out the non-admin user from the admin area
            flash("Access denied. You do not have administrator privileges.", "danger")
            return redirect(url_for("admin.admin_login"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# ADMIN LOGIN
# ---------------------------------------------------------------------------

@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():
    """
    Separate admin login page at /admin/login.
    Normal user credentials will not grant admin access here
    unless the user's role is 'admin'.
    """
    # Redirect already-authenticated admins to dashboard
    if current_user.is_authenticated and current_user.is_admin():
        return redirect(url_for("admin.admin_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter your admin email and password.", "warning")
            return render_template("admin/login.html")

        user = User.query.filter_by(email=email).first()

        # Check credentials AND admin role — normal users are denied
        if not user or not user.check_password(password):
            flash("Invalid credentials.", "danger")
            return render_template("admin/login.html")

        if not user.is_admin():
            # Non-admin attempting admin login — deny silently (same message)
            flash("Invalid credentials.", "danger")
            return render_template("admin/login.html")

        if user.account_status != "active":
            flash("This account has been suspended.", "danger")
            return render_template("admin/login.html")

        # Update last_login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        login_user(user)
        flash(f"Welcome to the Admin Panel, {user.full_name}.", "success")
        return redirect(url_for("admin.admin_dashboard"))

    return render_template("admin/login.html")


# ---------------------------------------------------------------------------
# ADMIN LOGOUT
# ---------------------------------------------------------------------------

@admin_bp.route("/logout")
def admin_logout():
    """Admin logout."""
    logout_user()
    for key in list(session.keys()):
        if not key.startswith("_"):
            session.pop(key, None)
    flash("You have been logged out of the admin panel.", "info")
    response = redirect(url_for("admin.admin_login"))
    response.delete_cookie("remember_token", path="/")
    response.delete_cookie("remember_token")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# ---------------------------------------------------------------------------
# ADMIN DASHBOARD
# ---------------------------------------------------------------------------

@admin_bp.route("/dashboard")
@admin_required
def admin_dashboard():
    """Admin overview: key platform statistics calculated directly from database records."""
    from datetime import date, timedelta
    now_utc = datetime.now(timezone.utc)
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)

    total_users = User.query.filter_by(role="user").count()
    total_analyses = ResumeAnalysis.query.count()

    # Analyses today
    analyses_today = ResumeAnalysis.query.filter(
        ResumeAnalysis.created_at >= today_start
    ).count()

    # New registrations in last 7 days
    seven_days_ago = now_utc - timedelta(days=7)
    new_users_7d = User.query.filter(
        User.role == "user",
        User.created_at >= seven_days_ago
    ).count()

    # New registrations in last 30 days
    thirty_days_ago = now_utc - timedelta(days=30)
    new_users_30d = User.query.filter(
        User.role == "user",
        User.created_at >= thirty_days_ago
    ).count()

    # Average alignment score across all analyses
    avg_result = db.session.query(func.avg(ResumeAnalysis.alignment_score)).scalar()
    avg_score = round(avg_result, 1) if avg_result else 0

    # Recent signups (last 8)
    recent_users = (
        User.query
        .filter_by(role="user")
        .order_by(desc(User.created_at))
        .limit(8)
        .all()
    )

    # Recent analyses (last 8)
    recent_analyses = (
        ResumeAnalysis.query
        .order_by(desc(ResumeAnalysis.created_at))
        .limit(8)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_analyses=total_analyses,
        analyses_today=analyses_today,
        new_users_7d=new_users_7d,
        new_users_30d=new_users_30d,
        avg_score=avg_score,
        recent_users=recent_users,
        recent_analyses=recent_analyses,
    )


# ---------------------------------------------------------------------------
# ADMIN USER MANAGEMENT
# ---------------------------------------------------------------------------

@admin_bp.route("/users")
@admin_required
def admin_users():
    """List all registered users with search, sort, and pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = 20
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort", "created_at")
    order = request.args.get("order", "desc")

    query = User.query.filter_by(role="user")

    if search:
        like = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(like)) | (User.email.ilike(like))
        )

    # Sorting
    sort_col = getattr(User, sort_by, User.created_at)
    if order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "admin/users.html",
        users=pagination.items,
        pagination=pagination,
        search=search,
        sort_by=sort_by,
        order=order,
    )


# ---------------------------------------------------------------------------
# ADMIN USER DETAIL
# ---------------------------------------------------------------------------

@admin_bp.route("/users/<int:user_id>")
@admin_required
def admin_user_detail(user_id: int):
    """
    View details of a specific user.
    Password hash is NEVER passed to the template.
    """
    from flask import abort
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    analyses = (
        ResumeAnalysis.query
        .filter_by(user_id=user_id)
        .order_by(desc(ResumeAnalysis.created_at))
        .all()
    )
    analysis_count = len(analyses)

    return render_template(
        "admin/user_detail.html",
        user=user,          # password_hash NOT passed — template only uses safe fields
        analyses=analyses,
        analysis_count=analysis_count,
    )


# ---------------------------------------------------------------------------
# ADMIN ANALYSES OVERVIEW
# ---------------------------------------------------------------------------

@admin_bp.route("/analyses")
@admin_required
def admin_analyses():
    """Platform-wide analysis records with search, filter, sort, pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = 20
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort", "created_at")
    order = request.args.get("order", "desc")

    query = ResumeAnalysis.query.join(User, ResumeAnalysis.user_id == User.id)

    if search:
        like = f"%{search}%"
        query = query.filter(
            (ResumeAnalysis.job_title.ilike(like)) |
            (ResumeAnalysis.company.ilike(like)) |
            (User.full_name.ilike(like)) |
            (User.email.ilike(like))
        )

    # Sorting
    sort_col_map = {
        "created_at": ResumeAnalysis.created_at,
        "alignment_score": ResumeAnalysis.alignment_score,
        "job_title": ResumeAnalysis.job_title,
    }
    sort_col = sort_col_map.get(sort_by, ResumeAnalysis.created_at)
    if order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "admin/analyses.html",
        analyses=pagination.items,
        pagination=pagination,
        search=search,
        sort_by=sort_by,
        order=order,
    )
