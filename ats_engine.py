import zipfile
import xml.etree.ElementTree as ET
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
"""
ATS Engine - Evidence-Based Resume Analyzer and Job Match Evaluator
Provides deterministic, explainable scoring and actionable recommendations.
Includes:
- Two Distinct Scores:
  1. Job Match Score (0-100): Evaluates resume against target JD (Required skills evidence, preferred skills, role alignment, eligibility, soft skills).
  2. Resume Quality Score (0-100): Evaluates structure, action verbs, measurable metrics, skills evidence ratio, readability, and contact info independently of JD.
- Anti-keyword-stuffing detection.
- Honest Fresher & Student handling (projects substantiate skills without penalizing lack of full-time experience).
- Evidence-based recommendations with issue, excerpt, why it matters, priority, action, and grounded rewrites.
- Clear disclaimers: Never labels scores as employer ATS algorithms or guarantees interview selection.
"""

import os
import re
import math
from typing import Dict, List, Any, Optional, Tuple

# ==============================================================================
# 1. TAXONOMY AND SKILL MAPPINGS (ALIAS NORMALIZATION)
# ==============================================================================

TECH_SKILLS_MAP = {
    # Programming Languages
    "python": "Python", "python3": "Python", "py": "Python",
    "javascript": "JavaScript", "js": "JavaScript", "es6": "JavaScript",
    "typescript": "TypeScript", "ts": "TypeScript",
    "java": "Java", "c++": "C++", "cpp": "C++",
    "c#": "C#", "csharp": "C#", "ruby": "Ruby",
    "go": "Go", "golang": "Go", "rust": "Rust",
    "php": "PHP", "swift": "Swift", "kotlin": "Kotlin",
    "scala": "Scala", "dart": "Dart", "r": "R", "matlab": "MATLAB",
    "sql": "SQL", "html": "HTML", "html5": "HTML",
    "css": "CSS", "css3": "CSS", "sass": "Sass", "scss": "Sass",

    # Web & Frameworks
    "react": "React", "reactjs": "React", "react.js": "React",
    "angular": "Angular", "angularjs": "Angular",
    "vue": "Vue", "vuejs": "Vue", "vue.js": "Vue",
    "nextjs": "Next.js", "next.js": "Next.js",
    "nodejs": "Node.js", "node.js": "Node.js",
    "express": "Express", "expressjs": "Express", "express.js": "Express",
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
    "spring": "Spring", "spring boot": "Spring Boot", "springboot": "Spring Boot",
    "asp.net": "ASP.NET", "dotnet": ".NET", ".net": ".NET",
    "laravel": "Laravel", "rails": "Ruby on Rails", "ruby on rails": "Ruby on Rails",
    "graphql": "GraphQL",
    "rest api": "REST APIs", "rest apis": "REST APIs", "restful api": "REST APIs",
    "restful apis": "REST APIs", "restful": "REST APIs", "rest": "REST APIs",
    "bootstrap": "Bootstrap", "tailwind": "Tailwind CSS", "tailwindcss": "Tailwind CSS",
    "jquery": "jQuery", "redux": "Redux",

    # Databases & Storage
    "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
    "mysql": "MySQL", "sqlite": "SQLite", "sqlite3": "SQLite",
    "mongodb": "MongoDB", "redis": "Redis", "cassandra": "Cassandra",
    "dynamodb": "DynamoDB", "oracle": "Oracle DB", "oracle db": "Oracle DB",
    "sql server": "SQL Server", "mssql": "SQL Server", "mariadb": "MariaDB",
    "elasticsearch": "Elasticsearch", "neo4j": "Neo4j",
    "firebase": "Firebase", "supabase": "Supabase",

    # Cloud, DevOps & Infrastructure
    "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "aws": "AWS", "amazon web services": "AWS",
    "azure": "Azure", "microsoft azure": "Azure",
    "gcp": "GCP", "google cloud": "GCP", "google cloud platform": "GCP",
    "git": "Git", "github": "GitHub", "gitlab": "GitLab",
    "ci/cd": "CI/CD", "cicd": "CI/CD", "jenkins": "Jenkins",
    "terraform": "Terraform", "ansible": "Ansible",
    "linux": "Linux", "unix": "Unix", "bash": "Bash", "shell": "Shell Scripting",
    "jira": "Jira", "postman": "Postman", "nginx": "Nginx",
    "kafka": "Kafka", "rabbitmq": "RabbitMQ",

    # Data Science, AI & Machine Learning
    "machine learning": "Machine Learning", "ml": "Machine Learning",
    "deep learning": "Deep Learning", "dl": "Deep Learning",
    "artificial intelligence": "AI", "ai": "AI",
    "natural language processing": "NLP", "nlp": "NLP",
    "computer vision": "Computer Vision", "cv": "Computer Vision",
    "data science": "Data Science", "pandas": "Pandas", "numpy": "NumPy",
    "scipy": "SciPy", "scikit-learn": "Scikit-Learn", "sklearn": "Scikit-Learn",
    "tensorflow": "TensorFlow", "tf": "TensorFlow",
    "pytorch": "PyTorch", "keras": "Keras",
    "tableau": "Tableau", "power bi": "Power BI", "powerbi": "Power BI",
    "spark": "Apache Spark", "apache spark": "Apache Spark",
    "hadoop": "Hadoop", "llm": "LLMs", "llms": "LLMs",
    "generative ai": "Generative AI", "genai": "Generative AI",

    # Methodologies, Architecture & Core CS
    "data structures": "Data Structures", "algorithms": "Algorithms",
    "oop": "OOP", "object oriented programming": "OOP",
    "mvc": "MVC", "microservices": "Microservices",
    "system design": "System Design", "agile": "Agile", "scrum": "Scrum",
    "unit testing": "Unit Testing", "tdd": "TDD",
    "cybersecurity": "Cybersecurity", "cryptography": "Cryptography",
    "web development": "Web Development", "full stack": "Full Stack Development",
    
}

ACTION_VERBS = [
    "accelerated", "achieved", "administered", "analyzed", "architected", "automated",
    "built", "collaborated", "configured", "constructed", "created", "debugged",
    "delivered", "deployed", "designed", "developed", "devised", "engineered",
    "enhanced", "established", "executed", "expanded", "formulated", "implemented",
    "improved", "increased", "initiated", "integrated", "launched", "lead",
    "managed", "mentored", "migrated", "modernized", "negotiated", "optimized",
    "orchestrated", "organized", "overhauled", "performed", "pioneered", "produced",
    "reduced", "refactored", "resolved", "restructured", "scaled", "simplified",
    "solved", "spearheaded", "standardized", "streamlined", "structured", "tested",
    "transformed", "upgraded"
]

COMMON_ATS_SECTIONS = [
    {"name": "Contact Information", "key": "contact", "critical": True},
    {"name": "Summary / Objective", "key": "summary", "critical": False},
    {"name": "Education", "key": "education", "critical": True},
    {"name": "Technical Skills", "key": "skills", "critical": True},
    {"name": "Experience / Work History", "key": "experience", "critical": False},
    {"name": "Projects", "key": "projects", "critical": True},
    {"name": "Certifications", "key": "certifications", "critical": False}
]

# ==============================================================================
# 2. FILE EXTRACTION UTILITIES
# ==============================================================================

def extract_text_from_file(filepath: str, original_filename: str = "") -> Tuple[Optional[str], Optional[str]]:
    """
    Safely extract readable text from PDF or DOCX resume file.
    Returns (extracted_text, error_message).
    If extraction fails or text is unreadable/image-only, returns (None, clean_error_message).
    """
    if not filepath or not os.path.exists(filepath):
        return None, "File not found on server."

    fname = (original_filename or filepath).lower()

    # 1. PDF EXTRACTION
    if fname.endswith(".pdf"):
        if PyPDF2 is None:
            return None, "PDF processing library is currently unavailable on the server."
        try:
            reader = PyPDF2.PdfReader(filepath)
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    return None, "The uploaded PDF is password-protected. Please upload an unlocked PDF document."

            extracted_pages = []
            for i, page in enumerate(reader.pages):
                try:
                    txt = page.extract_text()
                    if txt and txt.strip():
                        extracted_pages.append(txt.strip())
                except Exception:
                    continue

            full_text = "\n\n".join(extracted_pages).strip()
            if not full_text or len(full_text.split()) < 15:
                return None, (
                    "The uploaded PDF contains no readable text layer (it may be a scanned image or photo). "
                    "OCR (Optical Character Recognition) is not configured in this environment. "
                    "Please upload a PDF generated directly from text (e.g. Word, Google Docs, LaTeX) or a .docx document."
                )
            return full_text, None
        except Exception:
            return None, "Unable to read the uploaded PDF document. The file may be corrupted, truncated, or invalid."

    # 2. DOCX EXTRACTION
    elif fname.endswith(".docx"):
        # Primary: Pure standard-library ZIP + XML extraction (safe on all Python versions)
        try:
            with zipfile.ZipFile(filepath, "r") as z:
                if "word/document.xml" not in z.namelist():
                    return None, "The uploaded DOCX archive does not contain a valid Word document body."
                xml_data = z.read("word/document.xml")
                root = ET.fromstring(xml_data)
                
                paragraphs = []
                w_namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
                for p in root.iter(f"{w_namespace}p"):
                    texts = [node.text for node in p.iter(f"{w_namespace}t") if node.text]
                    if texts:
                        paragraphs.append("".join(texts).strip())
                
                full_text = "\n".join(paragraphs).strip()
                if not full_text or len(full_text.split()) < 15:
                    return None, "The uploaded Word (.docx) document is empty or contains insufficient readable text."
                return full_text, None
        except zipfile.BadZipFile:
            return None, "The uploaded Word file is corrupted or not a valid .docx format."
        except Exception:
            # Fallback to python-docx if available
            if docx is not None:
                try:
                    doc = docx.Document(filepath)
                    paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                    for table in doc.tables:
                        for row in table.rows:
                            for cell in row.cells:
                                if cell.text.strip():
                                    paras.append(cell.text.strip())
                    text = "\n".join(paras).strip()
                    if text and len(text.split()) >= 15:
                        return text, None
                except Exception:
                    pass
            return None, "Unable to read the uploaded Word (.docx) document. Please ensure the file is not corrupted."

    else:
        return None, "Unsupported file format. Please upload a PDF (.pdf) or Word document (.docx)."

def extract_contact_info(raw_text: str) -> Dict[str, Any]:
    """Audit contact information presence and formatting."""
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    phone_pattern = r'(?:(?:\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}|\+?\d{10,13})'
    linkedin_pattern = r'linkedin\.com/in/[a-zA-Z0-9_-]+'
    github_pattern = r'github\.com/[a-zA-Z0-9_-]+'
    portfolio_pattern = r'https?://(?:www\.)?[a-zA-Z0-9-]+\.(?:dev|io|me|app|com|org)(?:/[^\s]*)?'

    email_match = re.search(email_pattern, raw_text)
    phone_match = re.search(phone_pattern, raw_text)
    linkedin_match = re.search(linkedin_pattern, raw_text, re.IGNORECASE)
    github_match = re.search(github_pattern, raw_text, re.IGNORECASE)
    portfolio_match = re.search(portfolio_pattern, raw_text, re.IGNORECASE)

    # Candidate Name heuristic
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    candidate_name = None
    if lines:
        for line in lines[:4]:
            if "@" in line or "http" in line or "resume" in line.lower() or "curriculum" in line.lower():
                continue
            cleaned = re.sub(r'[^a-zA-Z\s\.]', '', line).strip()
            words = cleaned.split()
            if 1 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                candidate_name = cleaned
                break
        if not candidate_name and lines:
            candidate_name = lines[0][:40]

    return {
        "name": {
            "present": bool(candidate_name),
            "value": candidate_name or "Not detected",
            "status": "Present" if candidate_name else "Missing"
        },
        "email": {
            "present": bool(email_match),
            "value": email_match.group(0) if email_match else None,
            "status": "Present" if email_match else "Missing"
        },
        "phone": {
            "present": bool(phone_match),
            "value": phone_match.group(0) if phone_match else None,
            "status": "Present" if phone_match else "Missing"
        },
        "linkedin": {
            "present": bool(linkedin_match),
            "value": linkedin_match.group(0) if linkedin_match else None,
            "status": "Present" if linkedin_match else "Missing"
        },
        "github": {
            "present": bool(github_match),
            "value": github_match.group(0) if github_match else None,
            "status": "Present" if github_match else "Missing"
        },
        "portfolio": {
            "present": bool(portfolio_match),
            "value": portfolio_match.group(0) if portfolio_match else None,
            "status": "Present" if portfolio_match else "Missing"
        }
    }

def partition_resume_sections(raw_text: str) -> Dict[str, str]:
    """Splits raw resume text into distinct named section blocks."""
    lines = raw_text.splitlines()
    sections: Dict[str, List[str]] = {"header": []}
    current_section = "header"

    heading_patterns = {
        "education": ["education", "academic background", "academics", "qualifications", "academic credentials"],
        "skills": ["skills", "technical skills", "core competencies", "technologies", "tech stack", "skills & abilities", "key skills"],
        "projects": ["projects", "academic projects", "personal projects", "key projects", "project experience", "technical projects"],
        "experience": ["experience", "work experience", "professional experience", "employment history", "work history"],
        "internships": ["internship", "internships", "internship experience", "industrial training"],
        "summary": ["summary", "professional summary", "career objective", "objective", "profile", "about me"],
        "certifications": ["certifications", "certificates", "licenses & certifications"],
        "achievements": ["achievements", "honors & awards", "accomplishments", "extracurricular", "extracurricular activities"]
    }

    for line in lines:
        cleaned = re.sub(r"^[\d\.\-\*\•\–\>\:\s]+", "", line).strip().lower()
        cleaned = re.sub(r"[\:\-\|]+$", "", cleaned).strip()
        matched = None
        if cleaned and len(cleaned.split()) <= 5:
            for sec_name, pats in heading_patterns.items():
                if cleaned in pats or any(cleaned == p or cleaned.startswith(p + " ") or cleaned.endswith(" " + p) for p in pats):
                    matched = sec_name
                    break
        if matched:
            current_section = matched
            if current_section not in sections:
                sections[current_section] = []
        else:
            sections[current_section].append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items()}

def detect_sections(raw_text: str) -> List[Dict[str, Any]]:
    """Identifies standard ATS resume sections."""
    text_lower = raw_text.lower()
    sections_result = []

    section_aliases = {
        "contact": [r'\b(contact|email|phone|address|linkedin|github)\b'],
        "summary": [r'\b(summary|profile|about me|objective|professional summary|career objective)\b'],
        "education": [r'\b(education|academic|qualification|degree|university|college|school)\b'],
        "skills": [r'\b(skills|technical skills|technologies|core competencies|competencies|tech stack)\b'],
        "experience": [r'\b(experience|work experience|employment|employment history|work history|professional experience)\b'],
        "projects": [r'\b(projects|key projects|academic projects|personal projects)\b'],
        "certifications": [r'\b(certifications|certificates|licenses|courses|accreditations)\b']
    }

    for sec in COMMON_ATS_SECTIONS:
        key = sec["key"]
        patterns = section_aliases.get(key, [])
        is_present = False
        for pattern in patterns:
            if re.search(pattern, text_lower):
                is_present = True
                break

        sections_result.append({
            "name": sec["name"],
            "key": key,
            "present": is_present,
            "critical": sec["critical"]
        })

    return sections_result

# ==============================================================================
# 4. SKILLS EXTRACTION AND EVIDENCE SUBSTANTIATION
# ==============================================================================

def extract_skills_from_text(text: str) -> List[str]:
    """Extract recognized technical skills with alias normalization."""
    found_skills = set()
    text_lower = text.lower()

    for alias, canonical in TECH_SKILLS_MAP.items():
        if alias in ["c++", "c#", ".net", "ci/cd"]:
            pattern = rf"(?:^|[\s,;/()\[\]]){re.escape(alias)}(?:$|[\s,;/()\[\]])"
        elif alias in ["r", "c", "go", "py", "js", "ts"]:
            pattern = rf"(?:^|[\s,;/()\[\]]){re.escape(alias)}(?:$|[\s,;/()\[\]])"
        else:
            pattern = rf"\b{re.escape(alias)}\b"

        if re.search(pattern, text_lower):
            found_skills.add(canonical)

    return sorted(list(found_skills))

def extract_skills_with_evidence(raw_text: str, sections_dict: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Extract skills and verify whether they are substantiated with implementation
    details in Projects, Experience, or Internships sections.
    Also flags keyword stuffing and duplicate alias abuse.
    """
    if sections_dict is None:
        sections_dict = partition_resume_sections(raw_text)

    all_skills = extract_skills_from_text(raw_text)

    substantiating_text = "\n".join([
        sections_dict.get("projects", ""),
        sections_dict.get("experience", ""),
        sections_dict.get("internships", "")
    ]).lower()

    substantiated = []
    list_only = []
    evidence_snippets = {}

    for skill in all_skills:
        aliases = [k for k, v in TECH_SKILLS_MAP.items() if v == skill]
        matched_snippet = None
        for a in aliases:
            if a in ["c++", "c#", ".net", "ci/cd", "r", "c", "go", "py", "js", "ts"]:
                p = rf"(?:^|[\s,;/()\[\]]){re.escape(a)}(?:$|[\s,;/()\[\]])"
            else:
                p = rf"\b{re.escape(a)}\b"

            for line in substantiating_text.splitlines():
                if re.search(p, line):
                    cleaned = line.strip(" -*•–\t")
                    if len(cleaned.split()) >= 4:
                        matched_snippet = cleaned[:120]
                        break
            if matched_snippet:
                break

        if matched_snippet:
            substantiated.append(skill)
            evidence_snippets[skill] = matched_snippet
        else:
            list_only.append(skill)

    # Anti-keyword-stuffing check
    stuffing_warnings = []
    total_words = max(1, len(raw_text.split()))
    text_lower = raw_text.lower()
    for skill in all_skills:
        aliases = [k for k, v in TECH_SKILLS_MAP.items() if v == skill]
        total_occurrences = 0
        for a in aliases:
            total_occurrences += len(re.findall(rf"\b{re.escape(a)}\b", text_lower))
        if total_occurrences >= 7 and (total_occurrences / total_words > 0.03):
            stuffing_warnings.append(
                f"Keyword '{skill}' is repeated {total_occurrences} times without sufficient unique context."
            )

    substantiation_ratio = (len(substantiated) / max(len(all_skills), 1)) if all_skills else 0.0

    return {
        "all_skills": all_skills,
        "substantiated_skills": sorted(substantiated),
        "list_only_skills": sorted(list_only),
        "evidence_snippets": evidence_snippets,
        "stuffing_warnings": stuffing_warnings,
        "substantiation_ratio": round(substantiation_ratio, 2)
    }

# ==============================================================================
# 5. JOB DESCRIPTION REQUIREMENTS EXTRACTION & MATCHING
# ==============================================================================

def extract_jd_requirements(jd_text: str) -> Dict[str, Any]:
    """Parse Job Description into structured requirements."""
    if not jd_text or not jd_text.strip():
        return {
            "has_jd": False,
            "has_meaningful_jd": False,
            "message": "No job description provided."
        }

    lines = [l.strip() for l in jd_text.splitlines() if l.strip()]
    jd_lower = jd_text.lower()
    all_jd_skills = extract_skills_from_text(jd_text)

    # Check for meaningfulness: must have at least 1 recognizable technical skill or domain keyword
    if not all_jd_skills and len(jd_text.split()) < 12:
        return {
            "has_jd": True,
            "has_meaningful_jd": False,
            "message": "Job description is too short to extract requirements."
        }

    # Role Title heuristic
    role_title = ""
    for line in lines[:4]:
        m = re.search(r"(?:job title|role|position|title)\s*[:\-]\s*(.+)", line, re.IGNORECASE)
        if m:
            role_title = m.group(1).strip()
            break
    if not role_title and lines:
        first_line = lines[0].strip()
        if len(first_line.split()) <= 6 and not any(k in first_line.lower() for k in ["about", "company", "description", "overview", "hiring", "we are"]):
            role_title = first_line

    # Partition required vs preferred
    required_lines = []
    preferred_lines = []
    current_bucket = "required"

    for line in lines:
        l_lower = line.lower()
        if any(k in l_lower for k in ["preferred", "nice to have", "plus", "bonus", "good to have", "desired", "advantage"]):
            current_bucket = "preferred"
        elif any(k in l_lower for k in ["require", "must have", "essential", "qualifications", "responsibilities", "what you need", "skills"]):
            current_bucket = "required"

        if current_bucket == "preferred":
            preferred_lines.append(line)
        else:
            required_lines.append(line)

    req_str = " ".join(required_lines) if required_lines else jd_text
    pref_str = " ".join(preferred_lines)

    pref_skills = set(extract_skills_from_text(pref_str)) if pref_str else set()
    req_skills = set(all_jd_skills) - pref_skills if pref_skills else set(all_jd_skills)

    soft_skills_catalog = [
        "Communication", "Teamwork", "Problem Solving", "Leadership", "Collaboration",
        "Time Management", "Critical Thinking", "Adaptability", "Agile", "Scrum"
    ]
    detected_soft_skills = [s for s in soft_skills_catalog if re.search(rf"\b{re.escape(s.lower())}\b", jd_lower)]

    return {
        "has_jd": True,
        "has_meaningful_jd": bool(all_jd_skills or detected_soft_skills),
        "role_title": role_title or "Target Role",
        "required_skills": sorted(list(req_skills)),
        "preferred_skills": sorted(list(pref_skills)),
        "soft_skills": sorted(detected_soft_skills),
        "total_skills_count": len(all_jd_skills)
    }

def compare_job_description(
    resume_text: str,
    resume_skills: List[str],
    jd_text: str,
    sections_dict: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Transparently matches resume against Job Description using weighted requirements.
    - Required technical skills (45 pts): 1.0 weight for evidenced, 0.5 for list-only
    - Preferred technical skills (20 pts): 1.0 weight for evidenced, 0.6 for list-only
    - Role & Domain Alignment (15 pts)
    - Education & Eligibility (10 pts)
    - Soft skills / Context (10 pts)
    - Irrelevance clamping: Completely irrelevant resumes capped at <= 12 pts.
    """
    if not jd_text or not jd_text.strip():
        return {
            "has_jd": False,
            "has_meaningful_jd": False,
            "keywords_found": False,
            "match_rate": 0,
            "job_match_score": None,
            "job_match_rating": "Unavailable",
            "matched_keywords": [],
            "missing_keywords": [],
            "total_jd_keywords": 0,
            "note": "No Job Description provided: Job Match Score requires target role requirements. Resume Quality Score evaluated independently."
        }

    if sections_dict is None:
        sections_dict = partition_resume_sections(resume_text)

    jd_parsed = extract_jd_requirements(jd_text)
    all_jd_skills = set(extract_skills_from_text(jd_text))

    if not all_jd_skills:
        return {
            "has_jd": True,
            "has_meaningful_jd": False,
            "keywords_found": False,
            "match_rate": 0,
            "job_match_score": 0,
            "job_match_rating": "No Tech Keywords Found",
            "matched_keywords": [],
            "missing_keywords": [],
            "total_jd_keywords": 0,
            "note": "No recognizable technical keywords found in the provided job description. Please provide a detailed job description including required skills and role responsibilities."
        }

    required_skills = jd_parsed["required_skills"]
    preferred_skills = jd_parsed["preferred_skills"]
    target_role = jd_parsed["role_title"]

    skills_data = extract_skills_with_evidence(resume_text, sections_dict)
    substantiated = set(skills_data["substantiated_skills"])
    all_res_skills = set(skills_data["all_skills"])

    # 1. Match Required Skills (Full weight = 45 pts)
    matched_req_evidence = []
    matched_req_list_only = []
    missing_required = []

    for req in required_skills:
        if req in substantiated:
            matched_req_evidence.append(req)
        elif req in all_res_skills:
            matched_req_list_only.append(req)
        else:
            missing_required.append(req)

    req_count = len(required_skills)
    if req_count > 0:
        req_points = (
            (len(matched_req_evidence) * 1.0 + len(matched_req_list_only) * 0.5) / req_count
        ) * 45.0
    else:
        req_points = 45.0

    # 2. Match Preferred Skills (Weight = 20 pts)
    matched_pref_evidence = []
    matched_pref_list_only = []
    missing_preferred = []

    pref_count = len(preferred_skills)
    if pref_count > 0:
        for pref in preferred_skills:
            if pref in substantiated:
                matched_pref_evidence.append(pref)
            elif pref in all_res_skills:
                matched_pref_list_only.append(pref)
            else:
                missing_preferred.append(pref)
        pref_points = (
            (len(matched_pref_evidence) * 1.0 + len(matched_pref_list_only) * 0.6) / pref_count
        ) * 20.0
    else:
        pref_points = 20.0 * (req_points / 45.0) if req_count > 0 else 20.0

    # 3. Role & Domain Alignment (Weight = 15 pts)
    resume_lower = resume_text.lower()
    role_lower = target_role.lower()

    non_tech_keywords = ["chef", "culinary", "cook", "restaurant", "hospitality", "baker", "dentist", "nurse", "carpenter", "plumber"]
    is_non_tech_resume = any(k in resume_lower for k in non_tech_keywords) and len(all_res_skills) == 0

    if is_non_tech_resume:
        role_score = 0.0
    else:
        role_matches = sum(1 for word in role_lower.split() if len(word) > 3 and word in resume_lower)
        role_score = min(15.0, (role_matches / max(len(role_lower.split()), 1)) * 15.0) if role_lower else 10.0

    # 4. Education & Eligibility (Weight = 10 pts)
    edu_text = sections_dict.get("education", "").lower()
    if any(deg in edu_text for deg in ["b.tech", "btech", "b.e", "bachelor", "degree", "bs", "m.tech", "master", "ms", "cs", "computer science"]):
        edu_score = 10.0
    elif sections_dict.get("education"):
        edu_score = 6.0
    else:
        edu_score = 2.0

    # 5. Context & Soft Skills (Weight = 10 pts)
    soft_detected = [s for s in jd_parsed["soft_skills"] if re.search(rf"\b{re.escape(s.lower())}\b", resume_lower)]
    soft_score = (len(soft_detected) / max(len(jd_parsed["soft_skills"]), 1)) * 10.0 if jd_parsed["soft_skills"] else 8.0

    # Total Raw Match Score
    total_match = req_points + pref_points + role_score + edu_score + soft_score

    # Anti-stuffing penalty
    if skills_data["stuffing_warnings"]:
        total_match = max(5.0, total_match - 15.0)

    # Clamping for completely irrelevant resumes:
    # If 0 required skills matched AND role alignment is 0 -> Cap at <= 12%
    if len(matched_req_evidence) == 0 and len(matched_req_list_only) == 0:
        total_match = min(total_match, 12.0)
    elif len(matched_req_evidence) == 0 and len(matched_req_list_only) <= 1 and role_score < 5:
        total_match = min(total_match, 25.0)

    final_match_score = round(max(0, min(100, total_match)))

    # Keyword lists and match_rate for ATS coverage
    matched_all = sorted(list((all_res_skills | substantiated) & all_jd_skills))
    missing_all = sorted(list(all_jd_skills - (all_res_skills | substantiated)))

    keyword_coverage_rate = round((len(matched_all) / max(len(all_jd_skills), 1)) * 100)

    if final_match_score >= 80:
        match_rating = "Strong Match"
        match_badge = "pill-good"
    elif final_match_score >= 60:
        match_rating = "Moderate Match"
        match_badge = "pill-warn"
    elif final_match_score >= 35:
        match_rating = "Weak Match"
        match_badge = "pill-bad"
    else:
        match_rating = "Low / Highly Irrelevant"
        match_badge = "pill-bad"

    return {
        "has_jd": True,
        "has_meaningful_jd": True,
        "keywords_found": True,
        "job_match_score": final_match_score,
        "match_rate": keyword_coverage_rate,
        "job_match_rating": match_rating,
        "job_match_badge": match_badge,
        "target_role": target_role,
        "matched_keywords": matched_all,
        "missing_keywords": missing_all,
        "total_jd_keywords": len(matched_all) + len(missing_all),
        "required_skills": {
            "total": req_count,
            "matched_with_evidence": matched_req_evidence,
            "matched_list_only": matched_req_list_only,
            "missing": missing_required
        },
        "preferred_skills": {
            "total": pref_count,
            "matched_with_evidence": matched_pref_evidence,
            "matched_list_only": matched_pref_list_only,
            "missing": missing_preferred
        },
        "role_alignment_score": round(role_score),
        "stuffing_warnings": skills_data["stuffing_warnings"],
        "note": f"Job Match Score: {final_match_score}/100 based on required skills evidence, role alignment, and qualification fit."
    }

def generate_job_match_suggestions(
    matched_skills: List[str],
    missing_skills: List[str],
    match_rate: int,
    total_jd_keywords: int
) -> List[str]:
    """Generate human-readable matching feedback."""
    suggestions = []
    if missing_skills:
        top_missing = missing_skills[:5]
        suggestions.append(f"Missing Key Technical Skills: Consider incorporating experience or projects utilizing {', '.join(top_missing)} if you have practical knowledge in these areas.")
    if match_rate < 50:
        suggestions.append("Your resume currently has low keyword alignment with this job description. Tailor your project descriptions to emphasize the tech stack mentioned in the job posting.")
    elif match_rate >= 80:
        suggestions.append("Strong keyword alignment with this role. Ensure that these matched keywords are substantiated with quantified achievements in your experience or projects.")
    return suggestions

def analyze_job_match(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """Helper wrapper for job matching."""
    skills = extract_skills_from_text(resume_text)
    return compare_job_description(resume_text, skills, jd_text)

# ==============================================================================
# 6. READABILITY, FORMATTING & QUALITY AUDIT
# ==============================================================================

def analyze_formatting_and_readability(raw_text: str) -> Dict[str, Any]:
    """Audit resume formatting, word count, action verbs, and measurable metrics."""
    words = raw_text.split()
    word_count = len(words)
    lines = raw_text.splitlines()

    text_lower = raw_text.lower()
    detected_verbs = set()
    for verb in ACTION_VERBS:
        if re.search(rf'\b{re.escape(verb)}\b', text_lower):
            detected_verbs.add(verb.capitalize())

    metric_patterns = [
        r'\b\d+(?:\.\d+)?%',
        r'\$\s*\d+(?:,\d+)*(?:\.\d+)?\s*(?:[kKmMbB]|million|thousand)?',
        r'\b\d+\+\s*(?:users|clients|requests|customers|qps|endpoints|ms|seconds|minutes|hours|days|percent)',
        r'\b(?:reduced|increased|improved|scaled|optimized|cut|accelerated)\b[^\.\n]{0,40}\b\d+(?:\.\d+)?%?',
        r'\b(?:latency|throughput|performance|speed)\b[^\.\n]{0,30}\b(?:by\s+)?\d+(?:\.\d+)?%?'
    ]
    detected_metrics = []
    for pattern in metric_patterns:
        for m in re.finditer(pattern, raw_text, re.IGNORECASE):
            detected_metrics.append(m.group(0).strip())

    bullet_count = sum(1 for line in lines if re.match(r'^\s*[-*•–>]\s+', line))

    if 350 <= word_count <= 800:
        length_status = "Optimal"
        length_note = f"Word count ({word_count}) is in the ideal 1-page ATS range (350–800 words)."
    elif word_count < 350:
        length_status = "Too Short"
        length_note = f"Word count ({word_count}) is sparse. Expand on your project implementations and outcomes."
    else:
        length_status = "Lengthy"
        length_note = f"Word count ({word_count}) is high. Aim for conciseness and remove redundant descriptions."

    return {
        "word_count": word_count,
        "length_status": length_status,
        "length_note": length_note,
        "action_verbs": sorted(list(detected_verbs)),
        "action_verb_count": len(detected_verbs),
        "metrics_found": detected_metrics[:10],
        "metrics_count": len(detected_metrics),
        "bullet_count": bullet_count,
        "has_quantifiable_results": len(detected_metrics) >= 2
    }

def compute_resume_quality_score(
    contact_info: Dict[str, Any],
    sections: List[Dict[str, Any]],
    skills: List[str],
    formatting: Dict[str, Any],
    sections_dict: Dict[str, str],
    raw_text: str
) -> Tuple[int, Dict[str, Any]]:
    """
    Computes deterministic, evidence-based Resume Quality Score (0-100) independent of any Job Description.
    Categories:
    - Section Completeness & Standard Structure: 25 pts
    - Action-Oriented Impact & Measurable Metrics: 25 pts
    - Skills Evidence & Substantiation Ratio: 20 pts
    - ATS Readability & Formatting: 15 pts
    - Contact Information & Professional Links: 15 pts
    """
    # 1. Contact Information (15 pts)
    contact_score = 0
    if contact_info.get("name", {}).get("present"): contact_score += 4
    if contact_info.get("email", {}).get("present"): contact_score += 4
    if contact_info.get("phone", {}).get("present"): contact_score += 3
    if (contact_info.get("linkedin", {}).get("present") or
        contact_info.get("github", {}).get("present") or
        contact_info.get("portfolio", {}).get("present")):
        contact_score += 4
    contact_score = min(15, contact_score)

    # 2. Section Completeness (25 pts)
    sec_map = {s["name"]: s["present"] for s in sections}
    sec_score = 0
    if sec_map.get("Education"): sec_score += 6
    if sec_map.get("Technical Skills"): sec_score += 6

    # Fresher consideration: strong projects fulfill experience requirement without penalty
    has_exp = sec_map.get("Experience / Work History")
    has_proj = sec_map.get("Projects")
    if has_exp and has_proj:
        sec_score += 8
    elif has_proj or has_exp:
        sec_score += 8
    else:
        sec_score += 0

    if sec_map.get("Summary / Objective"): sec_score += 3
    if sec_map.get("Certifications"): sec_score += 2
    sec_score = min(25, sec_score)

    # 3. Action-Oriented Impact & Measurable Metrics (25 pts)
    verb_count = formatting.get("action_verb_count", 0)
    verb_score = min(12, verb_count * 2)

    metric_count = formatting.get("metrics_count", 0)
    if metric_count >= 3:
        metric_score = 13
    elif metric_count == 2:
        metric_score = 9
    elif metric_count == 1:
        metric_score = 5
    else:
        metric_score = 0
    impact_score = verb_score + metric_score

    # 4. Skills Evidence & Substantiation Ratio (20 pts)
    skills_data = extract_skills_with_evidence(raw_text, sections_dict)
    subst_ratio = skills_data.get("substantiation_ratio", 0.0)
    total_skills = len(skills)

    if total_skills == 0:
        skills_score = 0
    elif total_skills >= 4:
        if subst_ratio >= 0.70:
            skills_score = 20
        elif subst_ratio >= 0.50:
            skills_score = 16
        elif subst_ratio >= 0.30:
            skills_score = 12
        else:
            skills_score = 8
    else:
        skills_score = min(8, total_skills * 2)

    # 5. Readability & Formatting (15 pts)
    format_score = 0
    word_count = formatting.get("word_count", 0)
    if 300 <= word_count <= 850:
        format_score += 7
    elif 150 <= word_count < 300 or 850 < word_count <= 1200:
        format_score += 4
    else:
        format_score += 1

    bullets = formatting.get("bullet_count", 0)
    if bullets >= 4:
        format_score += 5
    elif bullets >= 1:
        format_score += 3

    lines = [l for l in raw_text.splitlines() if l.strip()]
    long_blocks = sum(1 for l in lines if len(l.split()) > 45)
    if long_blocks == 0:
        format_score += 3
    else:
        format_score += 1
    format_score = min(15, format_score)

    total_quality = contact_score + sec_score + impact_score + skills_score + format_score
    final_quality_score = max(0, min(100, round(total_quality)))

    quality_breakdown = {
        "contact": {"name": "Contact & Links", "score": contact_score, "max": 15},
        "sections": {"name": "Section Completeness", "score": sec_score, "max": 25},
        "impact_metrics": {"name": "Action Verbs & Measurable Metrics", "score": impact_score, "max": 25},
        "skills_evidence": {"name": "Skills Evidence Ratio", "score": skills_score, "max": 20, "substantiation_ratio": subst_ratio},
        "formatting": {"name": "ATS Readability & Layout", "score": format_score, "max": 15}
    }

    return final_quality_score, quality_breakdown

def compute_ats_score(
    contact_info: Dict[str, Any],
    sections: List[Dict[str, Any]],
    skills: List[str],
    formatting: Dict[str, Any],
    jd_analysis: Dict[str, Any],
    quality_score: Optional[int] = None
) -> Tuple[int, Dict[str, Any]]:
    """
    Maintains backward compatibility for legacy scoring calls.
    If job description is present and meaningful, returns job match score;
    otherwise reflects quality score.
    """
    has_meaningful_jd = jd_analysis.get("has_meaningful_jd", False) and jd_analysis.get("job_match_score") is not None

    if has_meaningful_jd:
        score = jd_analysis["job_match_score"]
    else:
        score = quality_score if quality_score is not None else 65

    category_scores = {
        "contact": {
            "name": "Contact Information",
            "score": sum([3 for k, v in contact_info.items() if v.get("present")]),
            "max": 15
        },
        "sections": {
            "name": "Section Completeness",
            "score": min(25, sum([4 for s in sections if s.get("present")])),
            "max": 25
        },
        "skills": {
            "name": "Skills Breadth & Alignment",
            "score": min(20, max(4, len(skills) * 2)),
            "max": 20
        },
        "formatting": {
            "name": "Formatting & Readability",
            "score": 15 if formatting.get("length_status") == "Optimal" else 10,
            "max": 20
        },
        "job_match": {
            "name": "Job Description Alignment",
            "score": round((jd_analysis.get("match_rate", 0) / 100.0) * 20),
            "max": 20
        }
    }

    return score, category_scores

# ==============================================================================
# 7. EVIDENCE-BASED RECOMMENDATIONS GENERATOR
# ==============================================================================

def generate_evidence_recommendations(
    contact_info: Dict[str, Any],
    sections: List[Dict[str, Any]],
    skills_data: Dict[str, Any],
    formatting: Dict[str, Any],
    jd_analysis: Dict[str, Any],
    sections_dict: Dict[str, str],
    quality_score: int
) -> List[Dict[str, Any]]:
    """Generates structured, evidence-based recommendations."""
    recs = []

    if not contact_info["email"]["present"]:
        recs.append({
            "issue": "Missing Email Address",
            "evidence": "No valid email address found in the resume header.",
            "requirement": "Standard candidate identification",
            "why_it_matters": "Recruiters and automated ATS parsers cannot route interview invitations without a valid email address.",
            "priority": "High",
            "action": "Add a professional email address (e.g., yourname@domain.com) at the top of your resume.",
            "suggested_rewrite": "Header: [Your Name] | your.email@example.com | [Phone Number] | [City, Country]"
        })

    if not contact_info["phone"]["present"]:
        recs.append({
            "issue": "Missing Phone Number",
            "evidence": "No phone number was detected in the document text.",
            "requirement": "Standard contact details",
            "why_it_matters": "Recruiting coordinators require a direct contact phone number for initial phone screens.",
            "priority": "High",
            "action": "Add an active telephone number with appropriate country/area code.",
            "suggested_rewrite": "Header: [Your Name] | [Email] | +1 (555) 000-0000 | [Location]"
        })

    if not (contact_info["linkedin"]["present"] or contact_info["github"]["present"]):
        recs.append({
            "issue": "Missing Professional Links (LinkedIn / GitHub)",
            "evidence": "Neither a LinkedIn profile URL nor a GitHub repository profile was found.",
            "requirement": "Professional validation",
            "why_it_matters": "Technical hiring managers inspect GitHub code contributions and LinkedIn recommendations to verify project experience.",
            "priority": "Medium",
            "action": "Include clean, clickable URLs for your LinkedIn profile and GitHub portfolio.",
            "suggested_rewrite": "Links: linkedin.com/in/[your-handle] | github.com/[your-handle]"
        })

    sec_map = {s["name"]: s["present"] for s in sections}
    if not sec_map.get("Education"):
        recs.append({
            "issue": "Missing Education Section",
            "evidence": "No distinct 'Education' or 'Academic Background' heading detected.",
            "requirement": "Educational eligibility check",
            "why_it_matters": "Many ATS filters screen candidates by degree type, field of study, and graduation year.",
            "priority": "High",
            "action": "Add an explicit 'Education' section stating degree, university, and graduation year.",
            "suggested_rewrite": "Education:\nBachelor of Technology in Computer Science | [University Name] | 2021 - 2025"
        })

    if not sec_map.get("Technical Skills"):
        recs.append({
            "issue": "Missing Dedicated Skills Section",
            "evidence": "No explicit 'Skills' or 'Technical Skills' heading found.",
            "requirement": "Keyword indexing",
            "why_it_matters": "ATS parsers look for standard categorized headings to index your technical core competencies.",
            "priority": "High",
            "action": "Group your technical proficiencies under a clear 'Technical Skills' heading.",
            "suggested_rewrite": "Technical Skills:\n- Languages: Python, JavaScript, SQL\n- Frameworks: React, Flask\n- Tools & Databases: Git, PostgreSQL, Docker"
        })

    list_only = skills_data.get("list_only_skills", [])
    if list_only:
        sample_unsub = list_only[:4]
        recs.append({
            "issue": "Skills Listed Without Project Evidence",
            "evidence": f"Skills listed without implementation context: {', '.join(sample_unsub)}",
            "requirement": "Demonstrated technical proficiency",
            "why_it_matters": "Modern ATS parsers and hiring managers discount bare lists of keywords unless supported by project bullet points.",
            "priority": "Medium",
            "action": "Integrate these technologies into your project descriptions, explaining what you engineered.",
            "suggested_rewrite": f"Example project bullet: Built a data service using {sample_unsub[0]}, improving API response latency by [X]%."
        })

    if formatting.get("metrics_count", 0) < 2:
        recs.append({
            "issue": "Lack of Quantifiable Achievements",
            "evidence": f"Only {formatting.get('metrics_count', 0)} quantified metric(s) found in bullet points.",
            "requirement": "Business impact and outcome validation",
            "why_it_matters": "Resumes with measurable results convert to interviews 3x more often than generic task lists.",
            "priority": "High",
            "action": "Follow the Google XYZ formula: 'Accomplished [X] as measured by [Y] by doing [Z]'.",
            "suggested_rewrite": "Draft template: 'Optimized database queries by indexing foreign keys, reducing query execution time by 30%.'"
        })

    if formatting.get("action_verb_count", 0) < 4:
        recs.append({
            "issue": "Weak or Passive Action Verbs",
            "evidence": f"Only {formatting.get('action_verb_count', 0)} strong action verb(s) detected.",
            "requirement": "Active professional framing",
            "why_it_matters": "Passive language ('responsible for', 'assisted with') diminishes perceived ownership of technical deliverables.",
            "priority": "Medium",
            "action": "Begin every bullet point with an assertive engineering verb such as 'Architected', 'Implemented', 'Automated', or 'Streamlined'.",
            "suggested_rewrite": "Instead of 'Helped with backend APIs', use 'Architected RESTful endpoints in Flask handling 10k+ daily transactions.'"
        })

    for warn in skills_data.get("stuffing_warnings", []):
        recs.append({
            "issue": "Potential Keyword Stuffing Detected",
            "evidence": warn,
            "requirement": "Natural language context",
            "why_it_matters": "Modern ATS parsers penalize repetitive keyword blocks without accompanying sentence structure.",
            "priority": "High",
            "action": "Distribute keyword mentions naturally across projects rather than repeating them in multiple places.",
            "suggested_rewrite": "Maintain 1-2 contextual mentions per project rather than repetitive listing."
        })

    if jd_analysis.get("has_meaningful_jd"):
        missing_req = jd_analysis.get("required_skills", {}).get("missing", [])
        if missing_req:
            top_missing = missing_req[:4]
            recs.append({
                "issue": "Missing Required Job Skills",
                "evidence": f"The job description specifies required skills missing from your resume: {', '.join(top_missing)}",
                "requirement": f"Core qualifications for {jd_analysis.get('target_role', 'this role')}",
                "why_it_matters": "ATS filters will score your profile lower if mandatory technical skills are omitted.",
                "priority": "High",
                "action": f"If you have hands-on experience with {', '.join(top_missing)}, add relevant project bullets highlighting them.",
                "suggested_rewrite": f"Optional verification: 'Engineered backend components using {top_missing[0]} to support scalable service operations.'"
            })

    return recs

def generate_problems_and_recommendations(
    contact_info: Dict[str, Any],
    sections: List[Dict[str, Any]],
    skills: List[str],
    formatting: Dict[str, Any],
    jd_analysis: Dict[str, Any],
    score: int
) -> Tuple[List[str], List[str]]:
    """
    Backwards-compatible generator returning string lists for problems and recommendations.
    Maintains exact string substrings expected by existing tests like test_05 and test_19.
    """
    problems = []
    recommendations = []

    if not contact_info["email"]["present"]:
        problems.append("Your email address was not detected. Recruiters and ATS systems cannot reach you without contact details.")
        recommendations.append("Add a professional email address (e.g., firstname.lastname@email.com) clearly in your header.")
    if not contact_info["phone"]["present"]:
        problems.append("Your phone number was not detected in the document text.")
        recommendations.append("Include an active phone number with country/area code in the contact section.")
    if not contact_info["linkedin"]["present"]:
        problems.append("LinkedIn profile link was not detected.")
        recommendations.append("Add your customized LinkedIn profile link (e.g., linkedin.com/in/yourname) to your header.")
    if not contact_info["github"]["present"]:
        problems.append("GitHub profile link was not detected.")
        recommendations.append("Include a link to your active GitHub profile displaying personal projects and contributions.")

    sec_map = {s["name"]: s["present"] for s in sections}
    if not sec_map.get("Education"):
        problems.append("No dedicated 'Education' section was detected. ATS parsers categorize qualifications by this heading.")
        recommendations.append("Add a clearly labeled 'Education' heading detailing your degree, institution, and graduation year.")
    if not sec_map.get("Projects"):
        problems.append("No dedicated 'Projects' section found. Projects are critical evidence of hands-on ability for students and engineers.")
        recommendations.append("Create a 'Projects' section featuring 2-3 significant software applications with live links.")
    if not sec_map.get("Technical Skills"):
        problems.append("Missing a dedicated 'Technical Skills' section. Keyword density is heavily evaluated through this block.")
        recommendations.append("Group your technical skills into clean categories (Languages, Frameworks, Databases, Tools).")

    if formatting["word_count"] < 350:
        problems.append(f"Resume text is too brief ({formatting['word_count']} words). Resumes with under 350 words appear incomplete.")
        recommendations.append("Expand on your project contributions, technologies used, and specific architectural decisions.")
    elif formatting["word_count"] > 800:
        problems.append(f"Resume length ({formatting['word_count']} words) is longer than recommended for standard 1-page ATS screening.")
        recommendations.append("Condense bullet points to focus exclusively on high-impact accomplishments and relevant tech stack.")

    if formatting["action_verb_count"] < 4:
        problems.append("Low usage of strong action verbs. Bullet points lack dynamic impact.")
        recommendations.append("Begin every bullet point with an assertive action verb (e.g., Engineered, Optimized, Automated, Deployed).")

    if formatting["metrics_count"] < 2:
        problems.append("Lack of quantifiable achievements (percentages, user numbers, latency improvements).")
        recommendations.append("Add measurable outcomes to your bullet points (e.g., 'reduced load time by 30%', 'serving 1,000+ daily users').")

    if jd_analysis.get("has_meaningful_jd") and jd_analysis.get("missing_keywords"):
        missing_top = jd_analysis["missing_keywords"][:4]
        problems.append(f"Missing required skills from job posting: {', '.join(missing_top)}.")
        recommendations.append(f"Incorporate relevant experience with {', '.join(missing_top)} if you possess those proficiencies.")

    return problems, recommendations

# ==============================================================================
# 8. MASTER ANALYSIS ENTRY POINT
# ==============================================================================

def analyze_resume(text: str, job_description: str = "") -> Dict[str, Any]:
    """
    Main entry point for Evidence-Based ATS Resume Analysis.
    Evaluates:
    - Job Match Score (0-100): Available only when meaningful JD is provided.
    - Resume Quality Score (0-100): Independent assessment of resume strength.
    - Detailed evidence extraction and grounded recommendations.
    """
    if not text or not text.strip() or len(text.strip().split()) < 15:
        return {
            "error": "The uploaded document contains insufficient readable text. Please upload a valid PDF or DOCX file with readable text content.",
            "success": False
        }

    raw_text = text.strip()

    sections_dict = partition_resume_sections(raw_text)
    contact_info = extract_contact_info(raw_text)
    sections = detect_sections(raw_text)
    skills_data = extract_skills_with_evidence(raw_text, sections_dict)
    skills = skills_data["all_skills"]
    formatting = analyze_formatting_and_readability(raw_text)

    jd_analysis = compare_job_description(raw_text, skills, job_description, sections_dict)

    quality_score, quality_breakdown = compute_resume_quality_score(
        contact_info, sections, skills, formatting, sections_dict, raw_text
    )

    legacy_score, category_scores = compute_ats_score(
        contact_info, sections, skills, formatting, jd_analysis, quality_score=quality_score
    )

    problems, legacy_recommendations = generate_problems_and_recommendations(
        contact_info, sections, skills, formatting, jd_analysis, legacy_score
    )

    evidence_recommendations = generate_evidence_recommendations(
        contact_info, sections, skills_data, formatting, jd_analysis, sections_dict, quality_score
    )

    def get_rating(s: int) -> Tuple[str, str]:
        if s >= 80: return "Strong / Highly Competitive", "pill-good"
        elif s >= 60: return "Moderate / Competitive with Minor Improvements", "pill-warn"
        elif s >= 40: return "Needs Targeted Improvement", "pill-bad"
        else: return "Weak / Incomplete Evidence", "pill-bad"

    quality_rating, quality_badge = get_rating(quality_score)
    
    has_meaningful_jd = jd_analysis.get("has_meaningful_jd", False) and jd_analysis.get("job_match_score") is not None
    primary_score = jd_analysis["job_match_score"] if has_meaningful_jd else quality_score
    score_rating, score_badge = get_rating(primary_score)

    projects_detected = next((s["present"] for s in sections if s["name"] == "Projects"), False)
    project_mentions = max(1 if projects_detected else 0, raw_text.lower().count("project"))

    return {
        "success": True,
        # Two Distinct Scores
        "job_match_score": jd_analysis.get("job_match_score"),
        "quality_score": quality_score,
        "score": primary_score,
        "score_rating": score_rating,
        "score_badge": score_badge,
        "quality_rating": quality_rating,
        "quality_badge": quality_badge,
        
        # Details & Breakdowns
        "quality_breakdown": quality_breakdown,
        "category_scores": category_scores,
        "contact_info": contact_info,
        "sections": sections,
        "missing_sections": [s["name"] for s in sections if not s["present"]],
        "skills_analysis": {
            "detected_skills": skills,
            "skill_count": len(skills),
            "substantiated_skills": skills_data["substantiated_skills"],
            "list_only_skills": skills_data["list_only_skills"],
            "substantiation_ratio": skills_data["substantiation_ratio"]
        },
        "job_match": jd_analysis,
        "formatting_audit": formatting,
        "problems": problems,
        "suggestions": legacy_recommendations,
        "recommendations": legacy_recommendations,
        "evidence_recommendations": evidence_recommendations,
        "project_count": min(10, project_mentions),
        "disclaimer": (
            "Disclaimer: This analysis provides diagnostic feedback on resume structure, evidence completeness, "
            "and keyword relevance. It is NOT an official employer ATS algorithm score and does not guarantee interviews or hiring outcomes."
        ),
        "limitations": (
            "This analysis uses text extraction, section partitioning, and weighted requirement heuristics. "
            "It does not visually evaluate complex graphical layouts or image-only content."
        ),
        "summary": (
            f"Analysis complete: Resume Quality is {quality_score}/100. " +
            (f"Job Match is {jd_analysis['job_match_score']}/100." if has_meaningful_jd else "Job Match is unavailable (no target job description provided).")
        )
    }
