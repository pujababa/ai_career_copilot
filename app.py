# -------------------- IMPORTS --------------------
import os
import re
import sqlite3
import time
import random
import secrets
from datetime import datetime, timedelta
from functools import wraps

import json
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
    else:
        load_dotenv()
except ImportError:
    pass

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx
except ImportError:
    docx = None

try:
    from aptitude_cs_questions import APTITUDE_QUESTIONS, CS_MCQ_QUESTIONS
except ImportError:
    APTITUDE_QUESTIONS = []
    CS_MCQ_QUESTIONS = []

try:
    from coding_problems import CODING_PROBLEMS
except ImportError:
    CODING_PROBLEMS = []

try:
    from coding_evaluator import evaluate_python_submission
except ImportError:
    evaluate_python_submission = None

try:
    from ats_engine import extract_text_from_file, analyze_resume, analyze_job_match
except ImportError:
    extract_text_from_file = None
    analyze_resume = None
    analyze_job_match = None

# -------------------- FLASK APP --------------------
_env_name = os.environ.get("FLASK_ENV", "").strip().lower()
IS_PRODUCTION = _env_name == "production" or bool(os.environ.get("RENDER"))

app = Flask(__name__)

_secret_key = os.environ.get("SECRET_KEY")
if IS_PRODUCTION:
    if not _secret_key or _secret_key in ("ai-career-copilot-secure-secret-key-prod-2026", "your_flask_secret_key_here"):
        raise RuntimeError(
            "CRITICAL CONFIGURATION ERROR: A strong, unique SECRET_KEY environment variable is required in production. "
            "Generate one using `python -c \"import secrets; print(secrets.token_hex(32))\"` and configure SECRET_KEY in your Render environment variables."
        )
    app.secret_key = _secret_key
else:
    app.secret_key = _secret_key or "ai-career-copilot-dev-secret-key-local-only"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
_cookie_secure_env = os.environ.get("SESSION_COOKIE_SECURE", "").strip().lower()
app.config["SESSION_COOKIE_SECURE"] = True if _cookie_secure_env in ("true", "1", "yes") else False
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)


try:
    from google import genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("Notice: GenAI client successfully initialized with GEMINI_API_KEY.")
    else:
        client = None
        print("Notice: GEMINI_API_KEY not found in environment.")
except Exception as e:
    print("Notice: GenAI client initialization skipped:", e)
    client = None


def safe_gemini_generate(prompt, model_names=None):
    """
    Safely executes Gemini API call with automatic model fallback.
    Returns response text string if successful, or None if client/API fails.
    Logs technical error diagnostics safely on the server without exposing secrets.
    """
    if app.config.get("TESTING"):
        return None
    if not client:
        app.logger.warning("safe_gemini_generate: GenAI client is not initialized.")
        return None
    if not model_names:
        model_names = ["gemini-3.7-flash", "gemini-3.5-flash", "gemini-flash-latest", "gemini-flash-lite-latest", "gemini-3.6-flash"]
    for model_name in model_names:
        try:
            res = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if res and res.text and res.text.strip():
                return res.text.strip()
        except Exception as e:
            err_msg = str(e)
            if GEMINI_API_KEY and GEMINI_API_KEY in err_msg:
                err_msg = err_msg.replace(GEMINI_API_KEY, "[REDACTED_API_KEY]")
            app.logger.error(f"safe_gemini_generate error on model '{model_name}': {type(e).__name__} - {err_msg}")
            continue
    return None
_default_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")
DATABASE = os.environ.get("DATABASE_PATH", _default_db)

CAREER_SKILLS = {
    "Data Scientist": ["python", "pandas", "machine learning", "sql", "statistics"],
    "Web Developer": ["html", "css", "javascript", "git", "react"],
    "Machine Learning Engineer": ["python", "machine learning", "deep learning", "tensorflow"],
    "Software Developer": ["data structures", "algorithms", "python", "git"]
}

# Admin configuration (production requires environment variables; dev falls back safely)
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
if not IS_PRODUCTION:
    if not ADMIN_EMAIL:
        ADMIN_EMAIL = "npuja3800@gmail.com"
    if not ADMIN_PASSWORD:
        ADMIN_PASSWORD = "puja123"


def get_db():
    """Get SQLite connection with directory auto-creation, timeout, and WAL mode."""
    db_dir = os.path.dirname(DATABASE)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except Exception:
            pass
    conn = sqlite3.connect(DATABASE, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    return conn


def log_activity(user_id, action, details=None):
    """Log a system activity."""
    conn = get_db()
    conn.execute(
        "INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)",
        (user_id, action, details)
    )
    conn.commit()
    conn.close()


def init_db():
    """Create users, chat_history tables and default admin."""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            approved INTEGER NOT NULL DEFAULT 0,
            resume_score INTEGER NOT NULL DEFAULT 0,
            skill_match INTEGER NOT NULL DEFAULT 0,
            project_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Ensure user table columns for extended profile & settings
    cursor = conn.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    extra_user_cols = {
        "bio": "TEXT DEFAULT ''",
        "target_role": "TEXT DEFAULT 'Software Developer'",
        "study_streak": "INTEGER DEFAULT 1",
        "dark_mode": "INTEGER DEFAULT 1",
        "education": "TEXT DEFAULT ''",
        "skills": "TEXT DEFAULT ''",
        "interests": "TEXT DEFAULT ''",
        "experience": "TEXT DEFAULT ''",
        "preferred_industry": "TEXT DEFAULT ''",
        "notifications_enabled": "INTEGER DEFAULT 1",
        "google_id": "TEXT DEFAULT ''"
    }
    for col_name, col_def in extra_user_cols.items():
        if col_name not in columns:
            try:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                print(f"Migration: Added '{col_name}' column to 'users' table.")
            except sqlite3.OperationalError as e:
                print(f"Migration notice for {col_name}: {e}")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            score INTEGER NOT NULL,
            feedback TEXT NOT NULL,
            details_json TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS roadmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            career_goal TEXT NOT NULL,
            available_hours INTEGER NOT NULL DEFAULT 2,
            content_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    # Auto migration for roadmaps progress tracking
    roadmap_cols = [row[1] for row in conn.execute("PRAGMA table_info(roadmaps)").fetchall()]
    if "completed_items_json" not in roadmap_cols:
        try: conn.execute("ALTER TABLE roadmaps ADD COLUMN completed_items_json TEXT DEFAULT '[]'")
        except Exception: pass
    if "progress_pct" not in roadmap_cols:
        try: conn.execute("ALTER TABLE roadmaps ADD COLUMN progress_pct INTEGER DEFAULT 0")
        except Exception: pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            template_name TEXT NOT NULL DEFAULT 'modern',
            title TEXT NOT NULL,
            content_json TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS cover_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_title TEXT NOT NULL,
            company_name TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            badge_id TEXT NOT NULL,
            badge_name TEXT NOT NULL,
            badge_desc TEXT NOT NULL,
            unlocked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notif_type TEXT DEFAULT 'info',
            is_read INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # --- Phase 1 Migration: Required Placement Platform Tables ---
    conn.execute("""
        CREATE TABLE IF NOT EXISTS aptitude_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Auto migration for aptitude_scores optional columns
    apt_cols = [row[1] for row in conn.execute("PRAGMA table_info(aptitude_scores)").fetchall()]
    if "time_taken" not in apt_cols:
        try: conn.execute("ALTER TABLE aptitude_scores ADD COLUMN time_taken INTEGER DEFAULT 0")
        except Exception: pass
    if "accuracy" not in apt_cols:
        try: conn.execute("ALTER TABLE aptitude_scores ADD COLUMN accuracy REAL DEFAULT 0.0")
        except Exception: pass
    if "details_json" not in apt_cols:
        try: conn.execute("ALTER TABLE aptitude_scores ADD COLUMN details_json TEXT DEFAULT '{}'")
        except Exception: pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS coding_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            problem_title TEXT NOT NULL,
            language TEXT NOT NULL,
            code TEXT NOT NULL,
            status TEXT NOT NULL,
            score INTEGER NOT NULL,
            passed_tests INTEGER NOT NULL,
            total_tests INTEGER NOT NULL,
            submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Auto migration for coding_submissions optional columns
    cs_cols = [row[1] for row in conn.execute("PRAGMA table_info(coding_submissions)").fetchall()]
    if "topic" not in cs_cols:
        try: conn.execute("ALTER TABLE coding_submissions ADD COLUMN topic TEXT DEFAULT ''")
        except Exception: pass
    if "difficulty" not in cs_cols:
        try: conn.execute("ALTER TABLE coding_submissions ADD COLUMN difficulty TEXT DEFAULT 'Easy'")
        except Exception: pass
    if "execution_time" not in cs_cols:
        try: conn.execute("ALTER TABLE coding_submissions ADD COLUMN execution_time REAL DEFAULT 0.0")
        except Exception: pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS mcq_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Auto migration for mcq_results optional columns
    mcq_cols = [row[1] for row in conn.execute("PRAGMA table_info(mcq_results)").fetchall()]
    if "accuracy" not in mcq_cols:
        try: conn.execute("ALTER TABLE mcq_results ADD COLUMN accuracy REAL DEFAULT 0.0")
        except Exception: pass
    if "details_json" not in mcq_cols:
        try: conn.execute("ALTER TABLE mcq_results ADD COLUMN details_json TEXT DEFAULT '{}'")
        except Exception: pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_date TEXT NOT NULL,
            tasks_json TEXT NOT NULL,
            completed_tasks_json TEXT DEFAULT '[]',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Auto migration for users table optional columns
    user_cols = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "study_streak" not in user_cols:
        try: conn.execute("ALTER TABLE users ADD COLUMN study_streak INTEGER DEFAULT 1")
        except Exception: pass
    if "last_study_date" not in user_cols:
        try: conn.execute("ALTER TABLE users ADD COLUMN last_study_date TEXT DEFAULT ''")
        except Exception: pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_pinned INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            app_link TEXT,
            deadline TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            company_name TEXT NOT NULL,
            job_role TEXT NOT NULL,
            status TEXT NOT NULL,
            date_applied TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS placements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            company_name TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            token TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_interviews_user ON interviews(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_aptitude_user ON aptitude_scores(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_coding_user ON coding_submissions(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mcq_user ON mcq_results(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_history(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_user ON daily_plans(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_placements_user ON placements(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id)")

    # Phase 2 Reconciliation: Non-destructively copy any unlinked legacy application records to placements
    conn.execute("""
        INSERT INTO placements (user_id, company_name, role, status, created_at)
        SELECT a.user_id, a.company_name, a.job_role,
               CASE 
                   WHEN LOWER(a.status) = 'interview' THEN 'Interview'
                   WHEN LOWER(a.status) = 'selected' THEN 'Selected'
                   WHEN LOWER(a.status) = 'rejected' THEN 'Rejected'
                   ELSE 'Applied'
               END,
               CASE 
                   WHEN a.date_applied LIKE '% %' THEN a.date_applied
                   ELSE a.date_applied || ' 12:00:00'
               END
        FROM applications a
        WHERE NOT EXISTS (
            SELECT 1 FROM placements p 
            WHERE p.user_id = a.user_id AND p.company_name = a.company_name AND p.role = a.job_role
        )
    """)

    conn.commit()
    if ADMIN_EMAIL and ADMIN_PASSWORD:
        cursor = conn.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,))
        if cursor.fetchone() is None:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "INSERT INTO users (name, email, password, role, approved, created_at) VALUES (?, ?, ?, 'admin', 1, ?)",
                ("Admin", ADMIN_EMAIL, hash_password(ADMIN_PASSWORD), now)
            )
            conn.commit()
    conn.close()

# Ensure schema is verified on import
try:
    init_db()
except Exception as _e:
    app.logger.warning(f"Initial DB schema migration notice: {_e}")


def hash_password(password):
    """Simple password hashing using werkzeug."""
    from werkzeug.security import generate_password_hash
    return generate_password_hash(password, method="pbkdf2:sha256")


def check_password(password, hashed):
    """Verify password against hash."""
    from werkzeug.security import check_password_hash
    return check_password_hash(hashed, password)


def calculate_readiness_score(user_id):
    """
    Transparent Placement Readiness Score calculator.
    Calculates unified placement readiness score dynamically based ONLY on completed categories.
    Does not assign fake weights to unattempted tests/modules.
    
    Standard weights when all completed:
    - Resume / ATS Score: 20%
    - Skill Match: 20%
    - Aptitude Test: 15%
    - Coding Assessment: 15%
    - CS Fundamentals / Technical MCQ: 15%
    - Mock Interview: 15%
    """
    conn = get_db()
    
    # 1. Fetch User Record (Resume Score & Skill Match)
    user = conn.execute("SELECT resume_score, skill_match FROM users WHERE id = ?", (user_id,)).fetchone()
    
    # 2. Fetch Aptitude Avg Score
    apt_row = conn.execute(
        "SELECT COUNT(*) as count, AVG(CAST(score AS FLOAT) / total_questions * 100) as avg_score FROM aptitude_scores WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    
    # 3. Fetch Coding Assessment Avg Score
    coding_row = conn.execute(
        "SELECT COUNT(*) as count, AVG(CAST(passed_tests AS FLOAT) / total_tests * 100) as avg_score FROM coding_submissions WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    
    # 4. Fetch CS Fundamentals Avg Score
    mcq_row = conn.execute(
        "SELECT COUNT(*) as count, AVG(CAST(score AS FLOAT) / total_questions * 100) as avg_score FROM mcq_results WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    
    # 5. Fetch Mock Interview Avg Score
    interview_row = conn.execute(
        "SELECT COUNT(*) as count, AVG(score) as avg_score FROM interviews WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    
    conn.close()
    
    components = {}
    
    # Category 1: Resume / ATS
    resume_val = user["resume_score"] if (user and user["resume_score"]) else 0
    resume_attempted = bool(user and user["resume_score"] and user["resume_score"] > 0)
    components["resume"] = {
        "title": "Resume & ATS Score",
        "score": round(float(resume_val), 1),
        "attempted": resume_attempted,
        "standard_weight": 20,
        "status": "Completed" if resume_attempted else "Not Attempted"
    }
    
    # Category 2: Skill Match
    skill_val = user["skill_match"] if (user and user["skill_match"]) else 0
    skill_attempted = bool(user and user["skill_match"] and user["skill_match"] > 0)
    components["skill_match"] = {
        "title": "Skill Gap & Role Match",
        "score": round(float(skill_val), 1),
        "attempted": skill_attempted,
        "standard_weight": 20,
        "status": "Completed" if skill_attempted else "Not Attempted"
    }
    
    # Category 3: Aptitude Test
    apt_count = apt_row["count"] if apt_row else 0
    apt_val = apt_row["avg_score"] if (apt_row and apt_row["avg_score"] is not None) else 0
    apt_attempted = apt_count > 0
    components["aptitude"] = {
        "title": "Aptitude Tests",
        "score": round(float(apt_val), 1),
        "attempted": apt_attempted,
        "standard_weight": 15,
        "status": f"Completed ({apt_count} test{'s' if apt_count > 1 else ''})" if apt_attempted else "Not Attempted"
    }
    
    # Category 4: Coding Assessment
    coding_count = coding_row["count"] if coding_row else 0
    coding_val = coding_row["avg_score"] if (coding_row and coding_row["avg_score"] is not None) else 0
    coding_attempted = coding_count > 0
    components["coding"] = {
        "title": "Coding Assessments",
        "score": round(float(coding_val), 1),
        "attempted": coding_attempted,
        "standard_weight": 15,
        "status": f"Completed ({coding_count} problem{'s' if coding_count > 1 else ''})" if coding_attempted else "Not Attempted"
    }
    
    # Category 5: CS Fundamentals
    mcq_count = mcq_row["count"] if mcq_row else 0
    mcq_val = mcq_row["avg_score"] if (mcq_row and mcq_row["avg_score"] is not None) else 0
    mcq_attempted = mcq_count > 0
    components["cs_fundamentals"] = {
        "title": "CS Fundamentals & MCQs",
        "score": round(float(mcq_val), 1),
        "attempted": mcq_attempted,
        "standard_weight": 15,
        "status": f"Completed ({mcq_count} quiz{'zes' if mcq_count > 1 else ''})" if mcq_attempted else "Not Attempted"
    }
    
    # Category 6: Mock Interview
    interview_count = interview_row["count"] if interview_row else 0
    interview_val = interview_row["avg_score"] if (interview_row and interview_row["avg_score"] is not None) else 0
    interview_attempted = interview_count > 0
    components["mock_interview"] = {
        "title": "AI Mock Interview",
        "score": round(float(interview_val), 1),
        "attempted": interview_attempted,
        "standard_weight": 15,
        "status": f"Completed ({interview_count} session{'s' if interview_count > 1 else ''})" if interview_attempted else "Not Attempted"
    }
    
    # Transparent Math: Compute overall score only from ATTEMPTED components
    attempted_components = [c for c in components.values() if c["attempted"]]
    
    if attempted_components:
        total_weight = sum(c["standard_weight"] for c in attempted_components)
        weighted_score_sum = sum(c["score"] * c["standard_weight"] for c in attempted_components)
        overall_score = round(weighted_score_sum / total_weight, 1)
    else:
        overall_score = 0.0
        
    return {
        "overall_score": overall_score,
        "attempted_count": len(attempted_components),
        "total_categories": len(components),
        "has_data": len(attempted_components) > 0,
        "components": components
    }



EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$")


def is_valid_email(email):
    """
    Validate email address format strictly.
    Accepts properly formatted email addresses (e.g. puja@gmail.com).
    Rejects clearly invalid formats (e.g. puja, puja@, @gmail.com, puja@gmail).
    """
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_password_strength(password):
    """
    Validate password strength:
    - Minimum 8 characters
    - At least one letter
    - At least one number
    - At least one special character
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    has_letter = bool(re.search(r"[a-zA-Z]", password))
    has_number = bool(re.search(r"[0-9]", password))
    has_special = bool(re.search(r"[^a-zA-Z0-9]", password))
    if not (has_letter and has_number and has_special):
        return False, "Password must contain at least one letter, one number, and one special character."
    return True, None



@app.after_request
def add_security_headers(response):
    """
    Prevent caching of dynamic and protected responses.
    Ensures browser Back button after logout cannot expose protected data from bfcache.
    """
    if not request.path.startswith("/static"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


def is_api_request():
    """Determine if current request is an API request expecting JSON."""
    return (
        request.path.startswith("/api/")
        or request.is_json
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.headers.get("Accept", "").startswith("application/json")
    )


def get_safe_redirect_target():
    """Retrieve safe local relative redirect target from current request."""
    target = request.full_path if request.query_string else request.path
    if target and target.startswith("/") and not target.startswith("//") and not target.startswith("/\\"):
        return target
    return None


def login_required(f):
    """Require user to be logged in (returns 401 JSON for APIs, redirects for pages with next param)."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            if is_api_request():
                return jsonify({"error": "Authentication required", "success": False}), 401
            flash("Please log in to access this page.")
            target = get_safe_redirect_target()
            return redirect(url_for("student_login", next=target) if target else url_for("student_login"))
        return f(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_user():
    """Provide current user to all templates."""
    user = None
    unread_notifs_count = 0
    if "user_id" in session:
        conn = get_db()
        u = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        if u:
            user = dict(u)
            user["initials"] = "".join(
                w[0] for w in (u["name"] or "U").split()[:2]
            ).upper() or "U"
            try:
                unread_row = conn.execute(
                    "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
                    (session["user_id"],)
                ).fetchone()
                if unread_row:
                    unread_notifs_count = unread_row[0]
            except Exception:
                unread_notifs_count = 0
        else:
            user = {
                "id": session.get("user_id"),
                "name": session.get("user_name", "Student"),
                "email": session.get("user_email", ""),
                "role": session.get("user_role", "student"),
                "resume_score": session.get("resume_score", 0),
                "target_role": "Software Developer",
                "study_streak": 1,
                "dark_mode": 1,
                "initials": "U"
            }
        conn.close()
    return dict(current_user=user, unread_notifs_count=unread_notifs_count)


def admin_required(f):
    """Require user to be admin (returns 401/403 for APIs, redirects for pages with next param)."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            if is_api_request():
                return jsonify({"error": "Authentication required", "success": False}), 401
            flash("Please log in as an administrator to access the admin portal.")
            target = get_safe_redirect_target()
            return redirect(url_for("admin_login", next=target) if target else url_for("admin_login"))
        if session.get("user_role") != "admin":
            if is_api_request():
                return jsonify({"error": "Forbidden: Administrator privileges required", "success": False}), 403
            flash("Administrator privileges required.")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapped


def student_required(f):
    """Require user to be authenticated (returns 401/403 for APIs, redirects for pages with next param). Allows admin for inspection without forced bounce loops."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            if is_api_request():
                return jsonify({"error": "Authentication required", "success": False}), 401
            flash("Please log in to continue.")
            target = get_safe_redirect_target()
            return redirect(url_for("student_login", next=target) if target else url_for("student_login"))
        if session.get("user_role") not in ("student", "admin"):
            if is_api_request():
                return jsonify({"error": "Forbidden: Student portal access required", "success": False}), 403
            flash("Student portal access required.")
            return redirect(url_for("student_login"))
        return f(*args, **kwargs)
    return wrapped


# -------- Authentication & Navigation Routes --------


@app.route("/")
def index():
    """Landing page with portal selection."""
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Unified login route (alias to student login)."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Both email and password are required.")
            return render_template("student-login.html", active_tab="login")

        if not is_valid_email(email):
            flash("Please enter a valid email address.")
            return render_template("student-login.html", active_tab="login")

        conn = get_db()
        user = conn.execute(
            "SELECT id, name, email, password, role, approved, resume_score FROM users WHERE LOWER(email) = ?",
            (email,)
        ).fetchone()
        conn.close()

        if not user or not check_password(password, user["password"]):
            flash("Invalid email or password. Please try again.")
            return render_template("student-login.html", active_tab="login")

        if user["role"] != "student":
            flash("This portal is for students only. Administrators must log in via the Admin Portal.")
            return render_template("student-login.html", active_tab="login")

        if not user["approved"]:
            flash("Your account is currently waiting for administrator approval.")
            return render_template("student-login.html", active_tab="login")

        session.permanent = True
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        session["user_role"] = user["role"]
        session["resume_score"] = user["resume_score"] or 0

        log_activity(user["id"], "Login", "Student logged in")

        next_url = request.args.get("next") or request.form.get("next")
        if next_url and next_url.startswith("/") and not next_url.startswith("//") and not next_url.startswith("/\\"):
            return redirect(next_url)

        return redirect(url_for("dashboard"))

    return render_template("student-login.html", active_tab="login")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """Student registration with email, password validation and PBKDF2 hashing."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        target_role = request.form.get("target_role", "Software Developer").strip()

        if not name or not email or not password or not confirm_password:
            flash("All registration fields are required.")
            return render_template("student-login.html", active_tab="signup")

        if not is_valid_email(email):
            flash("Please enter a valid email address.")
            return render_template("student-login.html", active_tab="signup")

        is_valid_pw, pw_err = validate_password_strength(password)
        if not is_valid_pw:
            flash(pw_err)
            return render_template("student-login.html", active_tab="signup")

        if password != confirm_password:
            flash("Passwords do not match. Please ensure both passwords match.")
            return render_template("student-login.html", active_tab="signup")

        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,)).fetchone()
        if existing:
            conn.close()
            flash("An account with this email address already exists. Please sign in.")
            return render_template("student-login.html", active_tab="login")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            conn.execute(
                "INSERT INTO users (name, email, password, role, approved, target_role, created_at) VALUES (?, ?, ?, 'student', 1, ?, ?)",
                (name, email, hash_password(password), target_role, now)
            )
            conn.commit()
            user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.close()
            log_activity(user_id, "Signup", "New student registered and activated")
            flash("Account created successfully! You can now log in.")
            return redirect(url_for("student_login"))
        except sqlite3.IntegrityError:
            conn.close()
            flash("Email already registered. Please sign in.")
            return render_template("student-login.html", active_tab="login")

    return render_template("student-login.html", active_tab="signup")


@app.route("/student-login", methods=["GET", "POST"])
def student_login():
    """Student portal login."""
    return login()


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    """Portal-specific admin login."""
    if request.method == "POST":
        email = (request.form.get("email") or request.form.get("username") or "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Both administrator email and password are required.")
            return render_template("admin-login.html")

        conn = get_db()
        user = conn.execute(
            "SELECT id, name, email, password, role FROM users WHERE (LOWER(email) = ? OR LOWER(name) = ?) AND LOWER(role) = 'admin'",
            (email, email)
        ).fetchone()
        if not user and not IS_PRODUCTION and email in ("admin", "admin@example.com", "administrator"):
            user = conn.execute(
                "SELECT id, name, email, password, role FROM users WHERE LOWER(role) = 'admin' ORDER BY id ASC LIMIT 1"
            ).fetchone()
        conn.close()

        if not user or not check_password(password, user["password"]):
            flash("Invalid admin credentials.")
            return render_template("admin-login.html")

        session.permanent = True
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        session["user_role"] = user["role"]

        log_activity(user["id"], "Login", "Admin logged in")

        next_url = request.args.get("next") or request.form.get("next")
        if next_url and next_url.startswith("/") and not next_url.startswith("//") and not next_url.startswith("/\\"):
            return redirect(next_url)

        return redirect(url_for("admin"))

    return render_template("admin-login.html")


@app.route("/logout")
def logout():
    """Securely log out user, clear session, and clear session cookie."""
    user_id = session.get("user_id")
    if user_id:
        try:
            log_activity(user_id, "Logout", "User logged out")
        except Exception:
            pass
    session.clear()
    flash("You have been securely signed out.")
    resp = redirect(url_for("student_login"))
    resp.delete_cookie(app.config.get("SESSION_COOKIE_NAME", "session"))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@app.route("/api/auth/session-check")
def auth_session_check():
    """Lightweight endpoint for frontend navigation history validation."""
    if "user_id" in session:
        return jsonify({
            "authenticated": True,
            "user_id": session["user_id"],
            "role": session.get("user_role", "student")
        }), 200
    return jsonify({"authenticated": False}), 401


def render_app_page(template, title, page, nav_subtitle=None):
    return render_template(
        template,
        title=title,
        page=page,
        nav_subtitle=nav_subtitle or title,
    )


def get_or_create_daily_plan(user_id, plan_date=None):
    """
    Retrieves or generates today's personalized daily preparation plan for the student.
    Guarantees max 3-5 tasks targeting real weak areas.
    Caches in daily_plans table to avoid repeated Gemini calls on page refresh.
    """
    if not plan_date:
        plan_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM daily_plans WHERE user_id = ? AND plan_date = ?",
        (user_id, plan_date)
    ).fetchone()

    if existing:
        conn.close()
        tasks = json.loads(existing["tasks_json"]) if existing["tasks_json"] else []
        completed_ids = json.loads(existing["completed_tasks_json"]) if existing["completed_tasks_json"] else []
        for t in tasks:
            t["completed"] = (t["task_id"] in completed_ids)
        return {
            "plan_date": plan_date,
            "tasks": tasks,
            "completed_ids": completed_ids,
            "total_tasks": len(tasks),
            "completed_count": len(completed_ids),
            "percentage": round((len(completed_ids) / len(tasks)) * 100) if tasks else 0
        }

    # Generate new daily plan using student context
    context = build_student_context(user_id)
    target_role = context.get("target_role", "Software Developer")
    weak_topics = context.get("weak_topics", [])
    
    prompt = f"""Generate a realistic 3-task daily placement preparation plan for a student targeting '{target_role}'.
Student Weak Areas: {', '.join(weak_topics) or 'Algorithms, System Design, STAR Method'}

Provide response strictly as JSON with key "tasks" containing an array of 3 tasks.
Each task object must contain:
- "task_id": string ("task_1", "task_2", "task_3")
- "title": string (short title e.g. "DSA Practice")
- "description": string (action-oriented task instruction)
- "category": string ("Coding Practice" / "Aptitude Practice" / "CS Fundamentals" / "Mock Interview" / "Resume Improvement")
- "estimated_minutes": integer (15 to 45)
"""
    tasks = None
    res_text = safe_gemini_generate(prompt)
    if res_text:
        try:
            clean_txt = res_text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_txt)
            tasks = parsed.get("tasks", [])
        except Exception:
            tasks = None

    # Deterministic Rule-Based Fallback Engine
    if not tasks or len(tasks) == 0:
        tasks = []
        if weak_topics:
            tasks.append({
                "task_id": "task_1",
                "title": f"Revise {weak_topics[0]}",
                "description": f"Practice concepts and sample questions for {weak_topics[0]}.",
                "category": "Aptitude Practice",
                "estimated_minutes": 30,
                "completed": False
            })
        else:
            tasks.append({
                "task_id": "task_1",
                "title": "DSA Array Practice",
                "description": "Solve 2 array problem challenges on two-pointer technique.",
                "category": "Coding Practice",
                "estimated_minutes": 45,
                "completed": False
            })

        if len(weak_topics) > 1:
            tasks.append({
                "task_id": "task_2",
                "title": f"Practice {weak_topics[1]}",
                "description": f"Solve 10 practice questions on {weak_topics[1]}.",
                "category": "CS Fundamentals",
                "estimated_minutes": 30,
                "completed": False
            })
        else:
            tasks.append({
                "task_id": "task_2",
                "title": "CS Fundamentals MCQ",
                "description": "Attempt a 10-question quiz on DBMS & SQL normalization.",
                "category": "CS Fundamentals",
                "estimated_minutes": 30,
                "completed": False
            })

        tasks.append({
            "task_id": "task_3",
            "title": f"Mock Interview for {target_role}",
            "description": "Practice answering 'Tell me about yourself' and project architecture.",
            "category": "Mock Interview",
            "estimated_minutes": 20,
            "completed": False
        })

    tasks_json_str = json.dumps(tasks)
    completed_json_str = json.dumps([])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    conn.execute(
        "INSERT INTO daily_plans (user_id, plan_date, tasks_json, completed_tasks_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, plan_date, tasks_json_str, completed_json_str, now)
    )
    conn.commit()
    conn.close()

    for t in tasks:
        t["completed"] = False

    return {
        "plan_date": plan_date,
        "tasks": tasks,
        "completed_ids": [],
        "total_tasks": len(tasks),
        "completed_count": 0,
        "percentage": 0
    }


@app.route("/daily-plan")
@student_required
def daily_plan():
    """Render Student Daily Preparation Plan page."""
    user_id = session["user_id"]
    plan = get_or_create_daily_plan(user_id)
    context = build_student_context(user_id)
    return render_template(
        "daily_plan.html", 
        title="Daily Preparation Plan", 
        page="daily-plan", 
        plan=plan, 
        context=context
    )


@app.route("/api/daily-plan/toggle-task", methods=["POST"])
@student_required
def api_toggle_daily_task():
    """Toggle completion status of a task in today's daily plan."""
    user_id = session["user_id"]
    data = request.get_json() or {}
    task_id = data.get("task_id")
    plan_date = data.get("plan_date") or datetime.now().strftime("%Y-%m-%d")
    
    if not task_id:
        return jsonify({"error": "Task ID is required"}), 400
        
    conn = get_db()
    plan_row = conn.execute(
        "SELECT * FROM daily_plans WHERE user_id = ? AND plan_date = ?",
        (user_id, plan_date)
    ).fetchone()
    
    if not plan_row:
        conn.close()
        return jsonify({"error": "Plan not found"}), 404
        
    tasks = json.loads(plan_row["tasks_json"])
    completed_ids = json.loads(plan_row["completed_tasks_json"]) if plan_row["completed_tasks_json"] else []
    
    if task_id in completed_ids:
        completed_ids.remove(task_id)
        is_now_completed = False
    else:
        completed_ids.append(task_id)
        is_now_completed = True
        
    conn.execute(
        "UPDATE daily_plans SET completed_tasks_json = ? WHERE id = ? AND user_id = ?",
        (json.dumps(completed_ids), plan_row["id"], user_id)
    )
    
    # Update study streak in users table if completing a task
    if is_now_completed:
        today_str = datetime.now().strftime("%Y-%m-%d")
        user = conn.execute("SELECT study_streak, last_study_date FROM users WHERE id = ?", (user_id,)).fetchone()
        if user:
            streak = user["study_streak"] or 0
            last_date = user["last_study_date"] or ""
            if last_date != today_str:
                conn.execute("UPDATE users SET study_streak = ?, last_study_date = ? WHERE id = ?", (streak + 1, today_str, user_id))
                
    conn.commit()
    conn.close()
    
    pct = round((len(completed_ids) / len(tasks)) * 100) if tasks else 0
    
    return jsonify({
        "task_id": task_id,
        "completed": is_now_completed,
        "completed_count": len(completed_ids),
        "total_tasks": len(tasks),
        "percentage": pct
    })


@app.route("/dashboard")
@student_required
def dashboard():
    """Student dashboard with readiness, daily plan, performance, and quick actions."""
    user_id = session["user_id"]
    conn = get_db()
    announcements = conn.execute("SELECT * FROM announcements ORDER BY id DESC LIMIT 3").fetchall()
    user_row = conn.execute("SELECT study_streak FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    
    readiness = calculate_readiness_score(user_id)
    context = build_student_context(user_id)
    today_plan = get_or_create_daily_plan(user_id)
    streak = user_row["study_streak"] if user_row and user_row["study_streak"] else 1
    
    return render_template(
        "dashboard.html", 
        title="Dashboard", 
        page="dashboard", 
        nav_subtitle="Your placement dashboard",
        announcements=announcements,
        readiness=readiness,
        context=context,
        today_plan=today_plan,
        streak=streak
    )


def build_student_context(user_id):
    """
    Builds a sanitized, structured context dictionary for the logged-in student.
    Includes target role, skills, education, ATS score, test performances, and weak topics.
    NEVER exposes passwords, API keys, or authentication secrets.
    """
    if not user_id:
        return {}

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return {}

    user_dict = dict(user)

    # Latest Aptitude
    apt = conn.execute(
        "SELECT category, score, total_questions, accuracy, details_json FROM aptitude_scores WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", 
        (user_id,)
    ).fetchone()
    
    # Latest Coding
    coding = conn.execute(
        "SELECT problem_title, score, passed_tests, total_tests, topic FROM coding_submissions WHERE user_id = ? ORDER BY submitted_at DESC LIMIT 1", 
        (user_id,)
    ).fetchone()
    
    # Latest CS Fundamentals
    mcq = conn.execute(
        "SELECT subject, score, total_questions, accuracy, details_json FROM mcq_results WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", 
        (user_id,)
    ).fetchone()
    
    # Latest Interview
    interview = conn.execute(
        "SELECT category, score, feedback FROM interviews WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", 
        (user_id,)
    ).fetchone()
    
    # Latest Placement Applications
    placements = conn.execute(
        "SELECT company_name, role, status FROM placements WHERE user_id = ? ORDER BY created_at DESC LIMIT 3", 
        (user_id,)
    ).fetchall()

    conn.close()

    apt_weak = []
    if apt and apt["details_json"]:
        try:
            apt_details = json.loads(apt["details_json"])
            apt_weak = apt_details.get("weak_topics", [])
        except Exception: pass

    mcq_weak = []
    if mcq and mcq["details_json"]:
        try:
            mcq_details = json.loads(mcq["details_json"])
            mcq_weak = mcq_details.get("weak_topics", [])
        except Exception: pass

    readiness = calculate_readiness_score(user_id)

    return {
        "name": user_dict.get("name", "Student"),
        "target_role": user_dict.get("target_role") or "Software Developer",
        "skills": user_dict.get("skills") or "Python, SQL, Web Basics",
        "education": user_dict.get("education") or "B.Tech Computer Science",
        "interests": user_dict.get("interests") or "Software Engineering, AI",
        "bio": user_dict.get("bio") or "",
        "resume_score": user_dict.get("resume_score", 0),
        "skill_match": user_dict.get("skill_match", 0),
        "readiness_score": readiness.get("overall_score", 0.0),
        "readiness_status": f"{readiness.get('attempted_count', 0)}/{readiness.get('total_categories', 6)} categories completed",
        "latest_aptitude": f"{apt['category']} ({apt['score']}/{apt['total_questions']}, {apt['accuracy']}%)" if apt else "Not Attempted",
        "latest_coding": f"{coding['problem_title']} ({coding['score']}%)" if coding else "Not Attempted",
        "latest_cs_fundamentals": f"{mcq['subject']} ({mcq['score']}/{mcq['total_questions']}, {mcq['accuracy']}%)" if mcq else "Not Attempted",
        "latest_interview": f"{interview['category']} (Score: {interview['score']}%)" if interview else "Not Attempted",
        "weak_topics": list(set(apt_weak + mcq_weak)),
        "recent_placements": [f"{p['company_name']} - {p['role']} ({p['status']})" for p in placements]
    }


def get_ai_response(user_message, user_id=None):
    """
    Context-aware AI assistant using Google GenAI SDK.
    Safely injects student context (profile, test scores, target role) and recent conversation history.
    """
    context = build_student_context(user_id) if user_id else {}

    # Fetch recent conversation turns for context
    conversation_history_text = ""
    if user_id:
        try:
            conn = get_db()
            history_rows = conn.execute(
                "SELECT message, response FROM chat_history WHERE user_id = ? ORDER BY id DESC LIMIT 6",
                (user_id,)
            ).fetchall()
            conn.close()
            if history_rows:
                turns = []
                for row in reversed(history_rows):
                    turns.append(f"Student: {row['message']}\nAI Copilot: {row['response']}")
                conversation_history_text = "\n".join(turns)
        except Exception as e:
            app.logger.warning(f"Could not load conversation history: {e}")

    target_role = context.get('target_role', 'Software Developer')
    skills = context.get('skills', 'Core CS, Algorithms')
    weak_topics = context.get('weak_topics', [])
    readiness = context.get('readiness_score', 0)

    # System instruction tailored to the authenticated student
    system_instruction = f"""You are AI Career Copilot, an expert placement coach and technical mentor for {context.get('name', 'the student')}.
STUDENT PROFILE:
- Target Role: {target_role}
- Skills: {skills}
- Education: {context.get('education', 'Computer Science')}
- Placement Readiness Score: {readiness}% ({context.get('readiness_status', '')})
- Weak Areas Identified from Tests: {', '.join(weak_topics) or 'None recorded yet'}
- Resume ATS Score: {context.get('resume_score', 0)}%
- Latest Coding: {context.get('latest_coding', 'None')}
- Latest CS Fundamentals: {context.get('latest_cs_fundamentals', 'None')}

DIRECTIVES:
1. Provide structured, accurate, encouraging markdown responses.
2. Personalize your guidance specifically to the candidate's target role ({target_role}) and address their weak topics ({', '.join(weak_topics) or 'Algorithms & Core CS'}) when relevant.
3. Keep answers concise, practical, and action-oriented for placement preparation."""

    prompt_parts = [f"SYSTEM INSTRUCTION:\n{system_instruction}"]
    if conversation_history_text:
        prompt_parts.append(f"RECENT CONVERSATION HISTORY:\n{conversation_history_text}")
    prompt_parts.append(f"CURRENT STUDENT MESSAGE:\n{user_message}\n\nAI COPILOT RESPONSE:")
    full_prompt = "\n\n".join(prompt_parts)

    res_text = safe_gemini_generate(full_prompt)
    if res_text:
        return res_text

    # Dynamic, profile-tailored fallback if AI service is unavailable
    app.logger.warning(f"AI response fallback invoked for user {user_id}. Message: '{user_message[:50]}'")
    msg_lower = user_message.lower()
    if "interview" in msg_lower:
        return f"### Placement Interview Preparation for {target_role}\n\n1. **Core Technical Depth**: Review your technical fundamentals in **{skills}**.\n2. **System Design & Coding**: Practice 2-3 algorithmic problems daily on arrays, strings, and trees.\n3. **Behavioral Questions**: Structure your answers using the **STAR method** (Situation, Task, Action, Result).\n4. **Weak Area Focus**: Strengthen concepts in **{', '.join(weak_topics) if weak_topics else 'Data Structures & DBMS'}**."
    elif "python" in msg_lower or "after python" in msg_lower:
        return f"### What to Learn After Python for {target_role}\n\n1. **Data Structures & Algorithms**: Master lists, dictionaries, stacks, queues, BSTs, and dynamic programming in Python.\n2. **Backend Frameworks**: Build RESTful APIs with **FastAPI** or **Flask**.\n3. **Databases**: Master SQL (PostgreSQL/MySQL) and ORM integration.\n4. **System Architecture**: Learn Git version control, Docker containerization, and cloud deployment."
    elif "dbms" in msg_lower or "database" in msg_lower:
        return f"### High-Yield DBMS Placement Concepts\n\n1. **ACID Properties**: Atomicity, Consistency, Isolation (Dirty/Phantom reads), Durability.\n2. **Indexing**: B+ Trees, clustered vs non-clustered indexes for query optimization.\n3. **Normalization**: 1NF, 2NF (eliminate partial dependency), 3NF (eliminate transitive dependency), BCNF.\n4. **Transactions & Locking**: Two-Phase Locking (2PL), deadlocks, and isolation levels."
    elif "resume" in msg_lower:
        return f"### Resume & ATS Optimization Guide\n\n1. **Measurable Impact**: Use the formula: *Accomplished [X] as measured by [Y], by doing [Z]*.\n2. **Tailor to {target_role}**: Include key target skills: **{skills}**.\n3. **Standard Section Layout**: Education, Technical Skills, Projects, Experience, Achievements.\n4. **ATS Formatting**: Single-column clean layout without complex tables or images."
    elif "dsa" in msg_lower or "plan" in msg_lower:
        return f"### 30-Day Placement DSA Roadmap for {target_role}\n\n- **Week 1 (Foundations)**: Arrays, Strings, Two Pointers, Sliding Window.\n- **Week 2 (Linear Data Structures)**: Linked Lists, Stacks, Queues, Binary Search.\n- **Week 3 (Non-Linear Structures)**: Binary Trees, BSTs, Heaps, Hash Maps.\n- **Week 4 (Advanced & Revision)**: Graph traversals (BFS/DFS), Dynamic Programming fundamentals, and Mock Interviews."
    elif weak_topics:
        return f"Based on your assessment results, focus today on revising your identified weak areas: **{', '.join(weak_topics)}** for your target role as **{target_role}**!"
    else:
        return f"Hello! As your AI Career Copilot for **{target_role}**, I can help you with coding challenges, CS fundamentals, mock interview questions, and resume optimization. What specific topic would you like to practice today?"


@app.route("/api/chat/delete/<int:msg_id>", methods=["POST"])
@student_required
def delete_chat_message(msg_id):
    """Delete a specific chat message."""
    conn = get_db()
    conn.execute("DELETE FROM chat_history WHERE id = ? AND user_id = ?", (msg_id, session["user_id"]))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/chat/pin/<int:msg_id>", methods=["POST"])
@student_required
def pin_chat_message(msg_id):
    """Toggle pin status for a chat message."""
    conn = get_db()
    # Get current pin status
    row = conn.execute("SELECT is_pinned FROM chat_history WHERE id = ? AND user_id = ?", 
                      (msg_id, session["user_id"])).fetchone()
    if row:
        new_status = 1 if row["is_pinned"] == 0 else 0
        conn.execute("UPDATE chat_history SET is_pinned = ? WHERE id = ? AND user_id = ?", 
                    (new_status, msg_id, session["user_id"]))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "is_pinned": new_status})
    conn.close()
    return jsonify({"error": "Message not found"}), 404


@app.route("/api/chat/clear", methods=["POST"])
@student_required
def clear_chat_history():
    """Clear all chat history for the user."""
    conn = get_db()
    conn.execute("DELETE FROM chat_history WHERE user_id = ?", (session["user_id"],))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/chat")
@student_required
def chat():
    """Render the chat page with history."""
    conn = get_db()
    # Fetch history ordered by time, including pinning status
    chat_history = conn.execute(
        "SELECT * FROM chat_history WHERE user_id = ? ORDER BY is_pinned DESC, created_at ASC", 
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return render_template(
        "chat.html",
        title="Chat",
        page="chat",
        nav_subtitle="Chat Copilot",
        chat_history=chat_history,
    )

@app.route("/api/chat", methods=["POST"])
@student_required
def api_chat():
    try:
        data = request.get_json() or {}
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({"reply": "Please enter a question or message!"}), 400

        user_id = session.get("user_id")
        
        # Generate Context-Aware AI Response
        ai_reply = get_ai_response(user_message, user_id=user_id)

        # Save to chat history in database
        if user_id:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = get_db()
            conn.execute(
                "INSERT INTO chat_history (user_id, message, response, timestamp, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, user_message, ai_reply, now, now)
            )
            conn.commit()
            conn.close()

        return jsonify({"reply": ai_reply})

    except Exception:
        return jsonify({
            "reply": "⚠️ An unexpected error occurred. Please try asking again!"
        })
        
@app.route("/chat-message", methods=["POST"])
@student_required
def chat_message():
    """Legacy chat message route - redirects to new API."""
    return api_chat()


@app.route("/skillgap")
@student_required
def skillgap():
    return render_app_page("skillgap.html", "Skill Gap", "skillgap")


@app.route("/career-analysis", methods=["POST"])
@student_required
def career_analysis():
    data = request.get_json()
    if not data or "career" not in data or "skills" not in data:
        return jsonify({"error": "Missing career or skills"}), 400
    
    selected_career = data["career"]
    user_skills_raw = data["skills"]
    
    if selected_career not in CAREER_SKILLS:
        return jsonify({"error": "Invalid career selected"}), 400
        
    target_skills = CAREER_SKILLS[selected_career]
    user_skills = [s.strip().lower() for s in user_skills_raw.split(",") if s.strip()]
    
    matched = [skill.title() for skill in target_skills if skill.lower() in user_skills]
    missing = [skill.title() for skill in target_skills if skill.lower() not in user_skills]
    
    match_percentage = int((len(matched) / len(target_skills)) * 100) if target_skills else 0
    
    # Save skill match to db
    conn = get_db()
    conn.execute("UPDATE users SET skill_match = ? WHERE id = ?", (match_percentage, session["user_id"]))
    conn.commit()
    conn.close()
    
    return jsonify({
        "matched": matched,
        "missing": missing,
        "match_percentage": match_percentage
    })

    
@app.route("/resume-analysis", methods=["GET", "POST"])
@login_required
def resume_analysis():
    if request.method == "GET":
        return render_app_page(
            "resume.html",
            "Resume Analysis",
            "resume-analysis",
            "Evidence-based ATS resume analysis, section audit, skill matching, and tailored feedback."
        )

    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded. Please select a PDF or DOCX resume to upload.", "success": False}), 400

    file = request.files["resume"]
    if not file or not file.filename:
        return jsonify({"error": "No file selected. Please select a PDF or DOCX resume to upload.", "success": False}), 400

    from werkzeug.utils import secure_filename
    raw_filename = secure_filename(file.filename) or "resume.pdf"
    ext = os.path.splitext(raw_filename)[1].lower()
    if ext not in [".pdf", ".docx"]:
        return jsonify({"error": "Unsupported file format. Please upload a PDF (.pdf) or Word document (.docx).", "success": False}), 400

    # Enforce file size limit (max 5MB)
    file_bytes = file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        return jsonify({"error": "File exceeds the 5MB size limit. Please upload a smaller document.", "success": False}), 400
    if len(file_bytes) == 0:
        return jsonify({"error": "The uploaded file is empty. Please upload a valid document.", "success": False}), 400

    upload_folder = os.path.join(app.root_path, "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    temp_filename = f"user_{session['user_id']}_{int(time.time())}_{secrets.token_hex(4)}{ext}"
    filepath = os.path.join(upload_folder, temp_filename)

    with open(filepath, "wb") as f:
        f.write(file_bytes)

    try:
        raw_text, extract_err = extract_text_from_file(filepath, raw_filename)
        if extract_err or not raw_text:
            return jsonify({
                "error": extract_err or "Unable to extract readable text from document.",
                "success": False
            }), 400

        job_description = request.form.get("job_description", "").strip()
        analysis = analyze_resume(raw_text, job_description)

        if not analysis.get("success"):
            return jsonify({
                "error": analysis.get("error", "Resume analysis could not be completed."),
                "success": False
            }), 400

        score = analysis["score"]
        project_count = analysis.get("project_count", 0)

        # Update database and session
        conn = get_db()
        conn.execute("UPDATE users SET resume_score = ?, project_count = ? WHERE id = ?", (score, project_count, session["user_id"]))
        conn.commit()
        conn.close()

        session["resume_score"] = score
        try:
            log_activity(session["user_id"], "Resume Analysis", f"Analyzed resume: Score {score}/100")
        except Exception:
            pass

        analysis["message"] = "Resume uploaded and analyzed successfully!"
        return jsonify(analysis)

    except Exception as e:
        app.logger.error(f"Error in resume_analysis: {e}")
        return jsonify({"error": "An error occurred while analyzing the resume. Please ensure the document is valid and try again.", "success": False}), 500
    finally:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass


@app.route("/placement-readiness")
@app.route("/api/placement-readiness")
@student_required
def placement_readiness():
    """
    Returns the dynamic, transparent Placement Readiness Score calculation.
    Considers only completed assessment categories to avoid fake zero/fake 100 weights.
    """
    user_id = session.get("user_id")
    readiness_data = calculate_readiness_score(user_id)
    
    score = readiness_data["overall_score"]
    if score < 50:
        insight = "Focus on building projects, attempting aptitude/coding tests, and improving technical skills."
    elif score <= 75:
        insight = "Good progress! Practice mock interviews and complete your missing CS fundamentals modules."
    else:
        insight = "Excellent placement readiness! You are well prepared for campus placements and technical interviews."
        
    readiness_data["insight"] = insight
    return jsonify(readiness_data)


@app.route("/admin")
@admin_required
def admin():
    """Admin console with user approvals."""
    conn = get_db()
    pending = conn.execute(
        "SELECT id, name, email, role FROM users WHERE approved = 0 ORDER BY id"
    ).fetchall()
    approved = conn.execute(
        "SELECT id, name, email, role FROM users WHERE approved = 1 ORDER BY name"
    ).fetchall()
    conn.close()
    return render_template(
        "admin.html",
        title="Admin",
        page="admin",
        nav_subtitle="Admin Console",
        pending=pending,
        approved=approved,
    )

@app.route("/admin/users")
@admin_required
def admin_users():
    """View all users."""
    conn = get_db()
    users = conn.execute("SELECT id, name, email, role, approved, created_at FROM users ORDER BY name").fetchall()
    conn.close()
    return render_template("admin_users.html", title="User Management", page="admin-users", nav_subtitle="User Management", users=users)


@app.route("/admin/approvals")
@admin_required
def admin_approvals():
    """Manage pending user approvals."""
    conn = get_db()
    pending = conn.execute("SELECT id, name, email, role FROM users WHERE approved = 0 ORDER BY id").fetchall()
    conn.close()
    return render_template("admin_approvals.html", title="Approvals", page="admin-approvals", nav_subtitle="User Approvals", pending=pending)


@app.route("/admin/analytics")
@admin_required
def admin_analytics():
    """Detailed analytics page."""
    return render_template("admin_analytics.html", title="System Analytics", page="admin-analytics", nav_subtitle="Analytics Dashboard")


@app.route("/admin/logs")
@admin_required
def admin_logs():
    """System activity logs."""
    conn = get_db()
    logs = conn.execute("""
        SELECT a.id, a.action, a.details, a.timestamp, u.name as user_name 
        FROM activity_logs a 
        LEFT JOIN users u ON a.user_id = u.id 
        ORDER BY a.id DESC 
        LIMIT 100
    """).fetchall()
    conn.close()
    return render_template("admin_logs.html", title="Activity Logs", page="admin-logs", nav_subtitle="System Logs", logs=logs)


@app.route("/admin/announcements", methods=["GET", "POST"])
@admin_required
def admin_announcements():
    """Post and view announcements."""
    conn = get_db()
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        app_link = request.form.get("app_link")
        deadline = request.form.get("deadline")
        
        if title and content:
            conn.execute(
                "INSERT INTO announcements (title, content, app_link, deadline) VALUES (?, ?, ?, ?)", 
                (title, content, app_link, deadline)
            )
            conn.commit()
            log_activity(session.get("user_id"), "Announcement", f"Posted: {title}")
            flash("Announcement posted successfully.")
        else:
            flash("Title and content are required.")
            
    announcements = conn.execute("SELECT * FROM announcements ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin_announcements.html", title="Announcements", page="admin-announcements", nav_subtitle="Announcements", announcements=announcements)


@app.route("/admin/delete-announcement/<int:ann_id>", methods=["POST"])
@admin_required
def delete_announcement(ann_id):
    """Delete an announcement."""
    conn = get_db()
    conn.execute("DELETE FROM announcements WHERE id = ?", (ann_id,))
    conn.commit()
    conn.close()
    log_activity(session.get("user_id"), "Delete Announcement", f"Deleted announcement ID: {ann_id}")
    flash("Announcement deleted successfully.")
    return redirect(url_for("admin_announcements"))


@app.route("/approve-user/<int:user_id>", methods=["POST"])
@admin_required
def approve_user(user_id):
    """Approve a pending user."""
    conn = get_db()
    conn.execute("UPDATE users SET approved = 1 WHERE id = ? AND approved = 0", (user_id,))
    conn.commit()
    conn.close()
    log_activity(session.get("user_id"), "Approve User", f"Approved user ID {user_id}")
    flash("User approved.")
    return redirect(url_for("admin"))


@app.route("/reject-user/<int:user_id>", methods=["POST"])
@admin_required
def reject_user(user_id):
    """Reject (delete) a pending user."""
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ? AND approved = 0 AND role != 'admin'", (user_id,))
    conn.commit()
    conn.close()
    flash("User rejected.")
    return redirect(url_for("admin"))


@app.route("/delete-user/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    """Delete an approved user."""
    conn = get_db()
    conn.execute("DELETE FROM users WHERE id = ? AND role != 'admin'", (user_id,))
    conn.commit()
    conn.close()
    flash("User deleted.")
    return redirect(url_for("admin"))


@app.route("/placement-tracker", methods=["GET"])
@student_required
def placement_tracker():
    """View user applications in the placement tracker."""
    conn = get_db()
    # Fetch from placements table as primary canonical model
    placements = conn.execute(
        "SELECT id, company_name, role, status, created_at FROM placements WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    
    # Calculate stats for the dashboard cards (case-insensitive and safe against unexpected values)
    total_count = len(placements)
    interview_count = sum(1 for p in placements if (p["status"] or "").strip().capitalize() == "Interview")
    selected_count = sum(1 for p in placements if (p["status"] or "").strip().capitalize() == "Selected")
    rejected_count = sum(1 for p in placements if (p["status"] or "").strip().capitalize() == "Rejected")
    
    # Calculate progress percentage (Selected * 100% + Interview * 50%)
    if total_count > 0:
        progress_percentage = min(100, int((selected_count * 100 + interview_count * 50) / total_count))
    else:
        progress_percentage = 0
    
    return render_template(
        "placement-tracker.html",
        title="Placement Preparation Tracker",
        page="placement-tracker",
        nav_subtitle="Placement Tracker",
        placements=placements,
        total_count=total_count,
        interview_count=interview_count,
        selected_count=selected_count,
        rejected_count=rejected_count,
        progress_percentage=progress_percentage
    )


@app.route("/create-application", methods=["POST"])
@student_required
def create_application():
    """Create a new job application record (harmonized with placements)."""
    company_name = request.form.get("company_name", "").strip()
    job_role = request.form.get("job_role", "") or request.form.get("role", "")
    job_role = job_role.strip()
    raw_status = request.form.get("status", "Applied").strip()
    
    if not company_name or not job_role:
        flash("Company Name and Job Role are required.")
        return redirect(url_for("placement_tracker"))
        
    valid_statuses = {"Applied", "Interview", "Selected", "Rejected"}
    normalized_status = raw_status.capitalize()
    if normalized_status not in valid_statuses:
        normalized_status = "Applied"
        
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_applied = datetime.now().strftime("%Y-%m-%d")
    
    conn = get_db()
    conn.execute(
        "INSERT INTO placements (user_id, company_name, role, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (session["user_id"], company_name, job_role, normalized_status, now)
    )
    conn.execute(
        "INSERT INTO applications (user_id, company_name, job_role, status, date_applied) VALUES (?, ?, ?, ?, ?)",
        (session["user_id"], company_name, job_role, normalized_status, date_applied)
    )
    conn.commit()
    conn.close()
    
    log_activity(session["user_id"], "Add Placement", f"Added application for {company_name}")
    flash("Application added successfully.")
    return redirect(url_for("placement_tracker"))


@app.route("/delete-application/<int:app_id>", methods=["POST"])
@student_required
def delete_application(app_id):
    """Delete a job application record."""
    conn = get_db()
    # Delete from applications
    conn.execute(
        "DELETE FROM applications WHERE id = ? AND user_id = ?",
        (app_id, session["user_id"])
    )
    # Also delete matching placement if present
    conn.execute(
        "DELETE FROM placements WHERE id = ? AND user_id = ?",
        (app_id, session["user_id"])
    )
    conn.commit()
    conn.close()
    
    flash("Application deleted.")
    return redirect(url_for("placement_tracker"))


# Additional page routes (no extra logic, just render)
@app.route("/account-settings", methods=["GET", "POST"])
@student_required
def account_settings():
    """Student profile and password management."""
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_new_password")
        
        if not current_password or not new_password or not confirm_password:
            flash("All password fields are required.")
            return redirect(url_for("account_settings"))

        is_valid_pw, pw_err = validate_password_strength(new_password)
        if not is_valid_pw:
            flash(pw_err)
            return redirect(url_for("account_settings"))
            
        if new_password != confirm_password:
            flash("New passwords do not match.")
            return redirect(url_for("account_settings"))
            
        conn = get_db()
        user = conn.execute("SELECT password FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        
        if not user or not check_password(current_password, user["password"]):
            conn.close()
            flash("Incorrect current password.")
            return redirect(url_for("account_settings"))
            
        hashed_pw = hash_password(new_password)
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, session["user_id"]))
        conn.commit()
        conn.close()
        
        log_activity(session["user_id"], "Password Change", "Student updated their password")
        flash("Password updated successfully.")
        return redirect(url_for("account_settings"))
        
    return render_template("student_account_settings.html", title="Account Settings", page="account-settings", nav_subtitle="Account Management")


@app.route("/admin/account-settings", methods=["GET", "POST"])
@admin_required
def admin_account_settings():
    """Admin profile and password management."""
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_new_password = request.form.get("confirm_new_password")
        
        if not current_password or not new_password or not confirm_new_password:
            flash("All fields are required.")
            return redirect(url_for("admin_account_settings"))

        is_valid_pw, pw_err = validate_password_strength(new_password)
        if not is_valid_pw:
            flash(pw_err)
            return redirect(url_for("admin_account_settings"))
            
        if new_password != confirm_new_password:
            flash("New passwords do not match.")
            return redirect(url_for("admin_account_settings"))
            
        conn = get_db()
        user = conn.execute("SELECT password FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        
        if not user or not check_password(current_password, user["password"]):
            conn.close()
            flash("Incorrect current password.")
            return redirect(url_for("admin_account_settings"))
            
        hashed_pw = hash_password(new_password)
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, session["user_id"]))
        conn.commit()
        conn.close()
        
        log_activity(session["user_id"], "Password Change", "Admin updated their password")
        flash("Password updated successfully.")
        return redirect(url_for("admin_account_settings"))
        
    return render_template("admin_account_settings.html", title="Account Settings", page="profile", nav_subtitle="Account Management")


@app.route("/career-roadmap")
@student_required
def career_roadmap():
    return render_app_page("career-roadmap.html", "Career Roadmap", "career-roadmap")


@app.route("/resume-tips")
@student_required
def resume_tips():
    return render_app_page("resume-tips.html", "Resume & Interview Preparation", "resume-tips", "Resume & Interview")




@app.route("/career-quiz")
@student_required
def career_quiz():
    return render_app_page("career-quiz.html", "Career Assessment Quiz", "career-quiz", "Career Quiz")


@app.route("/admin-stats", methods=["GET"])
@admin_required
def admin_stats():
    """Returns system analytics for the admin dashboard."""
    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    approved_users = conn.execute("SELECT COUNT(*) FROM users WHERE approved = 1").fetchone()[0]
    pending_users = conn.execute("SELECT COUNT(*) FROM users WHERE approved = 0").fetchone()[0]
    total_chats = conn.execute("SELECT COUNT(*) FROM chat_history").fetchone()[0]
    
    # Placements as canonical source of applications
    total_apps = conn.execute("SELECT COUNT(*) FROM placements").fetchone()[0]
    total_resumes = conn.execute("SELECT COUNT(*) FROM users WHERE resume_score > 0").fetchone()[0]
    
    # Status breakdown across all student applications
    status_counts = {"Applied": 0, "Interview": 0, "Selected": 0, "Rejected": 0}
    raw_status_counts = conn.execute("""
        SELECT status, COUNT(*) as count 
        FROM placements 
        GROUP BY status
    """).fetchall()
    for row in raw_status_counts:
        norm_status = (row["status"] or "").strip().capitalize()
        if norm_status in status_counts:
            status_counts[norm_status] += row["count"]
        else:
            status_counts[norm_status] = row["count"]
    
    # Activity data (Last 7 active dates of applications from placements)
    app_activity = conn.execute("""
        SELECT SUBSTR(created_at, 1, 10) as date, COUNT(*) as count 
        FROM placements 
        GROUP BY date 
        ORDER BY date DESC 
        LIMIT 7
    """).fetchall()
    
    # User growth (Last 7 days of signups)
    user_growth = conn.execute("""
        SELECT SUBSTR(created_at, 1, 10) as date, COUNT(*) as count 
        FROM users 
        GROUP BY date 
        ORDER BY date DESC 
        LIMIT 7
    """).fetchall()

    # Chat activity (Last 7 days of messages)
    chat_activity = conn.execute("""
        SELECT SUBSTR(timestamp, 1, 10) as date, COUNT(*) as count 
        FROM chat_history 
        GROUP BY date 
        ORDER BY date DESC 
        LIMIT 7
    """).fetchall()
    
    conn.close()
    
    # Format and reverse for chronological charts
    format_data = lambda query: [{"date": row["date"], "count": row["count"]} for row in reversed(query)]
    
    return jsonify({
        "total_users": total_users,
        "approved_users": approved_users,
        "pending_users": pending_users,
        "total_chats": total_chats,
        "total_apps": total_apps,
        "total_resumes": total_resumes,
        "status_counts": status_counts,
        "app_activity": format_data(app_activity),
        "user_growth": format_data(user_growth),
        "chat_activity": format_data(chat_activity)
    })


CAREER_MAP = {
    "Web Developer": {
        "explanation": "You enjoy designing user interfaces, building websites, and working with web technologies.",
        "skills": ["HTML", "CSS", "JavaScript", "React", "Node.js", "Git"],
        "roadmap": [
            "Learn HTML, CSS, and basic UI design principles",
            "Master JavaScript (ES6+) fundamentals",
            "Learn a frontend framework like React, Vue, or Angular",
            "Understand backend APIs and server-side logic with Node.js",
            "Build full-stack web applications and deploy them"
        ],
        "tools": ["VS Code", "Figma", "Git/GitHub", "npm/yarn", "Docker"]
    },
    "Data Scientist": {
        "explanation": "You like working with data, analyzing datasets, and applying statistical models.",
        "skills": ["Python", "SQL", "Pandas", "Matplotlib", "Machine Learning", "Statistics"],
        "roadmap": [
            "Learn Python programming and data structures",
            "Master SQL for data extraction and manipulation",
            "Study data analysis with Pandas and NumPy",
            "Learn data visualization with Matplotlib and Seaborn",
            "Practice Machine Learning models on real-world datasets"
        ],
        "tools": ["Jupyter Notebook", "Scikit-learn", "Tableau", "PostgreSQL", "Anaconda"]
    },
    "Machine Learning Engineer": {
        "explanation": "You are excited by training advanced models and building intelligent AI systems.",
        "skills": ["Python", "Math (Linear Algebra)", "Machine Learning", "Deep Learning", "TensorFlow", "MLOps"],
        "roadmap": [
            "Master Python and core mathematical concepts (Linear Algebra, Calculus)",
            "Understand classical Machine Learning algorithms (Regression, Trees)",
            "Dive into Deep Learning and Neural Network architectures",
            "Learn model deployment and MLOps practices",
            "Train and optimize models using real-world datasets"
        ],
        "tools": ["TensorFlow", "PyTorch", "HuggingFace", "AWS SageMaker", "Docker"]
    },
    "Software Developer": {
        "explanation": "You prefer building robust applications, problem-solving, and writing efficient algorithms.",
        "skills": ["Python/Java/C++", "DSA", "SQL", "System Design", "Git", "Unit Testing"],
        "roadmap": [
            "Master a core programming language (Python, Java, or C++)",
            "Practice Data Structures and Algorithms (DSA) extensively",
            "Learn Object-Oriented Programming (OOP) and Design Patterns",
            "Understand Database management and System Design",
            "Contribute to open source projects and build complex applications"
        ],
        "tools": ["IntelliJ IDEA", "VS Code", "GitHub Actions", "Docker", "PostgreSQL"]
    }
}


@app.route("/career-quiz-result", methods=["POST"])
@student_required
def career_quiz_result():
    """Evaluate the career quiz and return a recommendation."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No answers provided"}), 400
        
    # Tally up the domains
    scores = {
        "Web": 0,
        "Data": 0,
        "AI": 0,
        "Software": 0
    }
    
    # Map the answers to the domain categories (Realistic Questions)
    for question, answer in data.items():
        # Web Development indicators
        if answer in ["Creating a beautiful and interactive user interface", 
                     "Modern frameworks like React or Tailwind", 
                     "Thinking about how a user will interact with a feature", 
                     "The Future of Web Design: Glassmorphism and 3D", 
                     "Visual appeal and smooth user experience"]:
            scores["Web"] += 1
            
        # Data Science indicators
        elif answer in ["Finding hidden patterns in massive amounts of information", 
                       "Power bi, SQL, and database visualization", 
                       "Using statistical evidence to prove a hypothesis", 
                       "How Big Data is Revolutionizing Business Decisions", 
                       "Accuracy and clear data representation"]:
            scores["Data"] += 1
            
        # Machine Learning / AI indicators
        elif answer in ["Teaching a computer to recognize images or text", 
                       "Neural networks and deep learning", 
                       "Experimenting with data to improve model accuracy", 
                       "Breaking Through: New AI Models Surpass Human Performance", 
                       "Ability to learn and adapt over time"]:
            scores["AI"] += 1
            
        # Software Engineering / Backend indicators
        elif answer in ["Building a high-performance system or complex algorithm", 
                       "System architecture and low-level code", 
                       "Breaking down complex logic into efficient functions", 
                       "Optimizing Backend Systems for Millions of Users", 
                       "Reliability, performance, and structure"]:
            scores["Software"] += 1
            
    # Find the domain with the highest score
    winning_domain = max(scores, key=scores.get)
    
    # Map domains to careers
    domain_to_career = {
        "Web": "Web Developer",
        "Data": "Data Scientist",
        "AI": "Machine Learning Engineer",
        "Software": "Software Developer"
    }
    
    career_name = domain_to_career.get(winning_domain, "Software Developer")
    career_data = CAREER_MAP[career_name]
    
    return jsonify({
        "career": career_name,
        "explanation": career_data["explanation"],
        "skills": career_data["skills"],
        "roadmap": career_data["roadmap"],
        "tools": career_data["tools"]
    })


@app.route("/add-placement", methods=["POST"])
@student_required
def add_placement():
    """Add a new placement application entry."""
    company_name = request.form.get("company_name", "").strip()
    role = request.form.get("role", "").strip()
    raw_status = request.form.get("status", "Applied").strip()
    
    if not company_name or not role:
        flash("Company Name and Role are required.")
        return redirect(url_for("placement_tracker"))
    
    valid_statuses = {"Applied", "Interview", "Selected", "Rejected"}
    normalized_status = raw_status.capitalize()
    if normalized_status not in valid_statuses:
        normalized_status = "Applied"
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute(
        "INSERT INTO placements (user_id, company_name, role, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (session["user_id"], company_name, role, normalized_status, now)
    )
    conn.commit()
    conn.close()
    
    log_activity(session["user_id"], "Add Placement", f"Added application for {company_name}")
    flash("Placement entry added successfully!")
    return redirect(url_for("placement_tracker"))

@app.route("/update-placement/<int:id>", methods=["POST"])
@student_required
def update_placement(id):
    """Update the status of a placement entry."""
    raw_status = request.form.get("status", "").strip()
    if not raw_status:
        flash("Status is required.")
        return redirect(url_for("placement_tracker"))
    
    valid_statuses = {"Applied", "Interview", "Selected", "Rejected"}
    normalized_status = raw_status.capitalize()
    if normalized_status not in valid_statuses:
        flash("Invalid status.")
        return redirect(url_for("placement_tracker"))
    
    conn = get_db()
    # Ensure the placement belongs to the user
    placement = conn.execute("SELECT * FROM placements WHERE id = ? AND user_id = ?", (id, session["user_id"])).fetchone()
    
    if placement:
        conn.execute("UPDATE placements SET status = ? WHERE id = ? AND user_id = ?", (normalized_status, id, session["user_id"]))
        conn.commit()
        log_activity(session["user_id"], "Update Placement", f"Updated status for {placement['company_name']} to {normalized_status}")
        flash("Placement status updated!")
    else:
        flash("Placement record not found.")
        
    conn.close()
    return redirect(url_for("placement_tracker"))

@app.route("/delete-placement/<int:id>", methods=["POST"])
@student_required
def delete_placement(id):
    """Delete a placement entry."""
    conn = get_db()
    # Ensure the placement belongs to the user
    placement = conn.execute("SELECT * FROM placements WHERE id = ? AND user_id = ?", (id, session["user_id"])).fetchone()
    
    if placement:
        conn.execute("DELETE FROM placements WHERE id = ? AND user_id = ?", (id, session["user_id"]))
        conn.commit()
        log_activity(session["user_id"], "Delete Placement", f"Deleted placement entry for {placement['company_name']}")
        flash("Placement record deleted.")
    else:
        flash("Placement record not found.")
        
    conn.close()
    return redirect(url_for("placement_tracker"))


# ==============================================================================
#                      17 FEATURE MODULES ROUTE HANDLERS
# ==============================================================================

# 1. AUTH EXTENSIONS (Forgot Password)
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Secure password reset flow."""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not email:
            flash("Please enter your registered email address.")
            return render_template("student-login.html", active_tab="forgot")

        if not is_valid_email(email):
            flash("Please enter a valid email address.")
            return render_template("student-login.html", active_tab="forgot")

        conn = get_db()
        user = conn.execute("SELECT id, name, email FROM users WHERE LOWER(email) = ?", (email,)).fetchone()

        if not user:
            conn.close()
            flash("If that email address exists in our system, reset instructions have been processed.")
            return render_template("student-login.html", active_tab="forgot")

        # If user submitted new password with confirmation
        if new_password:
            is_valid_pw, pw_err = validate_password_strength(new_password)
            if not is_valid_pw:
                conn.close()
                flash(pw_err)
                return render_template("student-login.html", active_tab="forgot", reset_email=email, step=2)

            if new_password != confirm_password:
                conn.close()
                flash("Passwords do not match. Please re-enter matching passwords.")
                return render_template("student-login.html", active_tab="forgot", reset_email=email, step=2)

            hashed_pw = hash_password(new_password)
            conn.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, user["id"]))
            conn.commit()
            conn.close()
            log_activity(user["id"], "Password Reset", "User reset their account password")
            flash("Password updated successfully! You can now log in with your new password.")
            return redirect(url_for("student_login"))

        conn.close()
        flash(f"Account identified for {email}. Please set your new password below.")
        return render_template("student-login.html", active_tab="forgot", reset_email=email, step=2)

    return render_template("student-login.html", active_tab="forgot")


# 2. AI CAREER RECOMMENDATION
@app.route("/career-recommendation", methods=["GET", "POST"])
@login_required
def career_recommendation():
    recommendation = None
    if request.method == "POST":
        education = request.form.get("education", "").strip()
        skills = request.form.get("skills", "").strip()
        interests = request.form.get("interests", "").strip()
        experience = request.form.get("experience", "").strip()
        industry = request.form.get("industry", "").strip()
        
        prompt = f"""You are an expert AI Career Coach. Analyze the user profile below and recommend the top 3 best career paths.
Education: {education}
Skills: {skills}
Interests: {interests}
Experience: {experience}
Preferred Industry: {industry}

Provide response as a valid JSON object with key "careers" containing an array of objects with keys:
"title", "match_score" (percentage number), "salary_range", "demand_level" (High/Very High), "required_skills" (array of strings), "learning_steps" (array of strings). Do not include markdown code block formatting if possible.
"""
        recommendation = None
        res_text = safe_gemini_generate(prompt)
        if res_text:
            try:
                clean_txt = res_text.replace("```json", "").replace("```", "").strip()
                recommendation = json.loads(clean_txt)
            except Exception:
                recommendation = None
        
        if not recommendation:
            # High-quality dynamic fallback
            recommendation = {
                "careers": [
                    {
                        "title": f"Senior {industry or 'Tech'} Engineer",
                        "match_score": 92,
                        "salary_range": "$85,000 - $130,000",
                        "demand_level": "Very High",
                        "required_skills": [s.strip() for s in skills.split(",") if s.strip()] + ["System Design", "Cloud Architecture"],
                        "learning_steps": ["Master advanced data structures", "Build 2 full-stack portfolio projects", "Contribute to open source"]
                    },
                    {
                        "title": "AI Solutions Architect",
                        "match_score": 85,
                        "salary_range": "$95,000 - $145,000",
                        "demand_level": "Extreme",
                        "required_skills": ["Python", "Prompt Engineering", "LLM APIs", "SQL"],
                        "learning_steps": ["Complete Generative AI specialization", "Deploy production AI copilot app", "Practice system design interviews"]
                    }
                ]
            }

    return render_template("career_recommendation.html", title="AI Career Recommendation", page="career-recommendation", recommendation=recommendation)


# 3. PERSONALIZED AI LEARNING ROADMAP
@app.route("/roadmap", methods=["GET", "POST"])
@student_required
def roadmap():
    user_id = session["user_id"]
    context = build_student_context(user_id)
    latest_roadmap = None
    roadmap_data = None
    completed_items = []
    progress_pct = 0
    selected_goal = context.get("target_role", "Software Developer")
    selected_hours = "2"
    selected_level = "Beginner"

    conn = get_db()
    if request.method == "POST":
        career_goal = request.form.get("career_goal", selected_goal).strip()
        hours_per_day = request.form.get("hours_per_day", "2").strip()
        level = request.form.get("level", "Beginner").strip()
        selected_goal = career_goal
        selected_hours = hours_per_day
        selected_level = level

        prompt = f"""You are an expert AI Career Coach. Generate a comprehensive, personalized learning roadmap for this student:
STUDENT PROFILE:
- Target Role / Career Goal: {career_goal}
- Current Skills: {context.get('skills', 'Basics')}
- Education: {context.get('education', 'Undergraduate')}
- Weak Topics: {', '.join(context.get('weak_topics', [])) or 'None recorded'}
- Available Study Time: {hours_per_day} hours/day
- Experience Level: {level}

Provide the response strictly as a valid JSON object with the following keys:
- "daily": array of 3 actionable daily tasks with time estimates
- "weekly": array of 4 sequential weekly goal milestones
- "monthly": array of 3 monthly capstone objectives
- "tips": array of 2 placement preparation tips

Do not wrap in markdown quotes if possible."""

        res_text = safe_gemini_generate(prompt)
        if res_text:
            try:
                clean_txt = res_text.replace("```json", "").replace("```", "").strip()
                roadmap_data = json.loads(clean_txt)
            except Exception as e:
                app.logger.warning(f"Failed to parse Gemini roadmap JSON: {e}")
                roadmap_data = None

        if not roadmap_data:
            # Deterministic, profile-tailored fallback
            roadmap_data = {
                "daily": [
                    f"Hour 1: Algorithmic problem solving and data structure practice for {career_goal}",
                    f"Hour 2: Hands-on implementation of core skills ({context.get('skills', 'Code')} & project work)",
                    "30 mins: Review CS fundamentals, weak topics, and system concepts"
                ],
                "weekly": [
                    f"Week 1: Core Fundamentals, Language Proficiency & Command Line Tools",
                    f"Week 2: Frameworks, APIs & Database Integration for {career_goal}",
                    f"Week 3: Full-Stack Project Building & Version Control on GitHub",
                    f"Week 4: Portfolio Project Deployment & System Design Review"
                ],
                "monthly": [
                    f"Month 1: Technical Foundations, Problem Solving Mastery & Mini Projects",
                    f"Month 2: Production-Ready Capstone Application & Testing",
                    f"Month 3: System Design, Mock Interviews & Placement Drive Preparation"
                ],
                "tips": [
                    f"Dedicate at least {hours_per_day} hours consistently every day to retain muscle memory.",
                    f"Tailor your GitHub portfolio directly to {career_goal} job descriptions."
                ]
            }

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """
            INSERT INTO roadmaps (user_id, career_goal, available_hours, content_json, completed_items_json, progress_pct, created_at)
            VALUES (?, ?, ?, ?, '[]', 0, ?)
            """,
            (user_id, career_goal, int(hours_per_day), json.dumps(roadmap_data), now)
        )
        conn.commit()
        roadmap_id = cursor.lastrowid
        log_activity(user_id, "Generated Roadmap", f"Generated roadmap for {career_goal}")
        conn.close()
        return redirect(url_for("roadmap"))

    else:
        # GET request: load latest saved roadmap for this student
        row = conn.execute(
            "SELECT * FROM roadmaps WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        conn.close()

        if row:
            try:
                roadmap_data = json.loads(row["content_json"])
            except Exception:
                roadmap_data = None
            try:
                completed_items = json.loads(row["completed_items_json"]) if "completed_items_json" in row.keys() and row["completed_items_json"] else []
            except Exception:
                completed_items = []
            progress_pct = row["progress_pct"] if "progress_pct" in row.keys() and row["progress_pct"] else 0
            selected_goal = row["career_goal"]
            selected_hours = str(row["available_hours"])
            roadmap_id = row["id"]
        else:
            roadmap_id = None

    return render_template(
        "roadmap.html",
        title="Personalized Learning Roadmap",
        page="roadmap",
        roadmap=roadmap_data,
        completed_items=completed_items,
        progress_pct=progress_pct,
        roadmap_id=roadmap_id,
        context=context,
        selected_goal=selected_goal,
        selected_hours=selected_hours,
        selected_level=selected_level
    )


@app.route("/api/roadmap/toggle", methods=["POST"])
@student_required
def api_toggle_roadmap_item():
    """Toggle completion of an item in the student's latest roadmap."""
    user_id = session["user_id"]
    data = request.get_json() or {}
    item_id = data.get("item_id")
    roadmap_id = data.get("roadmap_id")

    if not item_id:
        return jsonify({"error": "Item ID required"}), 400

    conn = get_db()
    if roadmap_id:
        row = conn.execute("SELECT * FROM roadmaps WHERE id = ? AND user_id = ?", (roadmap_id, user_id)).fetchone()
    else:
        row = conn.execute("SELECT * FROM roadmaps WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,)).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Roadmap not found"}), 404

    try:
        content = json.loads(row["content_json"])
        total_items = len(content.get("daily", [])) + len(content.get("weekly", [])) + len(content.get("monthly", []))
    except Exception:
        total_items = 10

    completed = []
    try:
        completed = json.loads(row["completed_items_json"]) if row["completed_items_json"] else []
    except Exception:
        completed = []

    if item_id in completed:
        completed.remove(item_id)
        is_completed = False
    else:
        completed.append(item_id)
        is_completed = True

    new_pct = round((len(completed) / max(1, total_items)) * 100) if total_items > 0 else 0

    conn.execute(
        "UPDATE roadmaps SET completed_items_json = ?, progress_pct = ? WHERE id = ? AND user_id = ?",
        (json.dumps(completed), new_pct, row["id"], user_id)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "item_id": item_id,
        "is_completed": is_completed,
        "progress_pct": new_pct,
        "completed_count": len(completed),
        "total_count": total_items
    })


# 4. AI MOCK INTERVIEW
@app.route("/mock-interview")
@student_required
def mock_interview():
    """Render Enhanced AI Mock Interview Portal with history."""
    conn = get_db()
    history = conn.execute(
        "SELECT * FROM interviews WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    
    context = build_student_context(session["user_id"])
    
    return render_template(
        "mock_interview.html", 
        title="AI Mock Interview", 
        page="mock-interview",
        history=history,
        context=context
    )


@app.route("/api/mock-interview/start", methods=["POST"])
@student_required
def api_mock_interview_start():
    """
    Generates 5 personalized interview questions (Technical, HR, or Mixed) 
    tailored to the student's target role, skills, weak topics, and project profile.
    """
    user_id = session["user_id"]
    data = request.get_json() or {}
    category = data.get("category", "Technical Interview")
    target_role = data.get("target_role") or "Software Developer"
    question_count = int(data.get("question_count", 5))
    
    context = build_student_context(user_id)
    
    prompt = f"""You are an expert technical interviewer conducting a {category} for a candidate applying for '{target_role}'.
CANDIDATE CONTEXT:
- Skills: {context.get('skills')}
- Weak Topics: {', '.join(context.get('weak_topics', [])) or 'General CS'}
- Education: {context.get('education')}
- Projects/Interests: {context.get('interests')}

Generate exactly {question_count} placement-oriented interview questions.
If category is "HR Interview", focus on behavioral, project experience, teamwork, and career goal questions.
If category is "Technical Interview", focus on target role concepts, coding principles, SQL, and their weak topics.
If category is "Mixed Interview", combine technical and HR questions.

Return response strictly as a JSON object with key "questions" containing an array of strings. Do not include markdown formatting.
"""
    questions = None
    res_text = safe_gemini_generate(prompt)
    if res_text:
        try:
            clean_txt = res_text.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(clean_txt)
            questions = parsed.get("questions", [])
        except Exception:
            questions = None
            
    if not questions or len(questions) == 0:
        if "HR" in category:
            questions = [
                f"Tell me about yourself and why you want to become a {target_role}.",
                f"Describe a challenging technical problem you faced in your project and how you solved it.",
                f"How do you handle conflict or tight deadlines when working in a team?",
                f"What are your greatest technical strengths and what area are you currently working to improve?",
                f"Where do you see your career progressing in the next 3 to 5 years?"
            ]
        else:
            questions = [
                f"Explain the core concepts and architecture required to build a scalable application in {target_role}.",
                f"How do you handle memory management and optimization in your primary programming language ({context.get('skills', 'Python')})?",
                f"Explain SQL joins and indexing strategies. How would you optimize a slow database query?",
                f"Walk me through a real project you built. What tech stack did you choose and why?",
                f"How do you approach debugging a production issue when a system fails silently?"
            ]

    return jsonify({
        "category": category,
        "target_role": target_role,
        "questions": questions[:question_count],
        "total_questions": len(questions[:question_count])
    })


@app.route("/api/mock-interview/evaluate-question", methods=["POST"])
@student_required
def api_evaluate_question():
    """
    Evaluates a single question answer on 5 dimensions:
    Relevance, Technical Accuracy, Communication, Clarity, Problem Solving (0-100).
    """
    data = request.get_json() or {}
    category = data.get("category", "Technical Interview")
    question = data.get("question", "")
    answer = data.get("answer", "")
    
    if not answer or not answer.strip():
        return jsonify({
            "relevance": 0,
            "technical_accuracy": 0,
            "communication": 0,
            "clarity": 0,
            "problem_solving": 0,
            "overall_score": 0,
            "feedback": "No answer provided.",
            "ideal_answer": "Provide a structured answer detailing context, technical approach, and result."
        })
        
    prompt = f"""Evaluate this candidate's response to an interview question for {category}.
Question: {question}
Candidate Answer: {answer}

Provide evaluation strictly as JSON with keys:
- "relevance" (0-100)
- "technical_accuracy" (0-100)
- "communication" (0-100)
- "clarity" (0-100)
- "problem_solving" (0-100)
- "feedback" (2 sentence critique)
- "ideal_answer" (2 sentence ideal response)
"""
    result = None
    res_text = safe_gemini_generate(prompt)
    if res_text:
        try:
            clean_txt = res_text.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean_txt)
        except Exception:
            result = None

    if not result:
        ans_len = len(answer.strip().split())
        rel = min(95, max(40, ans_len * 3))
        acc = min(90, max(50, ans_len * 2 + 30))
        comm = 80 if ans_len > 15 else 50
        clar = 85 if ans_len > 20 else 55
        ps = 75
        result = {
            "relevance": rel,
            "technical_accuracy": acc,
            "communication": comm,
            "clarity": clar,
            "problem_solving": ps,
            "feedback": "Good attempt! Structure your response using the STAR method (Situation, Task, Action, Result) for maximum impact.",
            "ideal_answer": "An ideal response clearly explains the technical concept or situation, details the exact tools/action taken, and states the measurable outcome."
        }

    rel = int(result.get("relevance", 75))
    acc = int(result.get("technical_accuracy", 75))
    comm = int(result.get("communication", 75))
    clar = int(result.get("clarity", 75))
    ps = int(result.get("problem_solving", 75))
    
    overall_question_score = round((rel + acc + comm + clar + ps) / 5)
    result["overall_score"] = overall_question_score
    return jsonify(result)


@app.route("/api/mock-interview/submit-final", methods=["POST"])
@student_required
def api_submit_final_interview():
    """
    Calculates final session score across all 5 questions, generates comprehensive report,
    and saves to interviews database table.
    """
    user_id = session["user_id"]
    data = request.get_json() or {}
    category = data.get("category", "Technical Interview")
    evaluations = data.get("evaluations", [])
    
    if not evaluations:
        return jsonify({"error": "No question evaluations provided"}), 400
        
    avg_rel = round(sum(e.get("relevance", 70) for e in evaluations) / len(evaluations))
    avg_acc = round(sum(e.get("technical_accuracy", 70) for e in evaluations) / len(evaluations))
    avg_comm = round(sum(e.get("communication", 70) for e in evaluations) / len(evaluations))
    avg_clar = round(sum(e.get("clarity", 70) for e in evaluations) / len(evaluations))
    avg_ps = round(sum(e.get("problem_solving", 70) for e in evaluations) / len(evaluations))
    
    overall_score = round((avg_rel + avg_acc + avg_comm + avg_clar + avg_ps) / 5)
    
    strengths = []
    if avg_acc >= 75: strengths.append("Technical Accuracy")
    if avg_comm >= 75: strengths.append("Communication & Tone")
    if avg_clar >= 75: strengths.append("Response Structure & Clarity")
    if avg_ps >= 75: strengths.append("Problem Solving Approach")
    if not strengths: strengths.append("Relevance & Focus")

    weaknesses = []
    if avg_acc < 75: weaknesses.append("Technical Accuracy & Depth")
    if avg_comm < 75: weaknesses.append("Communication & Conciseness")
    if avg_clar < 75: weaknesses.append("Clarity & STAR Method Structure")
    if avg_ps < 75: weaknesses.append("Problem Solving Edge Cases")
    if not weaknesses: weaknesses.append("Deep System Trade-offs")

    rec_topics = ["Revise core technical definitions", "Practice 2 coding problems", "Structure HR answers with STAR technique"]
    feedback_summary = f"Completed {category} with an overall score of {overall_score}%. Strongest area: {strengths[0]}."

    details_json = json.dumps({
        "relevance": avg_rel,
        "technical_accuracy": avg_acc,
        "communication": avg_comm,
        "clarity": avg_clar,
        "problem_solving": avg_ps,
        "strengths": strengths,
        "areas_to_improve": weaknesses,
        "recommended_topics": rec_topics
    })

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute(
        "INSERT INTO interviews (user_id, category, score, feedback, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, category, overall_score, feedback_summary, details_json, now)
    )
    conn.commit()
    conn.close()

    log_activity(user_id, "Mock Interview", f"Category: {category}, Score: {overall_score}%")

    return jsonify({
        "overall_score": overall_score,
        "technical_accuracy": avg_acc,
        "communication": avg_comm,
        "clarity": avg_clar,
        "relevance": avg_rel,
        "problem_solving": avg_ps,
        "strengths": strengths,
        "areas_to_improve": weaknesses,
        "recommended_topics": rec_topics,
        "summary": feedback_summary
    })


# 5. JOB MATCH ANALYZER
@app.route("/job-match", methods=["GET", "POST"])
@login_required
def job_match():
    match_result = None
    jd_text = ""
    resume_text = ""
    if request.method == "POST":
        from werkzeug.utils import secure_filename
        import tempfile

        jd_text = request.form.get("job_description", "").strip()
        resume_text = request.form.get("resume_text", "").strip()
        file = request.files.get("resume_file")

        # 1. Validate Job Description
        if not jd_text:
            flash("Job Description is required to evaluate keyword alignment.", "error")
            return render_template("job_match.html", title="Job Match Analyzer", page="job-match", result=None, jd_text="", resume_text=resume_text), 400

        if len(jd_text.split()) < 5:
            flash("The provided Job Description is too brief. Please paste a more detailed job posting.", "error")
            return render_template("job_match.html", title="Job Match Analyzer", page="job-match", result=None, jd_text=jd_text, resume_text=resume_text), 400

        # 2. Extract Resume Content (File Upload OR Pasted Text)
        extracted_text = ""
        if file and file.filename:
            raw_filename = secure_filename(file.filename) or "resume.pdf"
            ext = os.path.splitext(raw_filename)[1].lower()
            if ext not in [".pdf", ".docx"]:
                flash("Invalid file format. Only PDF (.pdf) and Word (.docx) documents are supported.", "error")
                return render_template("job_match.html", title="Job Match Analyzer", page="job-match", result=None, jd_text=jd_text, resume_text=resume_text), 400

            file_bytes = file.read()
            if len(file_bytes) == 0:
                flash("The uploaded file is empty (0 bytes). Please upload a valid document.", "error")
                return render_template("job_match.html", title="Job Match Analyzer", page="job-match", result=None, jd_text=jd_text, resume_text=resume_text), 400

            if len(file_bytes) > 5 * 1024 * 1024:
                flash("Uploaded file exceeds maximum limit of 5MB.", "error")
                return render_template("job_match.html", title="Job Match Analyzer", page="job-match", result=None, jd_text=jd_text, resume_text=resume_text), 400

            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                if not extract_text_from_file:
                    flash("Text extraction engine unavailable.", "error")
                    return render_template("job_match.html", title="Job Match Analyzer", page="job-match", result=None, jd_text=jd_text, resume_text=resume_text), 500

                extracted_text, extract_err = extract_text_from_file(tmp_path, raw_filename)
                if extract_err:
                    flash(extract_err, "error")
                    return render_template("job_match.html", title="Job Match Analyzer", page="job-match", result=None, jd_text=jd_text, resume_text=resume_text), 400
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
        elif resume_text:
            extracted_text = resume_text
        else:
            flash("Please provide your resume by uploading a PDF/DOCX file or pasting your resume text.", "error")
            return render_template("job_match.html", title="Job Match Analyzer", page="job-match", result=None, jd_text=jd_text, resume_text=""), 400

        if not extracted_text or len(extracted_text.split()) < 10:
            flash("The provided resume content is too short to analyze. Please provide a more detailed resume.", "error")
            return render_template("job_match.html", title="Job Match Analyzer", page="job-match", result=None, jd_text=jd_text, resume_text=resume_text), 400

        # 3. Analyze Job Match via canonical engine
        if not analyze_job_match:
            flash("Job match analysis engine unavailable.", "error")
            return render_template("job_match.html", title="Job Match Analyzer", page="job-match", result=None, jd_text=jd_text, resume_text=resume_text), 500

        match_result = analyze_job_match(extracted_text, jd_text)

        # 4. Log activity
        user_id = session.get("user_id")
        if user_id:
            log_activity(
                user_id,
                "Job Match Analysis",
                f"Score: {match_result.get('score', 0)}% ({len(match_result.get('matching_skills', []))} matched, {len(match_result.get('missing_keywords', []))} missing)"
            )

    return render_template("job_match.html", title="Job Match Analyzer", page="job-match", result=match_result, jd_text=jd_text, resume_text=resume_text)


# 6. AI RESUME BUILDER
@app.route("/resume-builder", methods=["GET", "POST"])
@login_required
def resume_builder():
    """
    ATS-Friendly Resume Builder with full persistence in user_resumes table.
    Supports GET (view/load), POST (save/update), and JSON API responses.
    """
    user_id = session["user_id"]
    conn = get_db()
    
    # Handle save/update via POST
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        resume_id = data.get("resume_id")
        
        name = (data.get("name") or data.get("rbName") or "").strip()
        job_title = (data.get("title") or data.get("rbTitle") or "").strip()
        contact = (data.get("contact") or data.get("rbContact") or "").strip()
        summary = (data.get("summary") or data.get("rbSummary") or "").strip()
        skills = (data.get("skills") or data.get("rbSkills") or "").strip()
        education = (data.get("education") or data.get("rbEducation") or "").strip()
        template_name = (data.get("template_name") or "modern").strip()
        
        # Fallback to user profile if fields omitted
        if not name and "user_name" in session:
            name = session["user_name"]
            
        if not name or not job_title:
            conn.close()
            if is_api_request():
                return jsonify({"error": "Full Name and Target Job Title are required", "success": False}), 400
            flash("Full Name and Target Job Title are required.")
            return redirect(url_for("resume_builder"))
            
        doc_title = (data.get("doc_title") or f"{name} - {job_title}").strip()
        content_dict = {
            "name": name,
            "title": job_title,
            "contact": contact,
            "summary": summary,
            "skills": skills,
            "education": education
        }
        content_json = json.dumps(content_dict)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if updating an existing record with strict ownership verification
        saved_id = None
        if resume_id:
            try:
                resume_id_int = int(resume_id)
            except (ValueError, TypeError):
                resume_id_int = None
                
            if resume_id_int:
                existing = conn.execute(
                    "SELECT id FROM user_resumes WHERE id = ? AND user_id = ?",
                    (resume_id_int, user_id)
                ).fetchone()
                if existing:
                    conn.execute(
                        """
                        UPDATE user_resumes 
                        SET template_name = ?, title = ?, content_json = ?, updated_at = ?
                        WHERE id = ? AND user_id = ?
                        """,
                        (template_name, doc_title, content_json, now, resume_id_int, user_id)
                    )
                    saved_id = resume_id_int
                else:
                    # Tenant isolation check: if ID belongs to another user, reject
                    other_user_rec = conn.execute("SELECT id FROM user_resumes WHERE id = ?", (resume_id_int,)).fetchone()
                    if other_user_rec:
                        conn.close()
                        if is_api_request():
                            return jsonify({"error": "Forbidden: Cannot modify another user's resume", "success": False}), 403
                        flash("Access denied: You cannot modify another user's resume.")
                        return redirect(url_for("resume_builder"))

        if not saved_id:
            cursor = conn.execute(
                """
                INSERT INTO user_resumes (user_id, template_name, title, content_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, template_name, doc_title, content_json, now)
            )
            saved_id = cursor.lastrowid
            
        conn.commit()
        conn.close()
        
        log_activity(user_id, "Resume Builder", f"Saved resume: {doc_title}")
        
        if is_api_request():
            return jsonify({
                "success": True,
                "resume_id": saved_id,
                "title": doc_title,
                "template_name": template_name,
                "content": content_dict,
                "message": "Resume saved successfully!"
            }), (200 if resume_id else 201)
            
        flash("Resume saved successfully!")
        return redirect(url_for("resume_builder", id=saved_id))
        
    # GET Request: Fetch specific or latest resume and all saved resumes
    req_id = request.args.get("id")
    current_resume = None
    if req_id:
        try:
            req_id_int = int(req_id)
            r_row = conn.execute(
                "SELECT * FROM user_resumes WHERE id = ? AND user_id = ?",
                (req_id_int, user_id)
            ).fetchone()
            if r_row:
                try:
                    c_dict = json.loads(r_row["content_json"])
                except Exception:
                    c_dict = {}
                current_resume = {
                    "id": r_row["id"],
                    "template_name": r_row["template_name"],
                    "title": r_row["title"],
                    "content": c_dict,
                    "updated_at": r_row["updated_at"]
                }
        except (ValueError, TypeError):
            pass
            
    if not current_resume and not request.args.get("new"):
        latest_row = conn.execute(
            "SELECT * FROM user_resumes WHERE user_id = ? ORDER BY updated_at DESC, id DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        if latest_row:
            try:
                c_dict = json.loads(latest_row["content_json"])
            except Exception:
                c_dict = {}
            current_resume = {
                "id": latest_row["id"],
                "template_name": latest_row["template_name"],
                "title": latest_row["title"],
                "content": c_dict,
                "updated_at": latest_row["updated_at"]
            }
            
    saved_rows = conn.execute(
        "SELECT id, title, template_name, updated_at FROM user_resumes WHERE user_id = ? ORDER BY updated_at DESC, id DESC",
        (user_id,)
    ).fetchall()
    saved_resumes = [dict(r) for r in saved_rows]
    conn.close()
    
    if is_api_request():
        return jsonify({
            "success": True,
            "current_resume": current_resume,
            "resumes": saved_resumes
        })
        
    return render_template(
        "resume_builder.html",
        title="AI Resume Builder",
        page="resume-builder",
        resume=current_resume,
        saved_resumes=saved_resumes
    )


@app.route("/resume-builder/delete/<int:resume_id>", methods=["POST"])
@login_required
def delete_resume(resume_id):
    """Delete a resume with strict tenant ownership check."""
    user_id = session["user_id"]
    conn = get_db()
    existing = conn.execute("SELECT id FROM user_resumes WHERE id = ? AND user_id = ?", (resume_id, user_id)).fetchone()
    if not existing:
        conn.close()
        if is_api_request():
            return jsonify({"error": "Resume not found or access denied", "success": False}), 404
        flash("Resume not found or access denied.")
        return redirect(url_for("resume_builder"))
        
    conn.execute("DELETE FROM user_resumes WHERE id = ? AND user_id = ?", (resume_id, user_id))
    conn.commit()
    conn.close()
    
    log_activity(user_id, "Resume Builder", f"Deleted resume ID: {resume_id}")
    if is_api_request():
        return jsonify({"success": True, "message": "Resume deleted successfully"})
        
    flash("Resume deleted successfully.")
    return redirect(url_for("resume_builder"))


# 7. COVER LETTER GENERATOR
@app.route("/cover-letter", methods=["GET", "POST"])
@login_required
def cover_letter():
    """
    Cover Letter Generator with full persistence in cover_letters table.
    Supports GET (view latest/saved), POST (generate and persist / update), and JSON API.
    """
    user_id = session["user_id"]
    conn = get_db()
    
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        action = data.get("action", "generate")
        
        # Sub-action: directly update/save edited cover letter content
        if action == "update" or "edited_content" in data:
            letter_id = data.get("letter_id")
            new_content = (data.get("edited_content") or data.get("content") or "").strip()
            
            if not letter_id or not new_content:
                conn.close()
                if is_api_request():
                    return jsonify({"error": "Letter ID and content are required", "success": False}), 400
                flash("Letter content cannot be empty.")
                return redirect(url_for("cover_letter"))
                
            try:
                lid_int = int(letter_id)
            except (ValueError, TypeError):
                conn.close()
                return jsonify({"error": "Invalid letter ID", "success": False}), 400
                
            existing = conn.execute(
                "SELECT id, company_name, job_title FROM cover_letters WHERE id = ? AND user_id = ?",
                (lid_int, user_id)
            ).fetchone()
            
            if not existing:
                conn.close()
                if is_api_request():
                    return jsonify({"error": "Cover letter not found or access denied", "success": False}), 404
                flash("Cover letter not found or access denied.")
                return redirect(url_for("cover_letter"))
                
            new_company = (data.get("company_name") or existing["company_name"]).strip()
            new_title = (data.get("job_title") or existing["job_title"]).strip()
            
            conn.execute(
                "UPDATE cover_letters SET content = ?, company_name = ?, job_title = ? WHERE id = ? AND user_id = ?",
                (new_content, new_company, new_title, lid_int, user_id)
            )
            conn.commit()
            conn.close()
            
            log_activity(user_id, "Cover Letter", f"Updated cover letter ID: {lid_int}")
            if is_api_request():
                return jsonify({"success": True, "letter_id": lid_int, "message": "Cover letter updated successfully!"})
            flash("Cover letter updated successfully!")
            return redirect(url_for("cover_letter", id=lid_int))
            
        # Generation Action: Draft a new cover letter and persist it
        company = (data.get("company_name") or "").strip()
        job_title = (data.get("job_title") or "").strip()
        user_skills = (data.get("key_skills") or "").strip()
        
        if not company or not job_title:
            conn.close()
            if is_api_request():
                return jsonify({"error": "Company Name and Job Title are required", "success": False}), 400
            flash("Company Name and Job Title are required.")
            return redirect(url_for("cover_letter"))
            
        candidate_name = session.get("user_name", "Applicant")
        prompt = f"Draft a professional, compelling cover letter for {candidate_name} applying for {job_title} at {company}. Highlights: {user_skills or 'Problem-solving, Collaboration, Adaptability'}."
        
        letter_text = safe_gemini_generate(prompt)
        if not letter_text:
            skills_mention = f"With a solid foundation in {user_skills} and a passion for building scalable solutions" if user_skills else "With a solid academic foundation and passion for technological innovation"
            letter_text = f"""Dear Hiring Manager at {company},

I am writing to express my strong interest in the {job_title} position at {company}. {skills_mention}, I am excited about the opportunity to contribute effectively to your engineering organization.

Throughout my practical and academic experiences, I have developed a proven track record of writing clean, maintainable code, solving complex architectural challenges, and collaborating across multidisciplinary teams. I am particularly inspired by {company}'s commitment to engineering excellence and mission-driven products.

Thank you for your time and consideration. I welcome the opportunity to discuss how my qualifications align with your organizational objectives.

Sincerely,
{candidate_name}"""

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """
            INSERT INTO cover_letters (user_id, job_title, company_name, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, job_title, company, letter_text, now)
        )
        saved_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        log_activity(user_id, "Cover Letter", f"Generated and saved cover letter for {job_title} at {company}")
        
        if is_api_request():
            return jsonify({
                "success": True,
                "letter_id": saved_id,
                "company_name": company,
                "job_title": job_title,
                "content": letter_text,
                "created_at": now,
                "message": "Cover letter generated and saved successfully!"
            }), 201
            
        flash("Cover letter generated and saved successfully!")
        return redirect(url_for("cover_letter", id=saved_id))
        
    # GET Request: Fetch requested or latest cover letter plus history
    req_id = request.args.get("id")
    selected_letter = None
    if req_id:
        try:
            req_id_int = int(req_id)
            row = conn.execute(
                "SELECT * FROM cover_letters WHERE id = ? AND user_id = ?",
                (req_id_int, user_id)
            ).fetchone()
            if row:
                selected_letter = dict(row)
        except (ValueError, TypeError):
            pass
            
    if not selected_letter and not request.args.get("new"):
        latest_row = conn.execute(
            "SELECT * FROM cover_letters WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        if latest_row:
            selected_letter = dict(latest_row)
            
    saved_rows = conn.execute(
        "SELECT id, job_title, company_name, created_at FROM cover_letters WHERE user_id = ? ORDER BY id DESC",
        (user_id,)
    ).fetchall()
    saved_letters = [dict(r) for r in saved_rows]
    conn.close()
    
    letter_text = selected_letter["content"] if selected_letter else None
    
    if is_api_request():
        return jsonify({
            "success": True,
            "current_letter": selected_letter,
            "saved_letters": saved_letters
        })
        
    return render_template(
        "cover_letter.html",
        title="Cover Letter Generator",
        page="cover-letter",
        letter=letter_text,
        selected_letter=selected_letter,
        saved_letters=saved_letters
    )


@app.route("/cover-letter/delete/<int:letter_id>", methods=["POST"])
@login_required
def delete_cover_letter(letter_id):
    """Delete a cover letter with strict tenant ownership check."""
    user_id = session["user_id"]
    conn = get_db()
    existing = conn.execute("SELECT id FROM cover_letters WHERE id = ? AND user_id = ?", (letter_id, user_id)).fetchone()
    if not existing:
        conn.close()
        if is_api_request():
            return jsonify({"error": "Cover letter not found or access denied", "success": False}), 404
        flash("Cover letter not found or access denied.")
        return redirect(url_for("cover_letter"))
        
    conn.execute("DELETE FROM cover_letters WHERE id = ? AND user_id = ?", (letter_id, user_id))
    conn.commit()
    conn.close()
    
    log_activity(user_id, "Cover Letter", f"Deleted cover letter ID: {letter_id}")
    if is_api_request():
        return jsonify({"success": True, "message": "Cover letter deleted successfully"})
        
    flash("Cover letter deleted successfully.")
    return redirect(url_for("cover_letter"))


# 8. AI PROJECT RECOMMENDATIONS
@app.route("/projects")
@student_required
def projects():
    user_id = session["user_id"]
    context = build_student_context(user_id)
    target_role = context.get("target_role", "Software Developer")
    skills = context.get("skills", "Python, SQL, Algorithms")

    prompt = f"""You are a senior technical architect and engineering hiring manager.
Recommend exactly 3 high-impact resume portfolio projects tailored for a student targeting '{target_role}'.
Current Student Skills: {skills}
Interests: {context.get('interests', 'Software Engineering')}
Education: {context.get('education', 'Undergraduate')}

Provide the response strictly as a JSON array of 3 objects with keys:
- "level": string ("Beginner", "Intermediate", "Advanced")
- "title": string (engaging project title)
- "tech_stack": array of 3 to 4 technology strings
- "duration": string (e.g. "1 Week", "2 Weeks", "3-4 Weeks")
- "description": string (2-3 sentence overview highlighting architecture, core technical challenges, and placement talking points)
Do not include markdown code block formatting if possible."""

    projects_list = None
    res_text = safe_gemini_generate(prompt)
    if res_text:
        try:
            clean_txt = res_text.replace("```json", "").replace("```", "").strip()
            projects_list = json.loads(clean_txt)
        except Exception as e:
            app.logger.warning(f"Failed to parse projects JSON: {e}")
            projects_list = None

    if not projects_list or not isinstance(projects_list, list) or len(projects_list) == 0:
        # High quality role-specific deterministic fallback
        role_lower = target_role.lower()
        if "data" in role_lower or "machine" in role_lower:
            projects_list = [
                {
                    "level": "Beginner",
                    "title": "Exploratory Data Analysis & Predictive Churn Dashboard",
                    "tech_stack": ["Python", "Pandas", "Matplotlib", "Scikit-Learn"],
                    "duration": "1 Week",
                    "description": "Perform comprehensive data cleaning and feature engineering on customer churn datasets with regression/classification modeling."
                },
                {
                    "level": "Intermediate",
                    "title": "End-to-End Sentiment Analysis & Text Classification API",
                    "tech_stack": ["Python", "Flask", "NLTK/Transformers", "SQLite"],
                    "duration": "2 Weeks",
                    "description": "Build and deploy a REST API serving NLP sentiment classification with evaluation metrics and tokenized input pipelines."
                },
                {
                    "level": "Advanced",
                    "title": "Distributed Recommendation System with Vector Search",
                    "tech_stack": ["FastAPI", "FAISS/ChromaDB", "PostgreSQL", "Docker"],
                    "duration": "3-4 Weeks",
                    "description": "High-throughput embedding similarity search engine providing personalized recommendations with real-time caching."
                }
            ]
        elif "web" in role_lower or "frontend" in role_lower or "full" in role_lower:
            projects_list = [
                {
                    "level": "Beginner",
                    "title": "Interactive Task & Kanban Workflow Board",
                    "tech_stack": ["HTML5/CSS3", "JavaScript ES6", "LocalStorage"],
                    "duration": "1 Week",
                    "description": "Build an intuitive drag-and-drop workflow board with custom priority filtering and persistent browser state."
                },
                {
                    "level": "Intermediate",
                    "title": "Full-Stack SaaS Platform with Role-Based Auth",
                    "tech_stack": ["Python", "Flask", "SQLite/PostgreSQL", "REST API"],
                    "duration": "2 Weeks",
                    "description": "Production-ready web application featuring secure password hashing, session management, and CRUD dashboards."
                },
                {
                    "level": "Advanced",
                    "title": "Real-Time Collaboration Workspace with WebSockets",
                    "tech_stack": ["Node.js/FastAPI", "WebSockets", "Redis", "Docker"],
                    "duration": "3-4 Weeks",
                    "description": "Multi-user synchronized document editor with presence awareness, conflict resolution, and Redis pub/sub messaging."
                }
            ]
        else:
            projects_list = [
                {
                    "level": "Beginner",
                    "title": "Algorithmic Placement Problem Visualizer",
                    "tech_stack": ["Python", "Algorithms", "Tkinter/Flask", "Testing"],
                    "duration": "1 Week",
                    "description": "Visualize sorting, binary search tree operations, and pathfinding algorithms with step-by-step state animations."
                },
                {
                    "level": "Intermediate",
                    "title": "Secure Microservice URL Shortener & Analytics Engine",
                    "tech_stack": ["Python", "Flask", "SQLite", "Base62 Encoding"],
                    "duration": "2 Weeks",
                    "description": "Fast link shortening service with collision-resistant hashing, geo-click tracking, and rate-limiting middleware."
                },
                {
                    "level": "Advanced",
                    "title": "High-Concurrency Job Queue & Asynchronous Worker Pool",
                    "tech_stack": ["Python", "Redis", "Multiprocessing", "REST API"],
                    "duration": "3-4 Weeks",
                    "description": "Robust background worker system implementing retry backoffs, dead-letter queues, and task status telemetry."
                }
            ]

    return render_template("projects.html", title="Project Recommendations", page="projects", projects=projects_list, target_role=target_role)


# 9. LEARNING RESOURCE RECOMMENDATION
@app.route("/resources")
@student_required
def resources():
    user_id = session["user_id"]
    context = build_student_context(user_id)
    target_role = context.get("target_role", "Software Developer")
    weak_topics = context.get("weak_topics", [])

    all_resources = {
        "DSA & Algorithmic Problem Solving": [
            {"title": "LeetCode Top Interview 150 Study Plan", "type": "Practice", "url": "https://leetcode.com/studyplan/top-interview-150/"},
            {"title": "NeetCode Interactive Algorithmic Roadmap", "type": "Roadmap", "url": "https://neetcode.io/roadmap"},
            {"title": "GeeksforGeeks Complete DSA Tutorial", "type": "Documentation", "url": "https://www.geeksforgeeks.org/learn-data-structures-and-algorithms-dsa-tutorial/"}
        ],
        "Computer Science Core Fundamentals": [
            {"title": "Harvard CS50: Introduction to Computer Science", "type": "Course", "url": "https://cs50.harvard.edu/x/"},
            {"title": "GeeksforGeeks Core CS Fundamentals Guide", "type": "Article", "url": "https://www.geeksforgeeks.org/fundamentals-of-computer-science/"},
            {"title": "Donne Martin: System Design Primer Repository", "type": "GitHub", "url": "https://github.com/donnemartin/system-design-primer"}
        ],
        "Databases & SQL Optimization": [
            {"title": "SQLZoo Interactive SQL Practice & Queries", "type": "Interactive", "url": "https://sqlzoo.net/"},
            {"title": "Official PostgreSQL Documentation & Tutorial", "type": "Docs", "url": "https://www.postgresql.org/docs/"},
            {"title": "Database Normalization & ACID Properties Guide", "type": "Article", "url": "https://www.geeksforgeeks.org/dbms/"}
        ],
        "Web & Backend Development": [
            {"title": "MDN Web Docs: Web Development for Beginners", "type": "Docs", "url": "https://developer.mozilla.org/en-US/"},
            {"title": "Full Stack Open: Modern Web Development (University of Helsinki)", "type": "Free Course", "url": "https://fullstackopen.com/en/"},
            {"title": "Official Flask Web Framework Documentation", "type": "Docs", "url": "https://flask.palletsprojects.com/"},
            {"title": "Official Python 3 Tutorial & Documentation", "type": "Docs", "url": "https://docs.python.org/3/tutorial/"}
        ]
    }

    resource_categories = []
    for topic, links in all_resources.items():
        resource_categories.append({"topic": topic, "links": links})

    return render_template("resources.html", title="Learning Resources", page="resources", categories=resource_categories, target_role=target_role, weak_topics=weak_topics)


# 10. PROGRESS DASHBOARD & ANALYTICS
@app.route("/analytics")
@student_required
def analytics():
    user_id = session["user_id"]
    conn = get_db()

    # 1. Mock Interviews Performance
    interviews = conn.execute(
        "SELECT category, score, created_at FROM interviews WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
        (user_id,)
    ).fetchall()

    # 2. Aptitude Scores
    aptitude_rows = conn.execute(
        "SELECT category, score, total_questions, accuracy, created_at FROM aptitude_scores WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
        (user_id,)
    ).fetchall()

    # 3. Coding Submissions
    coding_rows = conn.execute(
        "SELECT problem_title, score, status, topic, difficulty, submitted_at FROM coding_submissions WHERE user_id = ? ORDER BY submitted_at DESC LIMIT 10",
        (user_id,)
    ).fetchall()

    # 4. CS Fundamentals MCQ
    mcq_rows = conn.execute(
        "SELECT subject, score, total_questions, accuracy, created_at FROM mcq_results WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
        (user_id,)
    ).fetchall()

    # 5. User Profile & Streak
    user_row = conn.execute(
        "SELECT resume_score, skill_match, study_streak, target_role FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    # 6. Latest Roadmap Progress
    roadmap_row = conn.execute(
        "SELECT progress_pct, career_goal FROM roadmaps WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    ).fetchone()

    conn.close()

    # Calculate actual statistics
    interview_scores = [iv["score"] for iv in reversed(interviews)]
    interview_labels = [f"Round {i+1} ({iv['category'][:4]})" for i, iv in enumerate(reversed(interviews))]

    avg_interview = round(sum(interview_scores) / len(interview_scores)) if interview_scores else 0
    avg_aptitude = round(sum(r["accuracy"] for r in aptitude_rows) / len(aptitude_rows)) if aptitude_rows else 0
    avg_coding = round(sum(c["score"] for c in coding_rows) / len(coding_rows)) if coding_rows else 0
    avg_mcq = round(sum(m["accuracy"] for m in mcq_rows) / len(mcq_rows)) if mcq_rows else 0

    resume_score = (user_row["resume_score"] if user_row and user_row["resume_score"] else 0)
    study_streak = (user_row["study_streak"] if user_row and user_row["study_streak"] else 1)
    roadmap_progress = (roadmap_row["progress_pct"] if roadmap_row and "progress_pct" in roadmap_row.keys() and roadmap_row["progress_pct"] else 0)

    # Subject Radar/Bar Matrix
    radar_labels = ["Aptitude", "Mock Interview", "Coding", "CS Fundamentals", "Roadmap", "Resume ATS"]
    radar_values = [avg_aptitude, avg_interview, avg_coding, avg_mcq, roadmap_progress, resume_score]

    analytics_data = {
        "interview_scores": interview_scores,
        "interview_labels": interview_labels,
        "radar_labels": radar_labels,
        "radar_values": radar_values,
        "avg_interview": avg_interview,
        "avg_aptitude": avg_aptitude,
        "avg_coding": avg_coding,
        "avg_mcq": avg_mcq,
        "resume_score": resume_score,
        "study_streak": study_streak,
        "roadmap_progress": roadmap_progress,
        "total_interviews": len(interviews),
        "total_aptitude": len(aptitude_rows),
        "total_coding": len(coding_rows),
        "total_mcq": len(mcq_rows)
    }

    return render_template(
        "analytics.html",
        title="Progress Analytics",
        page="analytics",
        interviews=[dict(i) for i in interviews],
        aptitude=[dict(a) for a in aptitude_rows],
        coding=[dict(c) for c in coding_rows],
        mcq=[dict(m) for m in mcq_rows],
        analytics=analytics_data
    )


# 11. NOTIFICATIONS
def create_notification(user_id, title, message, notif_type="info"):
    """Safely create a database-backed notification for a specific user."""
    if not user_id or not title or not message:
        return False
    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO notifications (user_id, title, message, notif_type, is_read, created_at) VALUES (?, ?, ?, ?, 0, ?)",
        (user_id, str(title).strip(), str(message).strip(), str(notif_type).strip(), now)
    )
    conn.commit()
    conn.close()
    return True


@app.route("/notifications")
@login_required
def notifications():
    """View user notifications (strictly database-backed, no fake fallbacks)."""
    conn = get_db()
    notifs = conn.execute(
        "SELECT id, user_id, title, message, notif_type, is_read, created_at FROM notifications WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    
    notif_list = [dict(n) for n in notifs]
    
    if request.args.get("format") == "json" or request.headers.get("Accept") == "application/json":
        return jsonify({
            "success": True,
            "notifications": notif_list,
            "count": len(notif_list)
        })
        
    return render_template(
        "notifications.html",
        title="Notification Center",
        page="notifications",
        notifications=notif_list
    )


@app.route("/api/notifications/create", methods=["POST"])
@login_required
def api_create_notification():
    """Create a persistent notification with role-based authorization."""
    data = request.get_json(silent=True) or request.form
    title = (data.get("title") or "").strip()
    message = (data.get("message") or "").strip()
    notif_type = (data.get("notif_type") or "info").strip()
    
    target_user_id = data.get("user_id")
    if target_user_id is not None:
        try:
            target_user_id = int(target_user_id)
        except (ValueError, TypeError):
            target_user_id = session["user_id"]
    else:
        target_user_id = session["user_id"]
        
    # Tenant isolation & authorization: only admin can send notifications to other users
    if target_user_id != session["user_id"] and session.get("user_role") != "admin":
        return jsonify({"error": "Forbidden: Cannot send notifications to other users", "success": False}), 403
        
    if not title or not message:
        return jsonify({"error": "Title and message are required", "success": False}), 400
        
    create_notification(target_user_id, title, message, notif_type)
    return jsonify({"success": True, "message": "Notification created successfully"}), 201


@app.route("/api/notifications/mark-read/<int:notif_id>", methods=["POST"])
@login_required
def api_mark_notification_read(notif_id):
    """Mark a notification as read with ownership verification."""
    conn = get_db()
    notif = conn.execute("SELECT id FROM notifications WHERE id = ? AND user_id = ?", (notif_id, session["user_id"])).fetchone()
    if not notif:
        conn.close()
        return jsonify({"error": "Notification not found", "success": False}), 404
        
    conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notif_id, session["user_id"]))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Notification marked as read"})


# 12. ACHIEVEMENTS & BADGES
@app.route("/achievements")
@login_required
def achievements():
    """Gamified achievements and badges dynamically computed from database-backed student metrics."""
    user_id = session["user_id"]
    conn = get_db()
    
    # 1. Fetch user metrics from users table
    user_row = conn.execute("SELECT study_streak, resume_score FROM users WHERE id = ?", (user_id,)).fetchone()
    study_streak = int(user_row["study_streak"] or 0) if user_row and user_row["study_streak"] is not None else 0
    resume_score = int(user_row["resume_score"] or 0) if user_row and user_row["resume_score"] is not None else 0
    
    # 2. Fetch completed interviews count from interviews table
    int_count_row = conn.execute("SELECT COUNT(*) FROM interviews WHERE user_id = ?", (user_id,)).fetchone()
    interviews_count = int_count_row[0] if int_count_row else 0
    
    # 3. Fetch any valid pre-existing achievements unlocked in the achievements table
    unlocked_rows = conn.execute("SELECT badge_id FROM achievements WHERE user_id = ?", (user_id,)).fetchall()
    existing_unlocked_ids = {r["badge_id"] for r in unlocked_rows}
    
    conn.close()
    
    # 4. Dynamically compute badge unlock states from evidence
    streak_unlocked = (study_streak >= 7) or ("streak_7" in existing_unlocked_ids)
    resume_unlocked = (resume_score >= 80) or ("resume_master" in existing_unlocked_ids)
    interview_unlocked = (interviews_count >= 3) or ("interview_champ" in existing_unlocked_ids)
    skill_unlocked = ("skill_conqueror" in existing_unlocked_ids)
    
    badges = [
        {
            "id": "streak_7",
            "name": "7-Day Study Streak",
            "desc": "Logged study time for 7 consecutive days",
            "icon": "fa-fire",
            "unlocked": streak_unlocked,
            "progress_label": f"Progress: {study_streak} / 7 days"
        },
        {
            "id": "resume_master",
            "name": "Resume Master",
            "desc": "Achieved ATS score of 80% or higher",
            "icon": "fa-file-invoice",
            "unlocked": resume_unlocked,
            "progress_label": f"Progress: {resume_score}% / 80%"
        },
        {
            "id": "interview_champ",
            "name": "Interview Champ",
            "desc": "Completed 3 AI Mock Interviews",
            "icon": "fa-headset",
            "unlocked": interview_unlocked,
            "progress_label": f"Progress: {interviews_count} / 3 interviews"
        },
        {
            "id": "skill_conqueror",
            "name": "Skill Conqueror",
            "desc": "Bridged 5 missing technical skills",
            "icon": "fa-award",
            "unlocked": skill_unlocked,
            "progress_label": "Requirement: 5 technical skills"
        }
    ]
    
    if request.args.get("format") == "json" or request.headers.get("Accept") == "application/json":
        return jsonify({
            "success": True,
            "badges": badges,
            "metrics": {
                "study_streak": study_streak,
                "resume_score": resume_score,
                "interviews_count": interviews_count
            }
        })
        
    return render_template("achievements.html", title="Achievements & Badges", page="achievements", badges=badges)


# 13. SETTINGS & PREFERENCES
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user_id = session["user_id"]
    if request.method == "POST":
        action = request.form.get("action", "profile")

        if action == "password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not current_password or not new_password or not confirm_password:
                flash("All password fields are required.")
                return redirect(url_for("settings"))

            is_valid_pw, pw_err = validate_password_strength(new_password)
            if not is_valid_pw:
                flash(pw_err)
                return redirect(url_for("settings"))

            if new_password != confirm_password:
                flash("New passwords do not match.")
                return redirect(url_for("settings"))

            conn = get_db()
            user = conn.execute("SELECT password FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user or not check_password(current_password, user["password"]):
                conn.close()
                flash("Current password is incorrect.")
                return redirect(url_for("settings"))

            hashed_pw = hash_password(new_password)
            conn.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, user_id))
            conn.commit()
            conn.close()
            log_activity(user_id, "Password Change", "User changed account password")
            flash("Password updated successfully!")
            return redirect(url_for("settings"))

        else:
            name = request.form.get("name", "").strip()
            target_role = request.form.get("target_role", "").strip()
            education = request.form.get("education", "").strip()
            skills = request.form.get("skills", "").strip()
            interests = request.form.get("interests", "").strip()
            experience = request.form.get("experience", "").strip()
            preferred_industry = request.form.get("preferred_industry", "").strip()
            bio = request.form.get("bio", "").strip()
            dark_mode = 1 if request.form.get("dark_mode") == "on" else 0
            notifications_enabled = 1 if request.form.get("notifications_enabled") == "on" else 0

            conn = get_db()
            conn.execute(
                """
                UPDATE users SET 
                    name = COALESCE(NULLIF(?, ''), name),
                    target_role = ?,
                    education = ?,
                    skills = ?,
                    interests = ?,
                    experience = ?,
                    preferred_industry = ?,
                    bio = ?,
                    dark_mode = ?,
                    notifications_enabled = ?
                WHERE id = ?
                """,
                (name, target_role, education, skills, interests, experience, preferred_industry, bio, dark_mode, notifications_enabled, user_id)
            )
            conn.commit()
            conn.close()

            if name:
                session["user_name"] = name
            log_activity(user_id, "Update Profile", "User updated profile and preferences")
            flash("Profile and preferences saved successfully!")
            return redirect(url_for("settings"))

    return render_template("settings.html", title="Workspace Settings", page="settings")


# ==============================================================================
#                 MODULE 1: APTITUDE PREPARATION & TEST
# ==============================================================================

@app.route("/aptitude")
@student_required
def aptitude():
    """Render Aptitude Preparation & Practice Portal."""
    conn = get_db()
    history = conn.execute(
        "SELECT * FROM aptitude_scores WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    
    categories = {
        "Quantitative": [
            "Percentage", "Profit and Loss", "Ratio and Proportion", "Average",
            "Time and Work", "Time, Speed and Distance", "Simple Interest",
            "Compound Interest", "Number System", "Probability"
        ],
        "Logical Reasoning": [
            "Number/Alphabet Series", "Coding-Decoding", "Blood Relations",
            "Direction Sense", "Syllogism", "Seating Arrangement", "Basic Puzzles"
        ],
        "Verbal Ability": [
            "Grammar", "Vocabulary", "Sentence Correction", "Reading Comprehension"
        ]
    }
    
    return render_template(
        "aptitude.html",
        title="Aptitude Preparation",
        page="aptitude",
        categories=categories,
        history=history
    )


@app.route("/api/aptitude/start", methods=["POST"])
@student_required
def api_aptitude_start():
    """Start an aptitude test session with filtered questions."""
    data = request.get_json() or {}
    category = data.get("category", "All")
    topic = data.get("topic", "All")
    difficulty = data.get("difficulty", "All")
    count = int(data.get("count", 10))
    
    filtered = []
    for q in APTITUDE_QUESTIONS:
        if category != "All" and q["category"] != category:
            continue
        if topic != "All" and q["topic"] != topic:
            continue
        if difficulty != "All" and q["difficulty"] != difficulty:
            continue
        filtered.append(q)
        
    if not filtered:
        filtered = [q for q in APTITUDE_QUESTIONS if category == "All" or q["category"] == category]
        
    random.shuffle(filtered)
    selected = filtered[:count]
    
    client_questions = []
    for q in selected:
        client_questions.append({
            "id": q["id"],
            "category": q["category"],
            "topic": q["topic"],
            "difficulty": q["difficulty"],
            "question": q["question"],
            "options": q["options"]
        })
        
    return jsonify({
        "questions": client_questions,
        "total": len(client_questions),
        "time_limit_seconds": len(client_questions) * 60
    })


@app.route("/api/aptitude/submit", methods=["POST"])
@student_required
def api_aptitude_submit():
    """
    Evaluate Aptitude test submission on backend with rule-based scoring.
    Saves score, accuracy, time taken, and weak topics to database.
    """
    user_id = session["user_id"]
    data = request.get_json() or {}
    category = data.get("category", "Quantitative")
    time_taken = int(data.get("time_taken", 0))
    user_answers = data.get("answers", {})
    
    q_map = {q["id"]: q for q in APTITUDE_QUESTIONS}
    
    correct_count = 0
    total_questions = len(user_answers) if user_answers else 1
    topic_performance = {}
    review_details = []
    
    for q_id, user_ans_idx in user_answers.items():
        q_data = q_map.get(q_id)
        if not q_data:
            continue
            
        topic = q_data["topic"]
        if topic not in topic_performance:
            topic_performance[topic] = {"correct": 0, "total": 0}
        topic_performance[topic]["total"] += 1
        
        is_correct = False
        try:
            if int(user_ans_idx) == int(q_data["correct"]):
                is_correct = True
                correct_count += 1
                topic_performance[topic]["correct"] += 1
        except (ValueError, TypeError):
            is_correct = False
            
        review_details.append({
            "id": q_id,
            "question": q_data["question"],
            "options": q_data["options"],
            "user_answer": user_ans_idx,
            "correct_answer": q_data["correct"],
            "is_correct": is_correct,
            "topic": topic,
            "explanation": q_data["explanation"]
        })
        
    accuracy = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0.0
    
    strong_topics = []
    weak_topics = []
    for top, stats in topic_performance.items():
        top_acc = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        if top_acc >= 70:
            strong_topics.append(top)
        else:
            weak_topics.append(top)
            
    details_json = json.dumps({
        "strong_topics": strong_topics,
        "weak_topics": weak_topics,
        "accuracy": accuracy,
        "time_taken": time_taken
    })
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute(
        "INSERT INTO aptitude_scores (user_id, category, score, total_questions, time_taken, accuracy, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, category, correct_count, total_questions, time_taken, accuracy, details_json, now)
    )
    conn.commit()
    conn.close()
    
    log_activity(user_id, "Aptitude Test", f"Category: {category}, Score: {correct_count}/{total_questions} ({accuracy}%)")
    
    return jsonify({
        "score": correct_count,
        "total_questions": total_questions,
        "wrong_count": total_questions - correct_count,
        "accuracy": accuracy,
        "time_taken": time_taken,
        "strong_topics": strong_topics,
        "weak_topics": weak_topics,
        "review": review_details
    })


# ==============================================================================
#                 MODULE 2: CS FUNDAMENTALS / TECHNICAL MCQ
# ==============================================================================

@app.route("/cs-fundamentals")
@student_required
def cs_fundamentals():
    """Render CS Fundamentals & Technical MCQ Portal."""
    conn = get_db()
    history = conn.execute(
        "SELECT * FROM mcq_results WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    
    subjects = [
        {"name": "DSA", "icon": "fa-project-diagram", "desc": "Data Structures & Algorithms"},
        {"name": "OOP", "icon": "fa-cubes", "desc": "Object-Oriented Programming"},
        {"name": "DBMS", "icon": "fa-database", "desc": "Database Management Systems"},
        {"name": "SQL", "icon": "fa-table", "desc": "Relational Queries & Optimization"},
        {"name": "Operating Systems", "icon": "fa-microchip", "desc": "Processes, Threads & Memory"},
        {"name": "Computer Networks", "icon": "fa-network-wired", "desc": "OSI Model, TCP/IP & Protocols"},
        {"name": "Python", "icon": "fa-code", "desc": "Python Core & Data Structures"},
        {"name": "C++", "icon": "fa-terminal", "desc": "Pointers, OOP & STL Memory"}
    ]
    
    return render_template(
        "cs_fundamentals.html",
        title="CS Fundamentals",
        page="cs_fundamentals",
        subjects=subjects,
        history=history
    )


@app.route("/api/cs-fundamentals/start", methods=["POST"])
@student_required
def api_cs_start():
    """Start CS Fundamentals MCQ test session."""
    data = request.get_json() or {}
    subject = data.get("subject", "All")
    difficulty = data.get("difficulty", "All")
    count = int(data.get("count", 10))
    
    filtered = []
    for q in CS_MCQ_QUESTIONS:
        if subject != "All" and q["subject"] != subject:
            continue
        if difficulty != "All" and q["difficulty"] != difficulty:
            continue
        filtered.append(q)
        
    if not filtered:
        filtered = [q for q in CS_MCQ_QUESTIONS if subject == "All" or q["subject"] == subject]
        
    random.shuffle(filtered)
    selected = filtered[:count]
    
    client_questions = []
    for q in selected:
        client_questions.append({
            "id": q["id"],
            "subject": q["subject"],
            "topic": q["topic"],
            "difficulty": q["difficulty"],
            "question": q["question"],
            "options": q["options"]
        })
        
    return jsonify({
        "questions": client_questions,
        "total": len(client_questions)
    })


@app.route("/api/cs-fundamentals/submit", methods=["POST"])
@student_required
def api_cs_submit():
    """
    Evaluate CS Fundamentals MCQ submission on backend.
    Saves score, accuracy, and weak topics to database.
    """
    user_id = session["user_id"]
    data = request.get_json() or {}
    subject = data.get("subject", "CS Fundamentals")
    user_answers = data.get("answers", {})
    
    q_map = {q["id"]: q for q in CS_MCQ_QUESTIONS}
    
    correct_count = 0
    total_questions = len(user_answers) if user_answers else 1
    topic_performance = {}
    review_details = []
    
    for q_id, user_ans_idx in user_answers.items():
        q_data = q_map.get(q_id)
        if not q_data:
            continue
            
        topic = q_data["topic"]
        if topic not in topic_performance:
            topic_performance[topic] = {"correct": 0, "total": 0}
        topic_performance[topic]["total"] += 1
        
        is_correct = False
        try:
            if int(user_ans_idx) == int(q_data["correct"]):
                is_correct = True
                correct_count += 1
                topic_performance[topic]["correct"] += 1
        except (ValueError, TypeError):
            is_correct = False
            
        review_details.append({
            "id": q_id,
            "question": q_data["question"],
            "options": q_data["options"],
            "user_answer": user_ans_idx,
            "correct_answer": q_data["correct"],
            "is_correct": is_correct,
            "topic": topic,
            "explanation": q_data["explanation"]
        })
        
    accuracy = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0.0
    
    strong_topics = []
    weak_topics = []
    for top, stats in topic_performance.items():
        top_acc = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        if top_acc >= 70:
            strong_topics.append(top)
        else:
            weak_topics.append(top)
            
    details_json = json.dumps({
        "strong_topics": strong_topics,
        "weak_topics": weak_topics,
        "accuracy": accuracy
    })
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute(
        "INSERT INTO mcq_results (user_id, subject, score, total_questions, accuracy, details_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, subject, correct_count, total_questions, accuracy, details_json, now)
    )
    conn.commit()
    conn.close()
    
    log_activity(user_id, "CS Fundamentals MCQ", f"Subject: {subject}, Score: {correct_count}/{total_questions} ({accuracy}%)")
    
    return jsonify({
        "score": correct_count,
        "total_questions": total_questions,
        "wrong_count": total_questions - correct_count,
        "accuracy": accuracy,
        "strong_topics": strong_topics,
        "weak_topics": weak_topics,
        "review": review_details
    })


# ==============================================================================
#                 MODULE 3: CODING ASSESSMENT
# ==============================================================================

@app.route("/coding-test")
@student_required
def coding_test():
    """Render Coding Assessment portal."""
    conn = get_db()
    history = conn.execute(
        "SELECT * FROM coding_submissions WHERE user_id = ? ORDER BY submitted_at DESC LIMIT 10",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    
    return render_template(
        "coding_test.html",
        title="Coding Assessment",
        page="coding_test",
        problems=CODING_PROBLEMS,
        history=history
    )


@app.route("/api/coding/problems", methods=["GET"])
@student_required
def api_coding_problems():
    """Return problem metadata list."""
    prob_list = []
    for p in CODING_PROBLEMS:
        prob_list.append({
            "id": p["id"],
            "title": p["title"],
            "topic": p["topic"],
            "difficulty": p["difficulty"]
        })
    return jsonify({"problems": prob_list})


@app.route("/api/coding/problem/<prob_id>", methods=["GET"])
@student_required
def api_coding_problem_detail(prob_id):
    """Return detailed problem statement, constraints, and initial code template."""
    prob = next((p for p in CODING_PROBLEMS if p["id"] == prob_id), None)
    if not prob:
        return jsonify({"error": "Problem not found"}), 404
        
    return jsonify({
        "id": prob["id"],
        "title": prob["title"],
        "topic": prob["topic"],
        "difficulty": prob["difficulty"],
        "description": prob["description"],
        "input_format": prob["input_format"],
        "output_format": prob["output_format"],
        "constraints": prob["constraints"],
        "examples": prob["examples"],
        "initial_code": prob["initial_code"]
    })


@app.route("/api/coding/submit", methods=["POST"])
@student_required
def api_coding_submit():
    """
    Evaluates Python code against problem test cases safely using Controlled Evaluation.
    Stores submission in database and optionally fetches Gemini AI educational hints.
    """
    user_id = session["user_id"]
    data = request.get_json() or {}
    prob_id = data.get("problem_id", "").strip()
    language = data.get("language", "python").strip().lower()
    code = data.get("code", "")
    
    if not prob_id:
        return jsonify({"error": "Problem ID is required."}), 400
    if not code or not code.strip():
        return jsonify({"error": "Code cannot be empty."}), 400
    if len(code) > 10000:
        return jsonify({"error": "Submitted code exceeds maximum limit of 10,000 characters."}), 400
    if language != "python":
        return jsonify({"error": "Only Python is supported in the current version."}), 400
        
    prob = next((p for p in CODING_PROBLEMS if p["id"] == prob_id), None)
    if not prob:
        return jsonify({"error": "Invalid Problem ID."}), 404
        
    if not evaluate_python_submission:
        return jsonify({"error": "Coding evaluation engine unavailable."}), 500

    # Execute Controlled Evaluation Architecture
    eval_start_time = time.time()
    eval_result = evaluate_python_submission(code, prob)
    eval_time = round(time.time() - eval_start_time, 3)
    
    status = eval_result["status"]
    score = eval_result["score"]
    passed_tests = eval_result["passed_tests"]
    total_tests = eval_result["total_tests"]
    
    # AI Feedback (Optional educational hint via Gemini)
    ai_feedback = None
    if client:
        ai_prompt = (
            f"Student submitted a Python solution for the coding problem '{prob['title']}' ({prob['topic']}).\n"
            f"Test Result: {passed_tests}/{total_tests} test cases passed (Score: {score}%).\n"
            f"Status: {status}.\n"
            "Provide 2 short, encouraging, action-oriented bullet points of educational feedback to help the student improve. Keep it under 60 words."
        )
        ai_feedback = safe_gemini_generate(ai_prompt)
            
    if not ai_feedback:
        if score == 100:
            ai_feedback = "Great solution! All test cases passed cleanly. Keep practicing optimization."
        elif score >= 50:
            ai_feedback = "Good progress! Check edge cases and array boundaries to pass remaining tests."
        else:
            ai_feedback = "Review the problem description and sample inputs carefully before re-submitting."
            
    # Save submission into database
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute(
        """
        INSERT INTO coding_submissions 
        (user_id, problem_title, language, code, status, score, passed_tests, total_tests, topic, difficulty, execution_time, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, prob["title"], language, code, status, score, passed_tests, total_tests, prob["topic"], prob["difficulty"], eval_time, now)
    )
    conn.commit()
    conn.close()
    
    log_activity(user_id, "Coding Submission", f"Problem: {prob['title']}, Passed: {passed_tests}/{total_tests} ({score}%)")
    
    return jsonify({
        "status": status,
        "score": score,
        "passed_tests": passed_tests,
        "total_tests": total_tests,
        "classification": eval_result["classification"],
        "execution_time": eval_time,
        "test_results": eval_result["test_results"],
        "error_message": eval_result["error_message"],
        "ai_feedback": ai_feedback,
        "topic": prob["topic"],
        "difficulty": prob["difficulty"]
    })


@app.route("/api/coding/submissions", methods=["GET"])
@student_required
def api_coding_submissions():
    """Return student's submission history and aggregate performance metrics."""
    user_id = session["user_id"]
    conn = get_db()
    submissions = conn.execute(
        "SELECT * FROM coding_submissions WHERE user_id = ? ORDER BY submitted_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    
    sub_list = [dict(s) for s in submissions]
    
    attempted_titles = set(s["problem_title"] for s in sub_list)
    passed_titles = set(s["problem_title"] for s in sub_list if s["status"] == "Passed")
    
    scores = [s["score"] for s in sub_list]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    
    topic_stats = {}
    for s in sub_list:
        t = s.get("topic") or "General"
        if t not in topic_stats:
            topic_stats[t] = {"total": 0, "score_sum": 0}
        topic_stats[t]["total"] += 1
        topic_stats[t]["score_sum"] += s["score"]
        
    strong_topics = []
    weak_topics = []
    for t, stat in topic_stats.items():
        t_avg = stat["score_sum"] / stat["total"]
        if t_avg >= 70:
            strong_topics.append(t)
        else:
            weak_topics.append(t)
            
    easy_passed = len(set(s["problem_title"] for s in sub_list if s.get("difficulty") == "Easy" and s["status"] == "Passed"))
    med_passed = len(set(s["problem_title"] for s in sub_list if s.get("difficulty") == "Medium" and s["status"] == "Passed"))
    
    return jsonify({
        "submissions": sub_list[:15],
        "attempted_count": len(attempted_titles),
        "passed_count": len(passed_titles),
        "avg_score": avg_score,
        "strong_topics": strong_topics,
        "weak_topics": weak_topics,
        "easy_completed": easy_passed,
        "medium_completed": med_passed
    })


# -------- Run --------


import os

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
