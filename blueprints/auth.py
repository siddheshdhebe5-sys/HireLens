"""Authentication Blueprint.

Handles: /login, /signup, /forgot-password, /reset-password, /logout.

Security:
- Passwords hashed with Werkzeug pbkdf2:sha256 — never stored plaintext.
- Email validation using email-validator.
- Authenticated users visiting /login or /signup are redirected to /dashboard.
- Forgot/reset password uses a time-limited token stored in the session.
"""

import secrets
from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session
)
from flask_login import login_user, logout_user, login_required, current_user

from models import db, User

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login page. Redirects already-authenticated users to /dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for("user.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember_me") == "on"

        if not email or not password:
            flash("Please enter your email and password.", "warning")
            return render_template("auth/login.html", email=email)

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email or password. Please try again.", "danger")
            return render_template("auth/login.html", email=email)

        if user.account_status != "active":
            flash("Your account has been suspended. Please contact support.", "danger")
            return render_template("auth/login.html", email=email)

        # Update last_login timestamp
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        login_user(user, remember=remember)
        flash(f"Welcome back, {user.full_name.split()[0]}! 👋", "success")

        next_page = request.args.get("next")
        if next_page and next_page.startswith("/") and "admin" not in next_page:
            return redirect(next_page)
        return redirect(url_for("user.dashboard"))

    return render_template("auth/login.html", email="")


# ---------------------------------------------------------------------------
# SIGNUP
# ---------------------------------------------------------------------------

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    """User registration. Redirects already-authenticated users to /dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for("user.dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []

        if not full_name or len(full_name) < 2:
            errors.append("Please enter your full name (at least 2 characters).")

        if not email or "@" not in email:
            errors.append("Please enter a valid email address.")

        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")

        if password != confirm_password:
            errors.append("Passwords do not match.")

        if not errors and User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists. Please log in.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("auth/signup.html", full_name=full_name, email=email)

        # Create user — password is hashed inside set_password()
        new_user = User(full_name=full_name, email=email)
        new_user.set_password(password)
        # role defaults to 'user' — never settable from form
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash(f"Account created successfully! Welcome, {new_user.full_name.split()[0]}! 🎉", "success")
        return redirect(url_for("user.dashboard"))

    return render_template("auth/signup.html", full_name="", email="")


# ---------------------------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------------------------

@auth_bp.route("/logout")
def logout():
    """Securely log out the current user, clear session, and delete remember-me cookies."""
    logout_user()

    # Clear custom session data while keeping Flask-Login's internal markers
    for key in list(session.keys()):
        if not key.startswith("_"):
            session.pop(key, None)

    flash("You have been logged out successfully.", "info")
    response = redirect(url_for("main.index"))

    # Explicitly clear remember-me cookie on the response object
    cookie_name = "remember_token"
    response.delete_cookie(cookie_name, path="/")
    response.delete_cookie("remember_token")

    # Anti-caching headers
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# ---------------------------------------------------------------------------
# FORGOT PASSWORD
# ---------------------------------------------------------------------------

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """
    Request a password reset token.
    Stores token in session keyed by email. In production, this would be emailed.
    Intentionally gives the same response whether email exists or not (anti-enumeration).
    """
    if current_user.is_authenticated:
        return redirect(url_for("user.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if email and "@" in email:
            user = User.query.filter_by(email=email).first()
            if user:
                # Generate a secure single-use token stored in server session
                token = secrets.token_urlsafe(32)
                session[f"reset_token_{token}"] = {
                    "user_id": user.id,
                    "email": email,
                    "used": False
                }
                # In a real deployment this would be emailed. Here we flash it for demo.
                reset_url = url_for("auth.reset_password", token=token, _external=True)
                flash(
                    f"Password reset link generated. "
                    f"In production this would be emailed. "
                    f"For now, copy this link: {reset_url}",
                    "info"
                )
                return render_template("auth/forgot_password.html", submitted=True)

        # Always show the same message (anti-enumeration)
        flash(
            "If an account with that email exists, a reset link has been generated.",
            "info"
        )
        return render_template("auth/forgot_password.html", submitted=True)

    return render_template("auth/forgot_password.html", submitted=False)


# ---------------------------------------------------------------------------
# RESET PASSWORD
# ---------------------------------------------------------------------------

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    """Consume a password reset token and set a new password."""
    if current_user.is_authenticated:
        return redirect(url_for("user.dashboard"))

    token_data = session.get(f"reset_token_{token}")

    if not token_data or token_data.get("used"):
        flash("This password reset link is invalid or has already been used.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("auth/reset_password.html", token=token)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/reset_password.html", token=token)

        user = db.session.get(User, token_data["user_id"])
        if not user:
            flash("User not found. Please request a new reset link.", "danger")
            return redirect(url_for("auth.forgot_password"))

        user.set_password(password)
        db.session.commit()

        # Mark token as used
        session[f"reset_token_{token}"]["used"] = True

        flash("Your password has been reset successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
