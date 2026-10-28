import io
import os
import zipfile
import unittest
from app import app, get_db, hash_password
from ats_engine import (
    extract_text_from_file,
    extract_contact_info,
    detect_sections,
    extract_skills_from_text,
    compare_job_description,
    analyze_formatting_and_readability,
    compute_ats_score,
    analyze_resume
)


def create_minimal_pdf_bytes(text_lines):
    """Construct a minimal valid PDF with Helvetica text stream."""
    stream_lines = ["BT", "/F1 12 Tf", "50 750 Td", "14 TL"]
    for i, line in enumerate(text_lines):
        clean = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if i == 0:
            stream_lines.append(f"({clean}) Tj")
        else:
            stream_lines.append(f"T* ({clean}) Tj")
    stream_lines.append("ET")
    stream_data = "\n".join(stream_lines).encode("latin1")
    stream_len = len(stream_data)

    header = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        + f"5 0 obj << /Length {stream_len} >> stream\n".encode("latin1")
    )
    trailer = (
        b"\nendstream\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n9999\n%%EOF"
    )
    return header + stream_data + trailer


def create_minimal_docx_bytes(paragraphs):
    """Construct a minimal valid .docx archive in memory."""
    from xml.sax.saxutils import escape
    buf = io.BytesIO()
    p_xmls = "".join(f"<w:p><w:r><w:t>{escape(p)}</w:t></w:r></w:p>" for p in paragraphs)
    body_xml = f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{p_xmls}</w:body></w:document>'
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", body_xml)
    buf.seek(0)
    return buf.getvalue()


class ResumeATSTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

        # Set up an isolated test user
        self.test_email = "test_ats_user_p2@example.com"
        conn = get_db()
        conn.execute("DELETE FROM users WHERE email = ?", (self.test_email,))
        conn.execute(
            "INSERT INTO users (name, email, password, role, approved) VALUES (?, ?, ?, 'student', 1)",
            ("Test ATS Student", self.test_email, hash_password("Pu@12345"))
        )
        conn.commit()
        conn.close()

        # Log in test user
        self.client.post("/login", data={"email": self.test_email, "password": "Pu@12345"})

    def tearDown(self):
        conn = get_db()
        conn.execute("DELETE FROM users WHERE email = ?", (self.test_email,))
        conn.commit()
        conn.close()

    # 1. Strong synthetic resume
    def test_01_strong_synthetic_resume(self):
        strong_resume = """
        Alex Johnson
        alex.johnson@example.com | +1 (555) 234-5678 | San Francisco, CA
        https://linkedin.com/in/alexjohnson | https://github.com/alexjohnson | https://alexj.dev

        Professional Summary
        Results-driven Full Stack Engineer with 3+ years of experience designing scalable distributed web architectures.
        Specialized in microservices, cloud deployments, and high-performance backend APIs.

        Technical Skills
        Languages: Python, JavaScript, TypeScript, Go, SQL, HTML5, CSS3
        Frameworks & Libraries: React, Node.js, Express, Flask, FastAPI, Django
        Databases: PostgreSQL, MongoDB, Redis, SQLite
        Cloud & DevOps: Docker, Kubernetes, AWS, CI/CD, Git, Linux, Nginx

        Professional Experience
        Senior Software Engineer - CloudScale Technologies (2023 - Present)
        - Engineered robust microservices handling 25,000+ daily API requests using Python and FastAPI.
        - Optimized database queries in PostgreSQL, reducing average query latency by 35%.
        - Architected automated CI/CD deployment pipelines using Docker and GitHub Actions, accelerating release cycles by 40%.
        - Built real-time analytics dashboards using React and WebSocket streams for 500+ enterprise clients.

        Education
        Bachelor of Science in Computer Science - University of California (GPA: 3.8/4.0)

        Projects
        Distributed Task Queue
        - Developed an asynchronous task worker in Python and Redis handling 10,000+ background jobs per hour.
        - Implemented fault-tolerant retry mechanics and dead-letter queues.

        Certifications
        - AWS Certified Solutions Architect
        """
        result = analyze_resume(strong_resume)
        self.assertTrue(result["success"])
        score = result["score"]
        self.assertGreaterEqual(score, 80, f"Expected strong resume score >= 80, got {score}")
        self.assertNotEqual(score, 97, "Score must be dynamic and evidence-based, not hardcoded to 97")
        self.assertTrue(result["contact_info"]["name"]["present"])
        self.assertTrue(result["contact_info"]["email"]["present"])
        self.assertTrue(result["contact_info"]["linkedin"]["present"])
        self.assertTrue(result["contact_info"]["github"]["present"])
        self.assertGreaterEqual(len(result["skills_analysis"]["detected_skills"]), 10)

    # 2. Weak synthetic resume
    def test_02_weak_synthetic_resume(self):
        weak_resume = """
        Looking for a job.
        I am hardworking and punctual.
        I know how to use Microsoft Word and browsing the web.
        I also learned basic Python last month.
        Please contact me for an interview.
        """
        result = analyze_resume(weak_resume)
        self.assertTrue(result["success"])
        score = result["score"]
        self.assertLessEqual(score, 45, f"Expected weak resume score <= 45, got {score}")
        self.assertFalse(result["contact_info"]["email"]["present"])
        self.assertFalse(result["contact_info"]["phone"]["present"])
        self.assertGreater(len(result["problems"]), 2)

    # 3. Student resume with projects but no professional experience
    def test_03_student_resume_with_projects(self):
        student_resume = """
        Pooja Sharma
        pooja.sharma@example.com | +91 9876543210 | Bangalore, India
        https://linkedin.com/in/poojasharma | https://github.com/poojasharma

        Career Objective
        Enthusiastic Computer Science undergraduate seeking an entry-level Software Developer role to apply algorithms, full-stack web development, and problem-solving skills.

        Education
        Bachelor of Technology in Computer Science & Engineering (2022 - 2026)
        National Institute of Technology - CGPA: 8.7/10

        Technical Skills
        Languages: Python, C++, Java, JavaScript, SQL, HTML, CSS
        Frameworks: React, Flask, Node.js
        Tools & Technologies: Git, GitHub, MySQL, MongoDB, Linux

        Academic Projects
        AI Career Copilot Web Platform
        - Developed full-stack placement portal using Flask, SQLite, and vanilla JavaScript.
        - Implemented automated scoring heuristics and integrated Gemini API for student coaching.
        - Designed responsive glassmorphic UI tested across 50+ user flows.

        Campus Placement Tracker
        - Built placement management system with real-time status tracking for 300+ students.
        - Engineered SQL schema with foreign keys and multi-tenant isolation.

        Internship Experience
        Web Development Intern - TechStartup Labs (Summer 2025)
        - Built 5 responsive dashboard components in React and integrated REST APIs.
        - Automated unit tests covering 85% of core user routes.
        """
        result = analyze_resume(student_resume)
        self.assertTrue(result["success"])
        score = result["score"]
        # Fair student evaluation: should score competitively (65 - 88)
        self.assertGreaterEqual(score, 65, f"Expected student resume with strong projects >= 65, got {score}")
        self.assertLessEqual(score, 90)
        self.assertTrue(result["contact_info"]["name"]["present"])
        self.assertTrue(result["contact_info"]["email"]["present"])
        # Projects section must be detected
        sec_map = {s["name"]: s["present"] for s in result["sections"]}
        self.assertTrue(sec_map.get("Projects"))
        self.assertTrue(sec_map.get("Education"))

    # 4. Resume with LinkedIn and GitHub
    def test_04_resume_with_linkedin_and_github(self):
        text = """
        Jane Developer
        jane@example.com | 555-0199
        https://linkedin.com/in/janedev | https://github.com/janedev
        Education: B.S. in Computer Science
        Skills: Python, SQL, Git
        Projects: Built web application
        """
        result = analyze_resume(text)
        self.assertTrue(result["contact_info"]["linkedin"]["present"])
        self.assertEqual(result["contact_info"]["linkedin"]["status"], "Present")
        self.assertTrue(result["contact_info"]["github"]["present"])
        self.assertEqual(result["contact_info"]["github"]["status"], "Present")

    # 5. Resume without LinkedIn and GitHub
    def test_05_resume_without_linkedin_and_github(self):
        text = """
        John Smith
        john@example.com | 555-0122 | Austin, TX
        Education: B.S. in Computer Engineering
        Skills: Python, C++, SQL, HTML
        Projects: Embedded system monitor
        Experience: Junior Software Engineer
        """
        result = analyze_resume(text)
        self.assertFalse(result["contact_info"]["linkedin"]["present"])
        self.assertEqual(result["contact_info"]["linkedin"]["status"], "Missing")
        self.assertFalse(result["contact_info"]["github"]["present"])
        self.assertEqual(result["contact_info"]["github"]["status"], "Missing")
        # Should not crash and should report factually
        self.assertIn("LinkedIn profile link was not detected.", result["problems"])

    # 6. Heading variations recognition
    def test_06_heading_variations(self):
        text = """
        Rahul Verma
        rahul@example.com | 9988776655

        Academic Background
        Bachelor of Engineering in Information Technology

        Core Competencies
        Python, JavaScript, React, Docker, SQL

        Key Projects
        E-Commerce Platform with microservices architecture

        Employment History
        Software Trainee at Tech Corp
        """
        sections = detect_sections(text)
        sec_map = {s["name"]: s["present"] for s in sections}
        self.assertTrue(sec_map.get("Education"), "Academic Background should match Education")
        self.assertTrue(sec_map.get("Technical Skills"), "Core Competencies should match Technical Skills")
        self.assertTrue(sec_map.get("Projects"), "Key Projects should match Projects")
        self.assertTrue(sec_map.get("Experience / Work History"), "Employment History should match Experience")

    # 7. Skill extraction and normalization
    def test_07_skill_extraction_and_normalization(self):
        text = "Experienced in python3, reactjs, k8s, postgres, AWS, and ci/cd pipelines."
        skills = extract_skills_from_text(text)
        self.assertIn("Python", skills)
        self.assertIn("React", skills)
        self.assertIn("Kubernetes", skills)
        self.assertIn("PostgreSQL", skills)
        self.assertIn("AWS", skills)
        self.assertIn("CI/CD", skills)

    # 8. Resume missing some skills required by Job Description
    def test_08_job_description_missing_skills(self):
        resume_text = "Experienced in Python, Flask, Git, and SQL development."
        resume_skills = ["Python", "Flask", "Git", "SQL"]
        jd_text = """
        We are seeking a Backend Developer with:
        - Python
        - Flask
        - PostgreSQL
        - Docker
        - Kubernetes
        - Redis
        """
        match = compare_job_description(resume_text, resume_skills, jd_text)
        self.assertTrue(match["has_jd"])
        self.assertTrue(match["keywords_found"])
        self.assertIn("Python", match["matched_keywords"])
        self.assertIn("Flask", match["matched_keywords"])
        self.assertIn("Docker", match["missing_keywords"])
        self.assertIn("Kubernetes", match["missing_keywords"])
        self.assertIn("Redis", match["missing_keywords"])
        self.assertLess(match["match_rate"], 100)

    # 9. Resume with no Job Description
    def test_09_no_job_description(self):
        text = """
        Dev User
        dev@example.com | 1234567890
        Education: B.Tech Computer Science
        Skills: Python, Django, PostgreSQL
        Projects: Web Portal
        """
        result = analyze_resume(text, job_description="")
        self.assertFalse(result["job_match"]["has_jd"])
        self.assertEqual(result["job_match"]["matched_keywords"], [])
        self.assertEqual(result["job_match"]["missing_keywords"], [])
        self.assertEqual(result["job_match"]["match_rate"], 0)

    # 10. Empty or unreadable document
    def test_10_empty_document_rejected(self):
        empty_text = "   \n\t  "
        result = analyze_resume(empty_text)
        self.assertFalse(result["success"])
        self.assertIn("insufficient readable text", result["error"])

    # 11. Corrupt or invalid upload format via HTTP endpoint
    def test_11_invalid_format_endpoint(self):
        data = {
            "resume": (io.BytesIO(b"Hello world text"), "resume.txt")
        }
        res = self.client.post("/resume-analysis", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        json_data = res.get_json()
        self.assertIn("Unsupported file format", json_data["error"])

    # 12. PDF upload via endpoint
    def test_12_pdf_upload_endpoint(self):
        pdf_lines = [
            "Sarah Connor",
            "sarah@example.com | 555-0100 | Los Angeles, CA",
            "https://linkedin.com/in/sarahconnor | https://github.com/sarahconnor",
            "Education: BS in Computer Science",
            "Skills: Python, C++, SQL, Docker, Git",
            "Projects: Automated Defense Tracker with 99% uptime",
            "Experience: Systems Engineer, built real-time monitor"
        ]
        pdf_bytes = create_minimal_pdf_bytes(pdf_lines)
        data = {
            "resume": (io.BytesIO(pdf_bytes), "sarah_resume.pdf")
        }
        res = self.client.post("/resume-analysis", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data["success"])
        self.assertGreater(json_data["score"], 40)
        self.assertIn("Python", json_data["skills_analysis"]["detected_skills"])

    # 13. DOCX upload via endpoint
    def test_13_docx_upload_endpoint(self):
        docx_lines = [
            "Michael Scott",
            "michael@example.com | 555-0188 | Scranton, PA",
            "Education: Bachelor of Business & Technology",
            "Technical Skills: Python, SQL, JavaScript, HTML, CSS, React",
            "Projects: Paper Sales Portal with 500+ daily orders",
            "Experience: Regional Lead, developed tracking tools"
        ]
        docx_bytes = create_minimal_docx_bytes(docx_lines)
        data = {
            "resume": (io.BytesIO(docx_bytes), "michael_resume.docx")
        }
        res = self.client.post("/resume-analysis", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data["success"])
        self.assertGreater(json_data["score"], 40)
        self.assertIn("Python", json_data["skills_analysis"]["detected_skills"])

    # 14. Job Description with identifiable keywords
    def test_14_job_description_with_keywords(self):
        resume_text = """
        John Dev | john@example.com
        Education: BS Computer Science
        Skills: Python, Flask, PostgreSQL, Git
        Projects: API Platform
        """
        jd = "Seeking a Python backend engineer with Flask, PostgreSQL, and Git."
        result = analyze_resume(resume_text, job_description=jd)
        self.assertTrue(result["job_match"]["has_jd"])
        self.assertTrue(result["job_match"]["keywords_found"])
        self.assertIn("Python", result["job_match"]["matched_keywords"])
        self.assertIn("Flask", result["job_match"]["matched_keywords"])
        self.assertEqual(result["job_match"]["match_rate"], 100)

    # 15. Job Description with no meaningful detectable keywords
    def test_15_job_description_with_no_keywords(self):
        resume_text = """
        John Developer
        john@example.com | 555-0199 | Austin, TX
        Education: Bachelor of Science in Computer Science
        Technical Skills: Python, Flask, PostgreSQL, Git
        Projects: Web Application API Platform
        Experience: Junior Software Engineer
        """
        jd = "We are seeking a great team player who comes on time and is friendly."
        result = analyze_resume(resume_text, job_description=jd)
        self.assertTrue(result["job_match"]["has_jd"])
        self.assertFalse(result["job_match"]["keywords_found"])
        self.assertEqual(result["job_match"]["match_rate"], 0)
        self.assertIn("No recognizable technical keywords", result["job_match"]["note"])

    # 16. Score determinism
    def test_16_deterministic_scoring(self):
        resume_text = """
        Alice Smith
        alice@example.com | 555-0144
        https://github.com/alicesmith
        Education: BS Computer Science
        Technical Skills: Python, SQL, React, Docker
        Projects: Cloud File Manager built with Python and React
        Experience: Junior Software Developer
        """
        res1 = analyze_resume(resume_text)
        res2 = analyze_resume(resume_text)
        self.assertEqual(res1["score"], res2["score"], "Same input must produce exact same score")
        self.assertEqual(res1["category_scores"], res2["category_scores"])

    # 17. Dynamic range verification (different evidence produces different scores)
    def test_17_dynamic_scoring_range(self):
        strong = """
        Strong Engineer
        strong@example.com | 555-0199 | Austin, TX
        https://linkedin.com/in/strong | https://github.com/strong | https://strong.dev
        Summary: Expert developer with 5+ years experience.
        Education: MS Computer Science
        Skills: Python, Go, TypeScript, React, Docker, Kubernetes, AWS, PostgreSQL, Redis, GraphQL
        Experience: Lead Developer. Engineered cloud platform serving 1,000,000+ users. Optimized latency by 45%.
        Projects: Scalable cache system built with Go and Redis. Handled 50,000 requests per second.
        Certifications: AWS Solutions Architect
        """
        moderate = """
        Moderate Student
        student@example.com | 555-0155
        Education: BS in Computer Science
        Skills: Python, SQL, HTML
        Projects: Library management system built with Python
        """
        weak = """
        John Doe
        john@example.com | 555-0123
        Objective: Looking for an entry-level position. I am a hardworking candidate with basic knowledge of HTML and internet browsing. Available immediately for interview.
        """

        score_strong = analyze_resume(strong)["score"]
        score_moderate = analyze_resume(moderate)["score"]
        score_weak = analyze_resume(weak)["score"]

        self.assertGreater(score_strong, score_moderate, f"Strong ({score_strong}) must score higher than Moderate ({score_moderate})")
        self.assertGreater(score_moderate, score_weak, f"Moderate ({score_moderate}) must score higher than Weak ({score_weak})")
        self.assertNotEqual(score_strong, 97, "Strong score must not be default 97")
        self.assertNotEqual(score_moderate, 97, "Moderate score must not be default 97")
        self.assertNotEqual(score_weak, 97, "Weak score must not be default 97")

    # 18. File size limit enforcement
    def test_18_file_size_limit(self):
        large_bytes = b"0" * (6 * 1024 * 1024) # 6MB
        data = {
            "resume": (io.BytesIO(large_bytes), "large_resume.pdf")
        }
        res = self.client.post("/resume-analysis", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        self.assertIn("exceeds the 5MB size limit", res.get_json()["error"])

    # 19. Recommendations are specific to detected findings
    def test_19_recommendations_reflect_actual_findings(self):
        # Case A: Resume missing email, phone, and metrics
        text_missing = """
        Dev Tester
        Education: BS Computer Science
        Skills: Python, Django, SQL
        Projects: Inventory System built using Python and Django
        """
        res_missing = analyze_resume(text_missing)
        problems_joined = " ".join(res_missing["problems"])
        self.assertIn("email address was not detected", problems_joined)
        self.assertIn("phone number was not detected", problems_joined)

        # Case B: Resume with email, phone, metrics, and action verbs
        text_complete = """
        Dev Tester
        dev.tester@example.com | +1 555-123-4567 | San Francisco, CA
        https://linkedin.com/in/devtester | https://github.com/devtester
        Summary: Full stack developer with 3 years experience.
        Education: BS Computer Science
        Skills: Python, Django, PostgreSQL, Docker, Git, Redis
        Experience: Software Engineer at CloudCo. Engineered high-throughput microservices handling 5,000 requests per second. Reduced latency by 30%.
        Projects: Scalable Web Application with 1,000+ daily active users.
        """
        res_complete = analyze_resume(text_complete)
        problems_complete = " ".join(res_complete["problems"])
        self.assertNotIn("email address was not detected", problems_complete)
        self.assertNotIn("phone number was not detected", problems_complete)

    # 20. Missing sections reported only when genuinely not detected
    def test_20_missing_sections_reported_factually(self):
        text = """
        Candidate Name
        candidate@example.com | 555-0199
        Education: BS Computer Science
        Technical Skills: Python, SQL, React
        Projects: Capstone Project with React
        """
        res = analyze_resume(text)
        # Education, Skills, and Projects MUST NOT be in missing_sections
        self.assertNotIn("Education", res["missing_sections"])
        self.assertNotIn("Technical Skills", res["missing_sections"])
        self.assertNotIn("Projects", res["missing_sections"])
        # Experience, Certifications, Summary MUST be in missing_sections
        self.assertIn("Experience / Work History", res["missing_sections"])
        self.assertIn("Certifications", res["missing_sections"])
        self.assertIn("Summary / Objective", res["missing_sections"])

    # 21. Scanned / image-only PDF handling (no readable text layer)
    def test_21_scanned_image_only_pdf_handling(self):
        # Create an empty/scanned PDF without text layer
        import PyPDF2
        writer = PyPDF2.PdfWriter()
        writer.add_blank_page(width=595, height=842)
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        try:
            writer.write(tmp)
            tmp.close()
            text, err = extract_text_from_file(tmp.name, "scanned_invoice.pdf")
            self.assertIsNone(text)
            self.assertIsNotNone(err)
            self.assertIn("OCR (Optical Character Recognition) is not configured", err)
            self.assertIn("scanned image", err)
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    # 22. Completely irrelevant resume receives low Job Match Score (no inflation)
    def test_22_completely_irrelevant_resume_no_score_inflation(self):
        chef_resume = """
        Gordon Baker
        gordon@bistroparis.com | +1 555-987-6543 | Chicago, IL
        Professional Summary
        Passionate Executive Chef with 10 years of culinary leadership in high-volume fine dining kitchens.
        Specialized in French pastry, menu development, inventory control, and food safety standards.
        
        Experience
        Head Chef - Bistro Paris (2018 - Present)
        - Managed kitchen brigade of 18 sous chefs, line cooks, and dishwashers.
        - Redesigned seasonal tasting menus, increasing guest satisfaction ratings by 24%.
        - Enforced strict health and sanitation protocols across culinary operations.
        
        Education
        Associate Degree in Culinary Arts - Culinary Arts Academy
        """
        python_jd = """
        Job Title: Senior Python Backend Engineer
        Requirements:
        - 4+ years of professional backend development with Python and Flask or FastAPI
        - Extensive experience with PostgreSQL, Redis, and Docker containerization
        - Strong background in microservices, RESTful API design, and CI/CD pipelines
        """
        result = analyze_resume(chef_resume, job_description=python_jd)
        self.assertTrue(result["success"])
        job_match = result["job_match_score"]
        self.assertIsNotNone(job_match)
        self.assertLessEqual(job_match, 15, f"Irrelevant resume must score <= 15, got {job_match}")
        self.assertEqual(result["job_match"]["match_rate"], 0)
        self.assertEqual(result["job_match"]["matched_keywords"], [])

    # 23. Highly relevant resume with genuine project evidence rewarded
    def test_23_highly_relevant_resume_with_genuine_evidence(self):
        strong_resume = """
        Alex Rivera
        alex.rivera@example.com | +1 555-0144 | Seattle, WA
        https://linkedin.com/in/alexrivera | https://github.com/alexrivera

        Professional Summary
        Backend Engineer with 4 years of experience building high-throughput cloud services.

        Technical Skills
        Languages: Python, SQL
        Frameworks: Flask, FastAPI
        Databases: PostgreSQL, Redis
        DevOps: Docker, Git, CI/CD

        Professional Experience
        Software Engineer - CloudPlatform Inc. (2021 - Present)
        - Engineered distributed backend services using Python and Flask handling 50,000+ daily API requests.
        - Optimized database queries in PostgreSQL and added Redis caching, decreasing latency by 40%.
        - Deployed scalable microservices using Docker and automated CI/CD deployment pipelines.

        Projects
        Real-Time Metrics Engine
        - Built telemetry aggregation system using FastAPI and PostgreSQL with 99.9% uptime.

        Education
        Bachelor of Science in Computer Science - University of Washington (2021)
        """
        python_jd = """
        Job Title: Python Backend Engineer
        Required Qualifications:
        - Proficient in Python and Flask or FastAPI
        - Experience with PostgreSQL, Redis, and Docker
        - Hands-on experience with Git and CI/CD
        """
        result = analyze_resume(strong_resume, job_description=python_jd)
        self.assertTrue(result["success"])
        self.assertGreaterEqual(result["job_match_score"], 80)
        self.assertGreaterEqual(result["quality_score"], 80)
        self.assertGreaterEqual(len(result["job_match"]["required_skills"]["matched_with_evidence"]), 3)

    # 24. Keyword stuffing detected, penalized, and flagged
    def test_24_keyword_stuffing_detected_and_penalized(self):
        stuffed_resume = """
        John Stuffer
        john@example.com | 555-0199
        Education: BS Computer Science
        Skills: Python, Python, Python, Python, Python, Python, Python, Python, Flask, SQL
        Projects:
        Python Python Python system using Python and Flask for Python operations.
        """
        jd = "Seeking a Python backend developer with Flask and SQL."
        result = analyze_resume(stuffed_resume, job_description=jd)
        self.assertTrue(result["success"])
        stuffing_warnings = result["job_match"]["stuffing_warnings"]
        self.assertGreater(len(stuffing_warnings), 0)
        self.assertIn("Python", stuffing_warnings[0])
        self.assertIn("repeated", stuffing_warnings[0])

    # 25. Missing required skills properly categorized and reported
    def test_25_missing_required_skills_in_jd(self):
        resume_text = """
        Dev User
        dev@example.com | 555-0100
        Education: BS in Computer Science
        Technical Skills: Python, Flask, Git
        Projects: Web API Portal built with Flask
        """
        jd = """
        Job Title: Cloud Software Engineer
        Required Skills:
        - Python
        - Docker
        - Kubernetes
        - PostgreSQL
        - Redis
        """
        result = analyze_resume(resume_text, job_description=jd)
        self.assertTrue(result["success"])
        missing = result["job_match"]["missing_keywords"]
        self.assertIn("Docker", missing)
        self.assertIn("Kubernetes", missing)
        self.assertIn("PostgreSQL", missing)
        self.assertIn("Redis", missing)

    # 26. Transparent handling when no Job Description is provided
    def test_26_no_job_description_transparent_handling(self):
        resume_text = """
        Alex Engineer
        alex@example.com | 555-0199 | Austin, TX
        https://linkedin.com/in/alex | https://github.com/alex
        Professional Summary
        Dedicated Software Engineer with 2 years of experience building reliable web applications.
        Education: BS Computer Science
        Skills: Python, PostgreSQL, Docker, Git
        Projects: Inventory Service
        - Developed REST API with Python and PostgreSQL handling 10,000+ requests.
        - Optimized database schema and reduced query latency by 25%.
        """
        result = analyze_resume(resume_text, job_description="")
        self.assertTrue(result["success"])
        self.assertIsNone(result["job_match_score"])
        self.assertFalse(result["job_match"]["has_meaningful_jd"])
        self.assertIn("Unavailable", result["job_match"]["job_match_rating"])
        # Quality score evaluated independently
        self.assertGreater(result["quality_score"], 60)

    # 27. Skill alias normalization without duplicate counting
    def test_27_alias_normalization_and_duplicate_suppression(self):
        text = "Skilled in js, JavaScript, es6, NLP, and Natural Language Processing."
        skills = extract_skills_from_text(text)
        self.assertEqual(skills.count("JavaScript"), 1)
        # NLP and Natural Language Processing normalize to single canonical entry
        canonical_nlp = "NLP" if "NLP" in skills else "Natural Language Processing"
        self.assertIn(canonical_nlp, skills)
        # Should contain only 2 unique canonical skills
        self.assertEqual(len(skills), 2)

    # 28. Fresher with strong projects is not penalized for lacking full-time experience
    def test_28_fresher_strong_projects_not_penalized(self):
        fresher_resume = """
        Pooja Sharma
        pooja.sharma@example.com | +91 9876543210 | Bangalore, India
        https://linkedin.com/in/poojasharma | https://github.com/poojasharma

        Career Objective
        Recent Computer Science graduate seeking an entry-level Software Engineer role.

        Education
        Bachelor of Technology in Computer Science | CGPA: 8.9/10 (2020 - 2024)

        Technical Skills
        Languages: Python, JavaScript, SQL
        Frameworks: React, Flask
        Databases: PostgreSQL, SQLite
        Tools: Git, Docker, Postman

        Academic Projects
        Placement Analytics Portal (2024)
        - Engineered full-stack recruitment dashboard using Flask and PostgreSQL.
        - Implemented role-based authentication and secure session cookies for 500+ student profiles.
        - Optimized database queries, reducing analytics page load time by 35%.

        Campus Event Management System (2023)
        - Developed event booking application with React and Flask RESTful APIs.
        - Integrated automated QR-code attendance tracker reducing registration lines by 50%.
        """
        result = analyze_resume(fresher_resume)
        self.assertTrue(result["success"])
        # Section score should be strong (>= 20/25) despite no full-time experience
        self.assertGreaterEqual(result["quality_breakdown"]["sections"]["score"], 20)
        self.assertGreaterEqual(result["quality_score"], 75)

    # 29. Structured evidence-based recommendations format
    def test_29_evidence_based_recommendations_fields(self):
        resume_text = """
        John Developer
        john@example.com | 555-0123 | San Jose, CA
        Summary: Aspiring software developer with project experience.
        Education: BS Computer Science
        Technical Skills: Python, SQL, Git
        Projects: Task Management Application
        - Created task tracker using Python and SQL for user management.
        """
        result = analyze_resume(resume_text)
        self.assertTrue(result["success"])
        recs = result["evidence_recommendations"]
        self.assertGreater(len(recs), 0)
        for r in recs:
            self.assertIn("issue", r)
            self.assertIn("evidence", r)
            self.assertIn("why_it_matters", r)
            self.assertIn("action", r)
            self.assertIn("suggested_rewrite", r)

    # 30. Clear disclaimer present
    def test_30_disclaimer_and_no_fake_guarantee(self):
        resume_text = """
        Jane Developer | jane@example.com | 555-0100
        Education: BS Computer Science
        Skills: Python, Django
        Projects: Blog App
        """
        result = analyze_resume(resume_text)
        self.assertIn("disclaimer", result)
        self.assertIn("NOT an official employer ATS algorithm", result["disclaimer"])


if __name__ == "__main__":
    unittest.main()
