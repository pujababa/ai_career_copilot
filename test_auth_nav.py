import os
import re
import unittest
from app import app, get_db, hash_password, check_password, is_valid_email, validate_password_strength, ADMIN_EMAIL, ADMIN_PASSWORD

class AuthAndNavTestCase(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        conn = get_db()
        conn.execute("DELETE FROM users WHERE email = 'teststudent_part1_valid@example.com'")
        conn.commit()
        conn.close()

    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

    def test_01_valid_signup(self):
        test_email = "teststudent_part1_valid@example.com"
        # Cleanup if previously created
        conn = get_db()
        conn.execute("DELETE FROM users WHERE email = ?", (test_email,))
        conn.commit()
        conn.close()

        res = self.client.post("/signup", data={
            "name": "Test Student Valid",
            "email": test_email,
            "password": "Pu@12345",
            "confirm_password": "Pu@12345",
            "target_role": "Software Developer"
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)
        self.assertIn("/student-login", res.headers.get("Location", ""))

        # Verify user in database
        conn = get_db()
        user = conn.execute("SELECT id, name, email, password, role, approved FROM users WHERE email = ?", (test_email,)).fetchone()
        conn.close()
        self.assertIsNotNone(user)
        self.assertTrue(check_password("Pu@12345", user["password"]))
        self.assertEqual(user["role"], "student")
        self.assertEqual(user["approved"], 1)

    def test_02_invalid_emails(self):
        invalid_emails = ["puja", "puja@", "@gmail.com", "puja@gmail", "puja@gmail."]
        for bad_email in invalid_emails:
            self.assertFalse(is_valid_email(bad_email), f"Failed to reject: {bad_email}")
            res = self.client.post("/signup", data={
                "name": "Bad Email User",
                "email": bad_email,
                "password": "Pu@12345",
                "confirm_password": "Pu@12345",
                "target_role": "Software Developer"
            }, follow_redirects=True)
            self.assertIn(b"Please enter a valid email address.", res.data)

    def test_03_valid_emails(self):
        valid_emails = ["puja@gmail.com", "test.user@domain.co", "student+tag@university.edu"]
        for good_email in valid_emails:
            self.assertTrue(is_valid_email(good_email), f"Failed to accept: {good_email}")

    def test_04_password_shorter_than_8(self):
        pw = "Pu@1234"  # 7 chars
        valid, msg = validate_password_strength(pw)
        self.assertFalse(valid)
        self.assertEqual(msg, "Password must be at least 8 characters long.")
        res = self.client.post("/signup", data={
            "name": "Short Pw",
            "email": "shortpw@example.com",
            "password": pw,
            "confirm_password": pw,
            "target_role": "Developer"
        }, follow_redirects=True)
        self.assertIn(b"Password must be at least 8 characters long.", res.data)

    def test_05_password_longer_than_8(self):
        # Passwords of 8 or more characters are accepted when otherwise valid
        pw = "Pu@123456"  # 9 chars
        valid, msg = validate_password_strength(pw)
        self.assertTrue(valid, f"Expected 9-character valid password to be accepted, got: {msg}")
        self.assertIsNone(msg)

    def test_06_password_without_number(self):
        pw = "Pu@abcdef"  # 9 chars, no digit
        valid, msg = validate_password_strength(pw)
        self.assertFalse(valid)
        self.assertEqual(msg, "Password must contain at least one letter, one number, and one special character.")
        res = self.client.post("/signup", data={
            "name": "No Num Pw",
            "email": "nonum@example.com",
            "password": pw,
            "confirm_password": pw,
            "target_role": "Developer"
        }, follow_redirects=True)
        self.assertIn(b"Password must contain at least one letter, one number, and one special character.", res.data)

    def test_07_password_without_special_char(self):
        pw = "puja1234"  # 8 chars, no special char
        valid, msg = validate_password_strength(pw)
        self.assertFalse(valid)
        self.assertEqual(msg, "Password must contain at least one letter, one number, and one special character.")
        res = self.client.post("/signup", data={
            "name": "No Special Pw",
            "email": "nospecial@example.com",
            "password": pw,
            "confirm_password": pw,
            "target_role": "Developer"
        }, follow_redirects=True)
        self.assertIn(b"Password must contain at least one letter, one number, and one special character.", res.data)

    def test_08_password_without_letter(self):
        pw = "123456@#"  # 8 chars, no letter
        valid, msg = validate_password_strength(pw)
        self.assertFalse(valid)
        self.assertEqual(msg, "Password must contain at least one letter, one number, and one special character.")
        res = self.client.post("/signup", data={
            "name": "No Letter Pw",
            "email": "noletter@example.com",
            "password": pw,
            "confirm_password": pw,
            "target_role": "Developer"
        }, follow_redirects=True)
        self.assertIn(b"Password must contain at least one letter, one number, and one special character.", res.data)

    def test_09_valid_exactly_8_character_password(self):
        valid_passwords = ["Pu@12345", "Pu@123456", "Ab#987654321", "P@ssw0rdLong", "xY!23456"]
        for pw in valid_passwords:
            self.assertGreaterEqual(len(pw), 8)
            valid, msg = validate_password_strength(pw)
            self.assertTrue(valid, f"Expected {pw} to be valid but got error: {msg}")

    def test_10_normal_login(self):
        # 1. Test student login
        test_email = "teststudent_part1_valid@example.com"
        res = self.client.post("/login", data={
            "email": test_email,
            "password": "Pu@12345"
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/dashboard", res.headers.get("Location", ""))

        # 2. Test admin login via registered email
        from app import ADMIN_EMAIL, ADMIN_PASSWORD
        res_admin = self.client.post("/admin-login", data={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, follow_redirects=False)
        self.assertEqual(res_admin.status_code, 302)
        self.assertIn("/admin", res_admin.headers.get("Location", ""))

        # 3. Test admin login via 'admin' username alias
        res_alias = self.client.post("/admin-login", data={
            "email": "admin",
            "password": ADMIN_PASSWORD
        }, follow_redirects=False)
        self.assertEqual(res_alias.status_code, 302)
        self.assertIn("/admin", res_alias.headers.get("Location", ""))

        # 4. Test admin login via 'admin@example.com' placeholder alias
        res_placeholder = self.client.post("/admin-login", data={
            "email": "admin@example.com",
            "password": ADMIN_PASSWORD
        }, follow_redirects=False)
        self.assertEqual(res_placeholder.status_code, 302)
        self.assertIn("/admin", res_placeholder.headers.get("Location", ""))

    def test_09b_prompt_expected_passwords(self):
        """Verify the exact test cases specified in prompt:
        - puja1234 -> REJECT (missing special character)
        - Pu@1234 -> REJECT (fewer than 8 characters)
        - Pu@123456 -> ACCEPT (9 characters, meets all rules)
        - password -> REJECT (missing digit, missing special char)
        - 12345678 -> REJECT (missing letter, missing special char)
        - Pu@12345 -> ACCEPT (8 characters, meets all rules)
        """
        cases = [
            ("puja1234", False),
            ("Pu@1234", False),
            ("Pu@123456", True),
            ("password", False),
            ("12345678", False),
            ("Pu@12345", True),
        ]
        for pw, should_accept in cases:
            valid, msg = validate_password_strength(pw)
            if should_accept:
                self.assertTrue(valid, f"Expected {pw} to be ACCEPTED, but got: {msg}")
            else:
                self.assertFalse(valid, f"Expected {pw} to be REJECTED, but it was accepted")

    def test_10b_auth_rejections_and_session_safety(self):
        """Confirm incorrect password or unknown email is rejected without creating a session."""
        valid_student_email = "teststudent_part1_valid@example.com"
        from app import ADMIN_EMAIL

        # 1. Student wrong password
        with self.client.session_transaction() as sess:
            sess.clear()
        res = self.client.post("/login", data={
            "email": valid_student_email,
            "password": "WrongPw1!"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Invalid email or password", res.data)
        with self.client.session_transaction() as sess:
            self.assertNotIn("user_id", sess, "Failed login must not create an authenticated session")

        # 2. Student unknown email
        with self.client.session_transaction() as sess:
            sess.clear()
        res = self.client.post("/login", data={
            "email": "unknown_student_99999@example.com",
            "password": "Pu@12345"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Invalid email or password", res.data)
        with self.client.session_transaction() as sess:
            self.assertNotIn("user_id", sess)

        # 3. Admin wrong password
        with self.client.session_transaction() as sess:
            sess.clear()
        res = self.client.post("/admin-login", data={
            "email": ADMIN_EMAIL,
            "password": "WrongAdminPw1!"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Invalid admin credentials", res.data)
        with self.client.session_transaction() as sess:
            self.assertNotIn("user_id", sess)

        # 4. Admin unknown email
        with self.client.session_transaction() as sess:
            sess.clear()
        res = self.client.post("/admin-login", data={
            "email": "unknown_admin_99999@example.com",
            "password": "Pu@12345"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Invalid admin credentials", res.data)
        with self.client.session_transaction() as sess:
            self.assertNotIn("user_id", sess)

    def test_10c_password_change_flows(self):
        """Verify password validation during password change and reset flows."""
        test_email = "teststudent_part1_valid@example.com"
        # Login first
        self.client.post("/login", data={"email": test_email, "password": "Pu@12345"})

        # Try changing password with invalid password (length 7)
        res = self.client.post("/account-settings", data={
            "current_password": "Pu@12345",
            "new_password": "Pu@1234",
            "confirm_new_password": "Pu@1234"
        }, follow_redirects=True)
        self.assertIn(b"Password must be at least 8 characters long.", res.data)

        # Change password with valid exactly 8-char password
        res = self.client.post("/account-settings", data={
            "current_password": "Pu@12345",
            "new_password": "Nw@12345",
            "confirm_new_password": "Nw@12345"
        }, follow_redirects=True)
        self.assertIn(b"Password updated successfully", res.data)

        # Verify old password no longer works
        self.client.get("/logout")
        res_old = self.client.post("/login", data={"email": test_email, "password": "Pu@12345"}, follow_redirects=True)
        self.assertIn(b"Invalid email or password", res_old.data)

        # Verify new password works
        res_new = self.client.post("/login", data={"email": test_email, "password": "Nw@12345"}, follow_redirects=False)
        self.assertEqual(res_new.status_code, 302)
        self.assertIn("/dashboard", res_new.headers.get("Location", ""))

        # Reset back to Pu@12345 via /account-settings for test reproducibility
        self.client.post("/account-settings", data={
            "current_password": "Nw@12345",
            "new_password": "Pu@12345",
            "confirm_new_password": "Pu@12345"
        })

    def test_10d_existing_accounts_and_hashing_mechanism(self):
        """Confirm password hashing uses PBKDF2 and existing accounts remain intact."""
        from app import ADMIN_EMAIL, ADMIN_PASSWORD
        conn = get_db()
        admin_row = conn.execute("SELECT id, email, password, role FROM users WHERE email = ?", (ADMIN_EMAIL,)).fetchone()
        conn.close()
        self.assertIsNotNone(admin_row, "Admin account must exist and remain intact")
        self.assertEqual(admin_row["role"], "admin")
        self.assertTrue(admin_row["password"].startswith("pbkdf2:sha256:"), "Password hash must use PBKDF2:SHA256")
        self.assertTrue(check_password(ADMIN_PASSWORD, admin_row["password"]))

    def test_11_student_portal_navigation(self):
        # Student logs in
        self.client.post("/login", data={
            "email": "teststudent_part1_valid@example.com",
            "password": "Pu@12345"
        })
        # Visit student portal pages
        res_landing = self.client.get("/")
        self.assertEqual(res_landing.status_code, 200)
        self.assertIn(b"Student Portal", res_landing.data)

        res_student_login = self.client.get("/student-login")
        self.assertEqual(res_student_login.status_code, 200)

        res_dash = self.client.get("/dashboard")
        self.assertEqual(res_dash.status_code, 200)

        res_resume = self.client.get("/resume-analysis")
        self.assertEqual(res_resume.status_code, 200)

    def test_12_admin_portal_navigation(self):
        from app import ADMIN_EMAIL, ADMIN_PASSWORD
        self.client.post("/admin-login", data={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        res_landing = self.client.get("/")
        self.assertEqual(res_landing.status_code, 200)

        res_admin_login = self.client.get("/admin-login")
        self.assertEqual(res_admin_login.status_code, 200)

        res_admin_dash = self.client.get("/admin")
        self.assertEqual(res_admin_dash.status_code, 200)

        res_admin_users = self.client.get("/admin/users")
        self.assertEqual(res_admin_users.status_code, 200)

    def test_13_browser_back_navigation(self):
        # Simulate history traversal: Landing -> Student Portal -> Dashboard -> Resume Analyzer
        # User is authenticated
        self.client.post("/login", data={
            "email": "teststudent_part1_valid@example.com",
            "password": "Pu@12345"
        })
        # 1. Resume Analyzer
        res = self.client.get("/resume-analysis")
        self.assertEqual(res.status_code, 200)

        # 2. Press BACK -> Dashboard
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)

        # 3. Press BACK -> Student Portal (MUST NOT REDIRECT BACK TO DASHBOARD)
        res = self.client.get("/student-login")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Sign In", res.data)

        # 4. Press BACK -> Landing Page / Login Page (MUST NOT REDIRECT BACK TO DASHBOARD)
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"AI Career Copilot", res.data)

    def test_14_browser_forward_navigation(self):
        # Simulate Forward button traversal: Landing Page -> Student Portal -> Dashboard -> Resume Analyzer
        self.client.post("/login", data={
            "email": "teststudent_part1_valid@example.com",
            "password": "Pu@12345"
        })
        # 1. On Landing Page
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)

        # 2. Forward -> Student Portal
        res = self.client.get("/student-login")
        self.assertEqual(res.status_code, 200)

        # 3. Forward -> Dashboard
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)

        # 4. Forward -> Resume Analyzer
        res = self.client.get("/resume-analysis")
        self.assertEqual(res.status_code, 200)

    def test_15_logout(self):
        # Login first
        self.client.post("/login", data={
            "email": "teststudent_part1_valid@example.com",
            "password": "Pu@12345"
        })
        # Perform logout
        res = self.client.get("/logout")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/student-login", res.headers.get("Location", ""))
        # Verify Cache-Control header prevents caching
        cache_ctrl = res.headers.get("Cache-Control", "")
        self.assertIn("no-store", cache_ctrl)
        self.assertIn("no-cache", cache_ctrl)

    def test_16_browser_back_after_logout(self):
        # Login then logout
        self.client.post("/login", data={
            "email": "teststudent_part1_valid@example.com",
            "password": "Pu@12345"
        })
        self.client.get("/logout")

        # Now simulate pressing browser Back button to previously viewed protected dashboard
        res = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/student-login", res.headers.get("Location", ""))

    def test_17_protected_page_after_logout(self):
        # Test multiple protected endpoints without active session
        with self.client.session_transaction() as sess:
            sess.clear()

        protected_urls = ["/dashboard", "/resume-analysis", "/admin", "/account-settings", "/chat"]
        for url in protected_urls:
            res = self.client.get(url, follow_redirects=False)
            self.assertEqual(res.status_code, 302, f"Failed on {url}")
            # Verifies redirect location points to login or admin-login
            loc = res.headers.get("Location", "")
            self.assertTrue("login" in loc or "student-login" in loc or "admin-login" in loc, f"Invalid redirect location: {loc}")

    def test_18_next_param_redirection_on_protected_routes(self):
        with self.client.session_transaction() as sess:
            sess.clear()
        
        # Test student route redirects with next param
        res = self.client.get("/resume-builder", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        loc = res.headers.get("Location", "")
        self.assertIn("next=", loc)
        self.assertIn("resume-builder", loc)

        # Test admin route redirects with next param
        res = self.client.get("/admin/announcements", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        loc = res.headers.get("Location", "")
        self.assertIn("next=", loc)
        self.assertIn("announcements", loc)

    def test_19_login_with_next_param_redirects_to_target(self):
        # 1. Student login with next param
        res = self.client.post("/login?next=/settings", data={
            "email": "teststudent_part1_valid@example.com",
            "password": "Pu@12345"
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers.get("Location"), "/settings")

        # 2. Admin login with next param
        res = self.client.post("/admin-login?next=/admin/logs", data={
            "email": "admin",
            "password": ADMIN_PASSWORD
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers.get("Location"), "/admin/logs")

    def test_20_session_check_endpoint(self):
        # Unauthenticated
        with self.client.session_transaction() as sess:
            sess.clear()
        res = self.client.get("/api/auth/session-check")
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data.get("authenticated"))

        # Authenticated student
        self.client.post("/login", data={
            "email": "teststudent_part1_valid@example.com",
            "password": "Pu@12345"
        })
        res = self.client.get("/api/auth/session-check")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("authenticated"))
        self.assertEqual(data.get("role"), "student")

    def test_21_topbar_back_button_rendering(self):
        # Login as student
        self.client.post("/login", data={
            "email": "teststudent_part1_valid@example.com",
            "password": "Pu@12345"
        })
        
        # Subpage should have back button
        res = self.client.get("/settings")
        self.assertIn(b"navBackBtn", res.data)
        self.assertIn(b"handleNavigationBack", res.data)

        # Dashboard should not have back button
        res = self.client.get("/dashboard")
        self.assertNotIn(b"navBackBtn", res.data)

if __name__ == "__main__":
    unittest.main()
