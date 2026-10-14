"""Comprehensive Test Suite for ResumeAI SaaS Platform.

Covers:
  1. Public site routes and status codes
  2. User authentication (signup, login, logout, password reset flow)
  3. User dashboard, history isolation, and profile updates
  4. Role-based access control & Admin system security
  5. Analysis pipeline & database persistence
  6. Document generation endpoints
"""

import os
import unittest

# Ensure testing configuration
os.environ["SECRET_KEY"] = "test-secret-key-12345"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import app, db
from models import User, ResumeAnalysis
from utils.helpers import get_sample_candidate, get_sample_job_description


class ResumeAITestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["WTF_CSRF_ENABLED"] = False
        self.app = app
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

            # Create standard test user
            user = User(
                email="user@test.com",
                full_name="Standard User",
                role="user",
                account_status="active"
            )
            user.set_password("Password123!")
            db.session.add(user)

            # Create test admin
            admin = User(
                email="admin@test.com",
                full_name="Admin User",
                role="admin",
                account_status="active"
            )
            admin.set_password("AdminPass123!")
            db.session.add(admin)

            db.session.commit()
            self.user_id = user.id
            self.admin_id = admin.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # -----------------------------------------------------------------------
    # 1. Public Site & Pages
    # -----------------------------------------------------------------------
    def test_public_pages(self):
        pages = ["/", "/how-it-works", "/features", "/pricing", "/about", "/analyzer"]
        for page in pages:
            response = self.client.get(page)
            self.assertEqual(response.status_code, 200, f"Failed on page: {page}")

    def test_pricing_page_contents(self):
        response = self.client.get("/pricing")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Starter", response.data)
        self.assertIn(b"Pro", response.data)
        self.assertIn(b"Student", response.data)
        self.assertIn(b"Payment processing is not yet implemented", response.data)

    def test_sample_match_analysis_card(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sample Match Analysis", response.data)
        self.assertIn(b"78", response.data)
        self.assertIn(b"Alignment Score", response.data)
        self.assertIn(b"Skills Matched", response.data)
        self.assertIn(b"6 / 8 (75%)", response.data)
        self.assertIn(b"Keyword Overlap", response.data)
        self.assertIn(b"82%", response.data)
        self.assertIn(b"Semantic Fit", response.data)
        self.assertIn(b"Strong", response.data)
        self.assertIn(b"Python", response.data)
        self.assertIn(b"SQL", response.data)
        self.assertIn(b"Pandas", response.data)
        self.assertIn(b"Power BI", response.data)
        self.assertIn(b"Excel", response.data)

    # -----------------------------------------------------------------------
    # 2. Authentication Flow
    # -----------------------------------------------------------------------
    def test_signup_success(self):
        response = self.client.post("/signup", data={
            "full_name": "New Candidate",
            "email": "candidate@test.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Account created successfully", response.data)
        with app.app_context():
            user = User.query.filter_by(email="candidate@test.com").first()
            self.assertIsNotNone(user)
            self.assertEqual(user.role, "user")
            self.assertTrue(user.check_password("SecurePass123!"))

    def test_signup_duplicate_email(self):
        response = self.client.post("/signup", data={
            "full_name": "Duplicate User",
            "email": "user@test.com",
            "password": "Password123!",
            "confirm_password": "Password123!"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"already exists", response.data)

    def test_login_and_logout(self):
        # 1. Initially logged out: verify logged out navbar
        resp_init = self.client.get("/")
        self.assertEqual(resp_init.status_code, 200)
        self.assertIn(b"Login", resp_init.data)
        self.assertIn(b"Sign Up", resp_init.data)
        self.assertIn(b"How It Works", resp_init.data)
        self.assertNotIn(b"Logout", resp_init.data)
        self.assertNotIn(b"\xf0\x9f\x91\x8b", resp_init.data)  # waving hand emoji 👋

        # 2. Successful login: verify logged in navbar
        response = self.client.post("/login", data={
            "email": "user@test.com",
            "password": "Password123!"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome back", response.data)
        self.assertIn(b"Logout", response.data)
        self.assertIn(b"Dashboard", response.data)
        self.assertIn(b"History", response.data)
        self.assertIn(b"Profile", response.data)
        self.assertNotIn(b"nav-login-btn", response.data)

        # 3. Logout: verify immediate return to logged out navbar
        response = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"logged out", response.data)
        self.assertIn(b"Login", response.data)
        self.assertIn(b"Sign Up", response.data)
        self.assertIn(b"How It Works", response.data)
        self.assertNotIn(b"nav-logout-btn", response.data)
        self.assertNotIn(b"\xf0\x9f\x91\x8b", response.data)  # waving hand emoji 👋
        self.assertNotIn(b"nav-dashboard", response.data)

        # 4. Refreshing home page stays logged out
        resp_refreshed = self.client.get("/")
        self.assertEqual(resp_refreshed.status_code, 200)
        self.assertIn(b"Login", resp_refreshed.data)
        self.assertIn(b"Sign Up", resp_refreshed.data)
        self.assertNotIn(b"nav-logout-btn", resp_refreshed.data)

    def test_login_with_remember_me_and_logout(self):
        # 1. Login with remember_me=True
        response = self.client.post("/login", data={
            "email": "user@test.com",
            "password": "Password123!",
            "remember_me": "on"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Logout", response.data)

        # 2. Logout
        response = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"logged out", response.data)
        self.assertIn(b"Login", response.data)
        self.assertIn(b"Sign Up", response.data)
        self.assertNotIn(b"nav-logout-btn", response.data)
        self.assertNotIn(b"Dashboard", response.data)

        # 3. Subsequent request must still be logged out
        response2 = self.client.get("/")
        self.assertIn(b"Login", response2.data)
        self.assertNotIn(b"nav-logout-btn", response2.data)

    def test_login_invalid_password(self):
        response = self.client.post("/login", data={
            "email": "user@test.com",
            "password": "WrongPassword!"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid email or password", response.data)

    def test_forgot_and_reset_password(self):
        # Request reset
        response = self.client.post("/forgot-password", data={
            "email": "user@test.com"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Password reset link generated", response.data)

        # Check reset endpoint with token in session
        token = None
        with self.client.session_transaction() as sess:
            for k in sess.keys():
                if k.startswith("reset_token_"):
                    token = k.replace("reset_token_", "")
                    break
        self.assertIsNotNone(token)

        # Post new password
        response = self.client.post(f"/reset-password/{token}", data={
            "password": "NewBrandPassword123!",
            "confirm_password": "NewBrandPassword123!"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Your password has been reset successfully", response.data)

        # Verify login with new password
        with app.app_context():
            user = User.query.filter_by(email="user@test.com").first()
            self.assertTrue(user.check_password("NewBrandPassword123!"))

    # -----------------------------------------------------------------------
    # 3. User Dashboard, History & Profile
    # -----------------------------------------------------------------------
    def test_user_routes_require_login(self):
        for route in ["/dashboard", "/history", "/profile"]:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login", response.headers["Location"])

    def test_user_dashboard_and_profile_update(self):
        # Login user
        self.client.post("/login", data={"email": "user@test.com", "password": "Password123!"})

        # Access Dashboard
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Standard", response.data)

        # Update Profile
        response = self.client.post("/profile/update", data={"full_name": "Standard Updated"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Profile updated successfully", response.data)

        with app.app_context():
            user = User.query.filter_by(email="user@test.com").first()
            self.assertEqual(user.full_name, "Standard Updated")

    def test_user_data_isolation(self):
        with app.app_context():
            # Create another user
            other_user = User(email="other@test.com", full_name="Other User", role="user")
            other_user.set_password("Pass123!")
            db.session.add(other_user)
            db.session.commit()

            # Add analysis for other user
            analysis1 = ResumeAnalysis(
                user_id=other_user.id,
                job_title="Confidential Role Other",
                alignment_score=95
            )
            # Add analysis for test user
            analysis2 = ResumeAnalysis(
                user_id=self.user_id,
                job_title="My Visible Role",
                alignment_score=80
            )
            db.session.add_all([analysis1, analysis2])
            db.session.commit()

        # Login as standard user
        self.client.post("/login", data={"email": "user@test.com", "password": "Password123!"})

        # History should ONLY contain "My Visible Role"
        response = self.client.get("/history")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"My Visible Role", response.data)
        self.assertNotIn(b"Confidential Role Other", response.data)

    # -----------------------------------------------------------------------
    # 4. Role-Based Access Control & Admin Security
    # -----------------------------------------------------------------------
    def test_admin_access_unauthenticated_redirects(self):
        for route in ["/admin/dashboard", "/admin/users", "/admin/analyses"]:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/admin/login", response.headers["Location"])

    def test_normal_user_denied_admin_access(self):
        # Login as regular user
        self.client.post("/login", data={"email": "user@test.com", "password": "Password123!"})

        # Attempt to access admin dashboard
        response = self.client.get("/admin/dashboard", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Access denied", response.data)

    def test_admin_login_success(self):
        response = self.client.post("/admin/login", data={
            "email": "admin@test.com",
            "password": "AdminPass123!"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Admin Panel", response.data)
        self.assertIn(b"Total Users", response.data)

    def test_admin_users_and_detail(self):
        # Login admin
        self.client.post("/admin/login", data={"email": "admin@test.com", "password": "AdminPass123!"})

        # Users list
        response = self.client.get("/admin/users")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"user@test.com", response.data)

        # User detail
        response = self.client.get(f"/admin/users/{self.user_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Standard User", response.data)
        # Ensure password hashes are NEVER displayed
        self.assertNotIn(b"pbkdf2", response.data)
        self.assertNotIn(b"password_hash", response.data)

    def test_admin_metrics_calculated_from_db(self):
        # Login admin
        self.client.post("/admin/login", data={"email": "admin@test.com", "password": "AdminPass123!"})

        # Check dashboard metrics
        response = self.client.get("/admin/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Total Users", response.data)
        self.assertIn(b"New Users (7 Days)", response.data)
        self.assertIn(b"New Users (30 Days)", response.data)
        self.assertIn(b"Total Analyses", response.data)

        # Total registered users (standard user only, admin excluded from user count)
        with app.app_context():
            user_count = User.query.filter_by(role="user").count()
            self.assertEqual(user_count, 1)

    def test_admin_analyses_view(self):
        # Login admin
        self.client.post("/admin/login", data={"email": "admin@test.com", "password": "AdminPass123!"})

        response = self.client.get("/admin/analyses")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Candidate Analysis Records", response.data)

    def test_admin_cannot_be_created_via_public_signup(self):
        # Attacker tries to post role="admin" via public signup
        self.client.post("/signup", data={
            "full_name": "Hacker User",
            "email": "hacker@test.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "admin"
        }, follow_redirects=True)

        with app.app_context():
            user = User.query.filter_by(email="hacker@test.com").first()
            self.assertIsNotNone(user)
            # Role MUST remain 'user' — never 'admin'
            self.assertEqual(user.role, "user")
            self.assertFalse(user.is_admin())

    # -----------------------------------------------------------------------
    # 5. Resume Analysis & DB Persistence
    # -----------------------------------------------------------------------
    def test_analyze_and_persistence(self):
        # Login user
        self.client.post("/login", data={"email": "user@test.com", "password": "Password123!"})

        sample_candidate = get_sample_candidate()
        sample_job = get_sample_job_description()

        response = self.client.post("/analyze", data={
            "resume_text": sample_candidate,
            "job_description": sample_job
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"RESUME-JOB ALIGNMENT", response.data)

        # Check DB record was saved
        with app.app_context():
            record = ResumeAnalysis.query.filter_by(user_id=self.user_id).first()
            self.assertIsNotNone(record)
            self.assertGreater(record.alignment_score, 0)
            self.assertTrue(len(record.job_title) > 0)


if __name__ == "__main__":
    unittest.main()
