# -------------------- IMPORTS --------------------
import os
import sqlite3
import time
import random
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv
from google import genai
import PyPDF2
import docx

# -------------------- ENV LOAD --------------------
load_dotenv()

# Debug check (optional - baad me hata dena)
print("API KEY:", os.getenv("GEMINI_API_KEY"))

# -------------------- FLASK APP --------------------
app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# -------------------- GEMINI CLIENT --------------------
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

# Configure Gemini AI using the new Google GenAI SDK
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY not found in environment.")
    client = None
DATABASE = "database.db"

CAREER_SKILLS = {
    "Data Scientist": ["python", "pandas", "machine learning", "sql", "statistics"],
    "Web Developer": ["html", "css", "javascript", "git", "react"],
    "Machine Learning Engineer": ["python", "machine learning", "deep learning", "tensorflow"],
    "Software Developer": ["data structures", "algorithms", "python", "git"]
}

# Default admin
ADMIN_EMAIL = "npuja3800@gmail.com"
ADMIN_PASSWORD = "puja123"


def get_db():
    """Get SQLite connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
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
    # Migrate: Check if 'created_at' column exists in 'users' table
    cursor = conn.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    if "created_at" not in columns:
        try:
            conn.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
            conn.commit()
            print("Migration: Added 'created_at' column to 'users' table.")
        except sqlite3.OperationalError as e:
            print(f"Migration error: {e}")
    
    # Update existing users where created_at is NULL
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("UPDATE users SET created_at = ? WHERE created_at IS NULL", (now,))
    conn.commit()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    # Migration: Add is_pinned if missing
    cursor = conn.execute("PRAGMA table_info(chat_history)")
    chat_columns = [row[1] for row in cursor.fetchall()]
    if "is_pinned" not in chat_columns:
        conn.execute("ALTER TABLE chat_history ADD COLUMN is_pinned INTEGER DEFAULT 0")
    
    conn.commit()
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
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
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
    # Migration: Check if new columns exist
    cursor = conn.execute("PRAGMA table_info(announcements)")
    ann_columns = [row[1] for row in cursor.fetchall()]
    if "app_link" not in ann_columns:
        conn.execute("ALTER TABLE announcements ADD COLUMN app_link TEXT")
    if "deadline" not in ann_columns:
        conn.execute("ALTER TABLE announcements ADD COLUMN deadline TEXT")
    
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
    conn.commit()
    cursor = conn.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,))
    if cursor.fetchone() is None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO users (name, email, password, role, approved, created_at) VALUES (?, ?, ?, 'admin', 1, ?)",
            ("Admin", ADMIN_EMAIL, hash_password(ADMIN_PASSWORD), now)
        )
        conn.commit()
    conn.close()


def hash_password(password):
    """Simple password hashing using werkzeug."""
    from werkzeug.security import generate_password_hash
    return generate_password_hash(password, method="pbkdf2:sha256")


def check_password(password, hashed):
    """Verify password against hash."""
    from werkzeug.security import check_password_hash
    return check_password_hash(hashed, password)


def login_required(f):
    """Require user to be logged in."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_user():
    """Provide current user to all templates."""
    user = None
    if "user_id" in session:
        user = {
            "name": session.get("user_name", ""),
            "email": session.get("user_email", ""),
            "role": session.get("user_role", "student"),
            "resume_score": session.get("resume_score", 0),
            "initials": "".join(
                w[0] for w in session.get("user_name", "U")[:2].split()
            )[:2].upper() or "U",
        }
    return dict(current_user=user)


def admin_required(f):
    """Require user to be admin."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in as an administrator.")
            return redirect(url_for("admin_login"))
        if session.get("user_role") != "admin":
            flash("Admin access required.")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapped


def student_required(f):
    """Require user to be a student."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to your student account.")
            return redirect(url_for("student_login"))
        if session.get("user_role") != "student":
            flash("Student access required.")
            return redirect(url_for("student_login"))
        return f(*args, **kwargs)
    return wrapped


# -------- Routes --------


@app.route("/")
def index():
    """Landing page with login and signup."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """User registration."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or not password:
            flash("All fields are required.")
            return redirect(url_for("student_login"))
        if len(password) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for("student_login"))
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password, role, approved, created_at) VALUES (?, ?, ?, 'student', 0, ?)",
                (name, email, hash_password(password), now)
            )
            conn.commit()
            user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.close()
            log_activity(user_id, "Signup", "New student registered")
            flash("Your account has been created and is waiting for admin approval.")
            return redirect(url_for("student_login"))
        except sqlite3.IntegrityError:
            conn.close()
            flash("Email already registered.")
            return redirect(url_for("student_login"))
    return redirect(url_for("student_login"))


@app.route("/student-login", methods=["GET", "POST"])
def student_login():
    """Portal-specific student login."""
    if "user_id" in session:
        if session.get("user_role") == "student":
            return redirect(url_for("dashboard"))
        return redirect(url_for("admin"))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        conn = get_db()
        user = conn.execute(
            "SELECT id, name, email, password, role, approved FROM users WHERE email = ? AND role = 'student'",
            (email,)
        ).fetchone()
        conn.close()
        
        if not user or not check_password(password, user["password"]):
            flash("Invalid student email or password.")
            return render_template("student-login.html")
            
        if not user["approved"]:
            flash("Your student account is waiting for admin approval.")
            return render_template("student-login.html")
            
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        session["user_role"] = user["role"]
        
        # Fetch updated score
        score_data = get_db().execute("SELECT resume_score FROM users WHERE id = ?", (user["id"],)).fetchone()
        session["resume_score"] = score_data["resume_score"] if score_data else 0
        
        log_activity(user["id"], "Login", "Student logged in")
        return redirect(url_for("dashboard"))
        
    return render_template("student-login.html")


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    """Portal-specific admin login."""
    if "user_id" in session:
        if session.get("user_role") == "admin":
            return redirect(url_for("admin"))
        return redirect(url_for("dashboard"))
        
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        conn = get_db()
        user = conn.execute(
            "SELECT id, name, email, password, role FROM users WHERE email = ? AND role = 'admin'",
            (email,)
        ).fetchone()
        conn.close()
        
        if not user or not check_password(password, user["password"]):
            flash("Invalid admin credentials.")
            return render_template("admin-login.html")
            
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        session["user_role"] = user["role"]
        
        log_activity(user["id"], "Login", "Admin logged in")
        return redirect(url_for("admin"))
        
    return render_template("admin-login.html")


@app.route("/logout")
def logout():
    """Log out user."""
    session.clear()
    return redirect(url_for("index"))


def render_app_page(template, title, page, nav_subtitle=None):
    return render_template(
        template,
        title=title,
        page=page,
        nav_subtitle=nav_subtitle or title,
    )


@app.route("/dashboard")
@student_required
def dashboard():
    """Student dashboard with stats and announcements."""
    conn = get_db()
    announcements = conn.execute("SELECT * FROM announcements ORDER BY id DESC LIMIT 3").fetchall()
    conn.close()
    return render_template("dashboard.html", 
                         title="Dashboard", 
                         page="dashboard", 
                         nav_subtitle="Your dashboard",
                         announcements=announcements)


def get_ai_response(user_message):
    """
    Highly intelligent AI assistant using the latest Google GenAI SDK.
    Includes retry logic, Hindi detection, and manual fallbacks.
    """
    if not client:
        return "AI Configuration missing. Please set GEMINI_API_KEY in the .env file."

    # 1. Hindi Detection
    is_hindi = any("\u0900" <= char <= "\u097F" for char in user_message)
    
    # 2. Manual Keyword Handling (Fallback/Fast Pass)
    manual_keywords = {
        "python": "Python is a versatile, high-level programming language known for its readability. It's great for web dev, data science, and AI!",
        "java": "Java is a powerful, class-based, object-oriented language. Its 'Write Once, Run Anywhere' principle makes it a global standard.",
        "html": "HTML (HyperText Markup Language) is the backbone of the web, used for structuring content on webpages.",
        "css": "CSS (Cascading Style Sheets) is used for styling and layout of web pages, making them look beautiful!",
        "javascript": "JavaScript is the programming language of the Web. It allows you to create dynamic, interactive content.",
        "sql": "SQL (Structured Query Language) is used for managing and querying data in databases."
    }
    
    # Check if AI is having trouble OR as a quick check for basic terms
    def get_manual_fallback(msg):
        msg_lower = msg.lower()
        for kw, resp in manual_keywords.items():
            if kw in msg_lower:
                return f"I can definitely help with that! {resp}"
        return None

    fallbacks = [
        "Oops! My AI brain is taking a quick nap. Please try asking again in a few seconds!",
        "I'm experiencing a bit of a data jam. Re-send your message and I'll jump right on it!",
        "Even AI needs a coffee break sometimes. I'll be back in a moment—try again!",
        "I'm having a tiny technical hiccup. Could you please repeat that?"
    ]

    # Add Hindi fallbacks if detected
    if is_hindi:
        fallbacks = [
            "क्षमा करें, मेरा मस्तिष्क अभी थोड़ा व्यस्त है। कृपया पुनः प्रयास करें।",
            "कुछ तकनीकी समस्या आ गई है। क्या आप फिर से पूछ सकते हैं?",
            "मैं अभी आपकी बात समझ नहीं पा रहा हूँ। कृपया दोबारा मैसेज भेजें।"
        ]

    # 3. System Prompt Construction
    system_instruction = "You are AI Career Copilot, a friendly and clear student assistant. Provide helpful, simple, and direct answers. Keep formatting clean using markdown. If the user writes in Hindi, respond strictly in Hindi."
    
    full_prompt = f"SYSTEM: {system_instruction}\nUSER: {user_message}"

    max_retries = 2
    retry_delay = 2

    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"DEBUG: Gemini API Error (Attempt {attempt + 1}): {str(e)}")
            
            if attempt < max_retries:
                time.sleep(retry_delay * (2 ** attempt))
            else:
                # 4. Final Fallback: Try Manual Keywords First
                manual = get_manual_fallback(user_message)
                if manual:
                    return manual
                return random.choice(fallbacks)


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
def api_chat():
    try:
        data = request.get_json()
        user_message = data.get("message", "").lower()

        # ----------- MANUAL SMART RESPONSES -----------

        if "python" in user_message:
            return jsonify({
                "reply": "Python is a powerful programming language used in web development, AI, and data science."
            })

        if "java" in user_message:
            return jsonify({
                "reply": "Java is a popular object-oriented programming language used for building enterprise applications."
            })

        if "html" in user_message:
            return jsonify({
                "reply": "HTML is used to create the structure of web pages."
            })

        if "data scientist" in user_message:
            return jsonify({
                "reply": """To become a Data Scientist, you need:
📊 Skills:
- Python
- Data Analysis (Pandas, NumPy)
- Machine Learning
- Statistics
- SQL

🚀 Start with Python and basic data analysis!"""
            })
        if "machine learning" in user_message:
            return jsonify({
                "reply": "Machine Learning is a part of AI where systems learn from data and improve automatically."
            })

        if "software development" in user_message:
            return jsonify({
                "reply": "Software development is the process of designing, building, testing, and maintaining applications."
            })

        if "data science" in user_message:
            return jsonify({
                "reply": "Data Science involves analyzing data to extract useful insights using Python and statistics."
            })

        if "web development" in user_message:
            return jsonify({
                "reply": "Web development involves creating websites using HTML, CSS, JavaScript, and backend frameworks."
            })

        if "sql" in user_message:
            return jsonify({
                "reply": "SQL is used to manage and query databases efficiently."
            })

        if "career" in user_message:
            return jsonify({
                "reply": "Choosing a career depends on your interests and skills. You can explore software, data science, or AI."
            })

        if "interview" in user_message:
            return jsonify({
                "reply": """Here are some tips to crack interviews:

✔ Practice DSA
✔ Build projects
✔ Revise core concepts
✔ Do mock interviews

👉 Stay confident and consistent!"""
            })

        if "ai" in user_message:
            return jsonify({
                "reply": "AI (Artificial Intelligence) is the ability of machines to think and learn like humans."
            })

        # ----------- HINDI SUPPORT -----------

        if any(word in user_message for word in ["kya", "kaise", "hai"]):
            return jsonify({
                "reply": "Main aapki madad kar sakta hoon 😊 Aap kya jaana chahte hain?"
            })

        # ----------- DEFAULT FALLBACK -----------

        fallback_responses = [
            "😅 I'm having a small issue right now. Try again in a moment!",
            "🤖 My brain is loading... please try again!",
            "⚡ Temporary glitch! Ask me again please."
        ]

        return jsonify({
            "reply": random.choice(fallback_responses)
        })

    except Exception as e:
        print("Chat Error:", e)
        return jsonify({
            "reply": "⚠️ Something went wrong. Please try again!"
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
        return render_app_page("resume.html", "Resume Analysis", "resume-analysis")
        
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
        
    # Ensure uploads folder exists and save file
    from werkzeug.utils import secure_filename
    upload_folder = os.path.join(app.root_path, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    text = ""
    
    try:
        if filename.lower().endswith(".pdf"):
            reader = PyPDF2.PdfReader(filepath)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif filename.lower().endswith(".docx"):
            doc = docx.Document(filepath)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            return jsonify({"error": "Unsupported file format. Please upload PDF or DOCX."}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 500

    text = text.lower()
    
    score = 0
    missing_sections = []
    suggestions = []
    
    # Check Resume Length
    word_count = len(text.split())
    if word_count < 150:
        suggestions.append("Expand your resume with more details about your work.")
        
    # Check for Action Verbs
    action_verbs = ["developed", "built", "implemented", "designed", "created", "led", "managed", "analyzed"]
    has_action_verbs = any(verb in text for verb in action_verbs)
    if not has_action_verbs:
        suggestions.append("Use action verbs like developed, built, implemented.")

    # Check for GitHub/Portfolio
    if "github" not in text and "linkedin.com" not in text and "portfolio" not in text:
        suggestions.append("Add a GitHub profile link to showcase your projects.")

    # Skills check (max 25 points)
    if "skill" in text or "technologies" in text or "tools" in text:
        score += 25
    else:
        missing_sections.append("Skills")
        suggestions.append("Add technical skills section.")
        
    # Projects check (max 25 points)
    # Give full points if section exists, but enforce counts via suggestions
    if "project" in text or "portfolio" in text:
        score += 25
        project_count = text.count("project")
        if project_count < 2 and word_count < 250:
            suggestions.append("Include at least 2 practical projects.")
    else:
        project_count = 0
        missing_sections.append("Projects")
        suggestions.append("Include at least 2 practical projects.")
        
    # Education check (max 20 points)
    if "education" in text or "university" in text or "college" in text or "degree" in text or "bachelor" in text:
        score += 20
    else:
        missing_sections.append("Education")
        suggestions.append("Add an Education section detailing your degree.")
        
    # Experience check (max 15 points)
    if "experience" in text or "internship" in text or "work history" in text:
        score += 15
    else:
        missing_sections.append("Experience")
        suggestions.append("Include internships or work experience.")
        
    # Keywords check (max 15 points)
    keywords = ["python", "sql", "machine learning", "html", "css", "javascript", "git"]
    found_keywords = sum(1 for kw in keywords if kw in text)
    
    # Give roughly 2.14 points per keyword, capped at 15
    keyword_points = min(15, int(found_keywords * (15 / len(keywords))))
    score += keyword_points
    
    # If skills < 5 found from the tech keywords, suggest adding more
    if found_keywords < 5:
        suggestions.append("Add more technical skills relevant to your target career.")
        
    # Ensure we always provide at least something if it's very short but no specific hits triggered
    if len(suggestions) < 3 and score < 90:
        suggestions.append("Quantify your achievements with data and metrics.")
        if len(suggestions) < 3:
            suggestions.append("Tailor your keywords to match the specific job description.")
        
    # Update score and project count in database
    conn = get_db()
    conn.execute("UPDATE users SET resume_score = ?, project_count = ? WHERE id = ?", (score, project_count, session["user_id"]))
    conn.commit()
    conn.close()
    
    # Update session
    session["resume_score"] = score
    
    return jsonify({
        "message": "Resume uploaded and analyzed successfully!",
        "score": score,
        "missing_sections": missing_sections,
        "suggestions": suggestions
    })


@app.route("/placement-readiness")
@student_required
def placement_readiness():
    conn = get_db()
    user_data = conn.execute("SELECT resume_score, skill_match, project_count FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    
    if not user_data:
        return jsonify({"error": "User not found"}), 404
        
    resume_score = user_data["resume_score"]
    skill_match = user_data["skill_match"]
    project_count = user_data["project_count"]
    
    # Normalize project metric: Max 20 points (10 points per project, max 2 projects)
    capped_projects = min(project_count, 2)
    
    readiness_score = int((resume_score * 0.4) + (skill_match * 0.4) + (capped_projects * 10))
    
    if readiness_score < 50:
        insight = "Focus on building projects and improving technical skills."
    elif readiness_score <= 70:
        insight = "Improve resume and practice coding interviews."
    else:
        insight = "You are close to placement readiness. Start applying for jobs."
        
    return jsonify({
        "readiness_score": readiness_score,
        "resume_score": resume_score,
        "skill_match": skill_match,
        "capped_projects": capped_projects,
        "insight": insight
    })


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
    # Fetch from placements table as requested
    placements = conn.execute(
        "SELECT id, company_name, role, status, created_at FROM placements WHERE user_id = ? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    
    # Calculate stats for the dashboard cards
    total_count = len(placements)
    interview_count = sum(1 for p in placements if p["status"] == "Interview")
    selected_count = sum(1 for p in placements if p["status"] == "Selected")
    rejected_count = sum(1 for p in placements if p["status"] == "Rejected")
    
    # Calculate progress percentage (Proposed: Selected * 100% + Interview * 50%)
    if total_count > 0:
        # We cap progress at 100%
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
    """Create a new job application record."""
    company_name = request.form.get("company_name", "").strip()
    job_role = request.form.get("job_role", "").strip()
    status = request.form.get("status", "Applied").strip()
    
    if not company_name or not job_role:
        flash("Company Name and Job Role are required.")
        return redirect(url_for("placement_tracker"))
        
    date_applied = datetime.utcnow().strftime("%Y-%m-%d")
    
    conn = get_db()
    conn.execute(
        "INSERT INTO applications (user_id, company_name, job_role, status, date_applied) VALUES (?, ?, ?, ?, ?)",
        (session["user_id"], company_name, job_role, status, date_applied)
    )
    conn.commit()
    conn.close()
    
    flash("Application added successfully.")
    return redirect(url_for("placement_tracker"))


@app.route("/delete-application/<int:app_id>", methods=["POST"])
@student_required
def delete_application(app_id):
    """Delete a job application record."""
    conn = get_db()
    conn.execute(
        "DELETE FROM applications WHERE id = ? AND user_id = ?",
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
    
    # New stats
    total_apps = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    total_resumes = conn.execute("SELECT COUNT(*) FROM users WHERE resume_score > 0").fetchone()[0]
    
    # Activity data (Last 7 days of applications)
    app_activity = conn.execute("""
        SELECT date_applied as date, COUNT(*) as count 
        FROM applications 
        GROUP BY date_applied 
        ORDER BY date_applied DESC 
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
    status = request.form.get("status", "Applied").strip()
    
    # Debug prints as requested
    print("--- Placement Add Triggered ---")
    print(f"Company: {company_name}")
    print(f"Role: {role}")
    print(f"Status: {status}")
    print("Placement Added:", company_name, role, status)
    
    if not company_name or not role:
        flash("Company Name and Role are required.")
        return redirect(url_for("placement_tracker"))
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute(
        "INSERT INTO placements (user_id, company_name, role, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (session["user_id"], company_name, role, status, now)
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
    new_status = request.form.get("status")
    if not new_status:
        flash("Status is required.")
        return redirect(url_for("placement_tracker"))
    
    conn = get_db()
    # Ensure the placement belongs to the user
    placement = conn.execute("SELECT * FROM placements WHERE id = ? AND user_id = ?", (id, session["user_id"])).fetchone()
    
    if placement:
        conn.execute("UPDATE placements SET status = ? WHERE id = ?", (new_status, id))
        conn.commit()
        log_activity(session["user_id"], "Update Placement", f"Updated status for {placement['company_name']} to {new_status}")
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
        conn.execute("DELETE FROM placements WHERE id = ?", (id,))
        conn.commit()
        log_activity(session["user_id"], "Delete Placement", f"Deleted placement entry for {placement['company_name']}")
        flash("Placement record deleted.")
    else:
        flash("Placement record not found.")
        
    conn.close()
    return redirect(url_for("placement_tracker"))

# -------- Run --------


import os

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
