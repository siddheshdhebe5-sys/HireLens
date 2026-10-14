"""ResumeAI Database Models.

Defines User and ResumeAnalysis models using Flask-SQLAlchemy.
Passwords are ALWAYS stored as hashed values — never plaintext.
The admin role is assigned only via the 'flask create-admin' CLI command.
"""

import json
from datetime import datetime, timezone
from typing import Optional

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


class User(db.Model, UserMixin):
    """
    Application user.

    role: 'user' (default) or 'admin'.
    Admin role is assigned ONLY via the flask create-admin CLI command.
    Normal users can NEVER promote themselves to admin via any form.
    The password_hash field is NEVER included in template context.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # 'user' | 'admin'
    account_status = db.Column(db.String(20), nullable=False, default="active")  # 'active' | 'suspended'
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=True, onupdate=utcnow)
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    analyses = db.relationship(
        "ResumeAnalysis",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def set_password(self, raw_password: str) -> None:
        """Hash and store the given plaintext password securely."""
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, raw_password)

    def is_admin(self) -> bool:
        """Return True if this user has the admin role."""
        return self.role == "admin"

    def to_safe_dict(self) -> dict:
        """Return a dict of non-sensitive user fields (NO password_hash)."""
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "account_status": self.account_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login": self.last_login,
            "analysis_count": self.analyses.count(),
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"


class ResumeAnalysis(db.Model):
    """
    Persisted record of a single resume-vs-job analysis.
    Linked to a User via user_id foreign key.
    Users may only access their own records (enforced in queries).
    """
    __tablename__ = "resume_analyses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # Job metadata
    job_title = db.Column(db.String(255), nullable=True)
    company = db.Column(db.String(255), nullable=True)
    resume_name = db.Column(db.String(255), nullable=True, default="Text Input")

    # Scores (0–100 integers)
    alignment_score = db.Column(db.Integer, nullable=False, default=0)
    skills_matched = db.Column(db.Integer, nullable=False, default=0)
    keyword_overlap = db.Column(db.Integer, nullable=False, default=0)
    semantic_fit = db.Column(db.Integer, nullable=False, default=0)

    # JSON-serialized lists
    _missing_skills = db.Column("missing_skills", db.Text, nullable=True)
    _recommendations = db.Column("recommendations", db.Text, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    @property
    def missing_skills(self) -> list:
        if not self._missing_skills:
            return []
        try:
            return json.loads(self._missing_skills)
        except (json.JSONDecodeError, TypeError):
            return []

    @missing_skills.setter
    def missing_skills(self, value: list) -> None:
        self._missing_skills = json.dumps(value) if value else "[]"

    @property
    def recommendations(self) -> list:
        if not self._recommendations:
            return []
        try:
            return json.loads(self._recommendations)
        except (json.JSONDecodeError, TypeError):
            return []

    @recommendations.setter
    def recommendations(self, value: list) -> None:
        self._recommendations = json.dumps(value) if value else "[]"

    def to_dict(self) -> dict:
        """Safe serializable representation of this analysis record."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "job_title": self.job_title or "Unknown Role",
            "company": self.company or "Unknown Company",
            "resume_name": self.resume_name or "Text Input",
            "alignment_score": self.alignment_score,
            "skills_matched": self.skills_matched,
            "keyword_overlap": self.keyword_overlap,
            "semantic_fit": self.semantic_fit,
            "missing_skills": self.missing_skills,
            "recommendations": self.recommendations,
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        return f"<ResumeAnalysis id={self.id} user_id={self.user_id} score={self.alignment_score}>"
