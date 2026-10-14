# HireLens - Distinctive Career-Tech SaaS Platform

> **"Your Skills. A Brighter Tomorrow."**  
> An AI-powered career assistant helping college students, freshers, and job seekers compare resumes with job postings, identify missing skills, understand keyword alignment, and improve their resumes with honest, explainable recommendations.

---

## 📌 1. Project Overview & Brand Identity

**HireLens** is a distinctive career-tech SaaS platform built with an editorial-inspired visual identity. Moving away from generic dark themes and neon glows, HireLens embraces warm white surfaces, deep ink typography, and muted forest-green accents.

### Core Philosophy: Honest Resume Enhancement
HireLens helps job seekers present their genuine skills and experience with maximum clarity. **We never encourage or generate fake qualifications, unearned degrees, or fabricated projects.**

### 💼 Proposed Business Model
- **Free Tier (Student / Entry-level):** Basic resume-job comparison, deterministic skill extraction, missing skill & keyword gap detection.
- **Premium (Proposed at ₹149/month):** Advanced keyword and skill-gap insights, detailed improvement recommendations, expanded analysis history, tailored professional summary suggestions, and DOCX/PDF exports.
- **University Campus B2B Vision:** Institutional placement cell licensing with aggregate readiness analytics.

---

## 🚀 2. Key Features

- 📄 **Multi-Format Document Parsing:** High-performance text extraction from **PDF** (PyMuPDF) and **Microsoft Word DOCX** (python-docx) with manual text paste fallback.
- 📊 **Explainable 4-Factor Alignment Score:**
  - Required Skill Match: 40%
  - Keyword Alignment: 25%
  - Semantic TF-IDF Cosine Similarity: 20%
  - Experience & Action Verbs Evidence: 15%
- 🔍 **Deterministic Skill Extraction:** 150+ categorized competencies across programming languages, data & AI, web frameworks, cloud/databases, tools, and professional soft skills.
- 🛡️ **Zero-Fabrication Ethical AI:** Genuine missing skill advisories; recommendations emphasize quantifiable results without inventing facts.
- 👤 **Full User Authentication & Protected Routes:**
  - Secure signup, login, remember-me sessions, and password management via Flask-Login and PBKDF2 hashing.
  - Strict user data isolation: authenticated users can only view their own resume analyses and history.
- 👑 **Private Founder Admin Dashboard:**
  - Dedicated admin portal (`/admin/login`, `/admin/dashboard`, `/admin/users`, `/admin/analyses`).
  - Real database-backed statistics (Total registered users, new registrations in last 7 and 30 days, total analyses, average alignment score).
  - Searchable and paginated candidate user management table and analysis audits.
  - Mandatory server-side `@admin_required` authorization check on every admin endpoint.
- ⚡ **Dual-Mode AI Engine:** Seamless operation with live **Google Gemini Flash** models when `GEMINI_API_KEY` is present, or an autonomous deterministic rule-based engine when in demo mode.
- 📥 **Application Exports:** Download tailored `.docx` resumes and formatted `.pdf` cover letters.

---

## 🎨 3. Design System & Palette

- **Warm Background:** `#F7F6F2`
- **Primary Surface:** `#FFFFFF`
- **Primary Text (Deep Ink):** `#20251F`
- **Secondary Text:** `#6B7069`
- **Primary Accent (Muted Forest Green):** `#426B52`
- **Accent Hover:** `#345640`
- **Light Green Surface:** `#EAF0E8`
- **Border:** `#E5E5DD`
- **Success:** `#347653`
- **Warning:** `#A36B25`
- **Error:** `#B94A48`
- **Typography:** Google Fonts **Manrope** (editorial headings) & **Inter** (clean body & data).

---

## 🛠️ 4. Technology Stack

- **Backend:** Python 3.14+, Flask 3.0+
- **Authentication:** Flask-Login, Werkzeug Security (PBKDF2 SHA-256)
- **Database ORM:** Flask-SQLAlchemy (SQLite default, PostgreSQL ready via `DATABASE_URL`)
- **Document Processing:** PyMuPDF (`fitz`), `python-docx`, `reportlab`
- **NLP & Similarity:** `scikit-learn` (TF-IDF Vectorizer & Cosine Similarity)
- **Generative AI:** Google GenAI SDK (`google-genai` using `gemini-2.5-flash`)
- **Testing:** `pytest` (38 automated unit & integration tests)

---

## 📂 5. Project Directory Structure

```
ResumeAI/
├── app.py                          # Application entry point, CLI commands, context processors
├── models.py                       # SQLAlchemy models: User and ResumeAnalysis
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── README.md                       # Platform documentation
├── PROJECT_STATUS.md               # Implementation audit & verification record
│
├── blueprints/
│   ├── auth.py                     # Public authentication routes (/login, /signup, /logout)
│   ├── user.py                     # User protected routes (/dashboard, /history, /profile)
│   └── admin.py                    # Founder admin routes (/admin/*) with server-side RBAC
│
├── services/
│   ├── resume_parser.py            # PDF/DOCX ingestion & section segmentation
│   ├── skill_extractor.py          # Extensible skill dictionary & regex boundary matching
│   ├── resume_analyzer.py          # 4-factor scoring engine and recommendation logic
│   ├── ai_service.py               # Google Gemini client + deterministic fallback mode
│   ├── resume_generator.py         # Tailored DOCX resume builder
│   └── cover_letter_generator.py   # Formatted PDF cover letter builder
│
├── static/
│   ├── css/
│   │   └── style.css               # HireLens career-tech editorial design system
│   └── js/
│       └── app.js                  # Dropzone, sample data prefill, modal loaders, toggles
│
├── templates/
│   ├── base.html                   # Global layout with HireLens logo & responsive navigation
│   ├── index.html                  # Editorial landing page (hero, preview, 3-step, trust, pricing)
│   ├── analyzer.html               # File dropzone + job description + demo data loader
│   ├── results.html                # 6-step results presentation & ATS diagnostics
│   ├── dashboard.html              # Authenticated candidate dashboard & first-time empty state
│   ├── history.html                # Private paginated resume analysis history
│   ├── profile.html                # User profile management & password update
│   ├── tailored_resume.html        # AI-tailored summary, skills & bullet improvements
│   ├── cover_letter.html           # Letterhead preview & PDF download
│   ├── about.html                  # Venture story, customer segments, privacy policy & terms
│   ├── 404.html & 500.html         # Friendly error pages
│   ├── auth/                       # Login, Signup, Forgot & Reset Password templates
│   └── admin/                      # Founder admin dashboard, users, and analyses templates
│
└── tests/
    ├── test_parser.py              # Tests for document ingestion and text parsing
    ├── test_analyzer.py            # Tests for deterministic skill extraction & scoring
    ├── test_routes.py              # Integration tests for core endpoints and downloads
    └── test_saas.py                # Comprehensive tests for auth, RBAC, admin metrics, & persistence
```

---

## ⚙️ 6. Quick Start & Execution Instructions

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
- If `GEMINI_API_KEY` is omitted, HireLens runs in **Deterministic Demo / Fallback Mode**.
- Set `SECRET_KEY` in production.

### Step 3: Run Automated Test Suite
```bash
pytest
```
*All 38 unit and integration tests will execute and verify authentication, user data isolation, admin metrics, scoring algorithms, and route accessibility.*

### Step 4: Create the Founder Administrator Account
Admin accounts **cannot** be created through public registration. Use the secure CLI command:
```bash
flask create-admin admin@hirelens.local "Founder Admin"
```
*(You will be prompted to enter and confirm the admin password securely).*

### Step 5: Start the Development Server
```bash
python app.py
```
Visit `http://127.0.0.1:5000` in your web browser.

---

## 🔐 7. Admin & User Verification Instructions

### Candidate Account Testing:
1. Navigate to `http://127.0.0.1:5000/signup`.
2. Register a new candidate account (e.g. `alex@example.com`).
3. You will be redirected to the candidate dashboard (`/dashboard`). First-time users see the clean empty state: *"Your next opportunity starts here."*
4. Click **"Start Your First Analysis"** or navigate to `/analyzer`.
5. Click **"Load Sample Data (CS Student + Data Analyst Job)"** and click **"Analyze Resume"**.
6. Review the 6-step results page (`/results`).
7. Check `/history` to confirm your analysis was persisted to the database.

### Founder Admin Portal Testing:
1. Navigate to `http://127.0.0.1:5000/admin/login`.
2. Sign in with your administrator credentials created via `flask create-admin`.
3. View the **Founder Overview** (`/admin/dashboard`) showing live database counts:
   - Total registered candidates
   - New registrations in the last 7 days
   - New registrations in the last 30 days
   - Total analyses conducted
   - Recent registrations table and recent analyses activity
4. Navigate to `/admin/users` to search and audit registered users.
5. Navigate to `/admin/analyses` to review platform comparison records.
6. Verify security: Standard candidate accounts attempting to visit `/admin/dashboard` are immediately denied and redirected.
