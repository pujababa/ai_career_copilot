import unittest
from unittest.mock import patch, MagicMock
import os
import json
import sqlite3

# Import Flask app and helpers
from app import (
    app,
    get_db,
    is_valid_client_secret,
    redact_sensitive_data,
    get_google_oauth_config,
    hash_password
)


class TestGoogleOAuth(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.config["SECRET_KEY"] = "test-secret-key-12345"
        self.client = app.test_client()

        # Set up a test database record if needed
        conn = get_db()
        conn.execute("DELETE FROM users WHERE email = 'oauth_test_user@example.com'")
        conn.commit()
        conn.close()

    def tearDown(self):
        conn = get_db()
        conn.execute("DELETE FROM users WHERE email = 'oauth_test_user@example.com'")
        conn.commit()
        conn.close()

    def test_is_valid_client_secret(self):
        """Verify client secret validation logic."""
        self.assertFalse(is_valid_client_secret(""))
        self.assertFalse(is_valid_client_secret(None))
        self.assertFalse(is_valid_client_secret("****wvxZ"))
        self.assertFalse(is_valid_client_secret("short"))
        self.assertTrue(is_valid_client_secret("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"))
        self.assertTrue(is_valid_client_secret("valid_secret_key_12345678"))

    def test_redact_sensitive_data(self):
        """Verify sensitive secrets are never leaked into logged strings."""
        test_secret = "super_secret_client_credential_999"
        message = f"Error communicating with {test_secret} at endpoint"
        redacted = redact_sensitive_data(message, additional_secrets=[test_secret])
        self.assertNotIn(test_secret, redacted)
        self.assertIn("[REDACTED_SECRET]", redacted)

    def test_google_login_initiates_oauth(self):
        """Verify /google-login generates state and redirects to Google auth."""
        with self.client:
            resp = self.client.get("/google-login")
            # Should redirect to Google accounts
            self.assertEqual(resp.status_code, 302)
            self.assertIn("accounts.google.com/o/oauth2/v2/auth", resp.location)
            self.assertIn("redirect_uri=http%3A%2F%2F127.0.0.1%3A10000%2Fgoogle-callback", resp.location)
            self.assertIn("response_type=code", resp.location)
            self.assertIn("scope=openid+email+profile", resp.location)
            # Session should contain oauth_state
            with self.client.session_transaction() as sess:
                self.assertIn("oauth_state", sess)
                self.assertIn("oauth_redirect_uri", sess)
                self.assertEqual(sess["oauth_redirect_uri"], "http://127.0.0.1:10000/google-callback")

    def test_google_callback_state_mismatch(self):
        """Verify mismatched state is rejected."""
        with self.client:
            # Set session state
            with self.client.session_transaction() as sess:
                sess["oauth_state"] = "correct_session_state"
                sess["oauth_redirect_uri"] = "http://127.0.0.1:10000/google-callback"

            # Hit callback with mismatched state
            resp = self.client.get("/google-callback?code=test_code&state=wrong_state", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            # Should flash state error message and redirect to login
            self.assertIn(b"Invalid or expired OAuth state session", resp.data)

    def test_google_callback_single_use_state(self):
        """Verify state is popped and cannot be reused for a second request."""
        with self.client:
            with self.client.session_transaction() as sess:
                sess["oauth_state"] = "valid_state_123"
                sess["oauth_redirect_uri"] = "http://127.0.0.1:10000/google-callback"

            # First attempt with mock failure
            with patch("requests.post") as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 401
                mock_resp.json.return_value = {"error": "invalid_client", "error_description": "The provided client secret is invalid."}
                mock_resp.text = json.dumps(mock_resp.json.return_value)
                mock_post.return_value = mock_resp

                resp = self.client.get("/google-callback?code=code_1&state=valid_state_123", follow_redirects=True)
                self.assertIn(b"Failed to exchange authentication token with Google", resp.data)

            # Second attempt with the same state should fail state check because it was popped
            resp2 = self.client.get("/google-callback?code=code_1&state=valid_state_123", follow_redirects=True)
            self.assertIn(b"Invalid or expired OAuth state session", resp2.data)

    def test_token_exchange_failure_logging_and_flash(self):
        """Verify non-200 Google token response logs errors cleanly and flashes generic user message."""
        with self.client:
            with self.client.session_transaction() as sess:
                sess["oauth_state"] = "test_state_401"
                sess["oauth_redirect_uri"] = "http://127.0.0.1:10000/google-callback"

            with patch("requests.post") as mock_post, patch.object(app.logger, "error") as mock_logger:
                mock_resp = MagicMock()
                mock_resp.status_code = 401
                mock_resp.json.return_value = {
                    "error": "invalid_client",
                    "error_description": "The provided client secret is invalid."
                }
                mock_resp.text = json.dumps(mock_resp.json.return_value)
                mock_post.return_value = mock_resp

                resp = self.client.get("/google-callback?code=auth_code_xyz&state=test_state_401", follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                # Verify user-facing flash message
                self.assertIn(b"Failed to exchange authentication token with Google. Please use email/password login.", resp.data)
                # Verify logger logged the status code, error, and description
                mock_logger.assert_called()
                log_calls = [call[0][0] for call in mock_logger.call_args_list]
                token_exchange_log = next((msg for msg in log_calls if "Token exchange failed" in msg), None)
                self.assertIsNotNone(token_exchange_log)
                self.assertIn("Status 401", token_exchange_log)
                self.assertIn("invalid_client", token_exchange_log)
                self.assertIn("The provided client secret is invalid.", token_exchange_log)

    def test_successful_google_oauth_flow(self):
        """Verify successful token exchange creates/logs in student and sets session."""
        with self.client:
            with self.client.session_transaction() as sess:
                sess["oauth_state"] = "valid_flow_state"
                sess["oauth_redirect_uri"] = "http://127.0.0.1:10000/google-callback"

            mock_token_resp = MagicMock()
            mock_token_resp.status_code = 200
            mock_token_resp.json.return_value = {"access_token": "mock_access_token_12345"}

            mock_userinfo_resp = MagicMock()
            mock_userinfo_resp.status_code = 200
            mock_userinfo_resp.json.return_value = {
                "sub": "google_sub_99999",
                "email": "oauth_test_user@example.com",
                "email_verified": True,
                "name": "OAuth Test Student"
            }

            with patch("requests.post", return_value=mock_token_resp), \
                 patch("requests.get", return_value=mock_userinfo_resp):
                resp = self.client.get("/google-callback?code=valid_code_999&state=valid_flow_state", follow_redirects=False)
                # Should redirect to dashboard
                self.assertEqual(resp.status_code, 302)
                self.assertIn("/dashboard", resp.location)

            # Verify session was populated
            with self.client.session_transaction() as sess:
                self.assertEqual(sess["user_email"], "oauth_test_user@example.com")
                self.assertEqual(sess["user_name"], "OAuth Test Student")
                self.assertEqual(sess["user_role"], "student")
                self.assertIsNotNone(sess["user_id"])

    def test_standard_email_password_auth_intact(self):
        """Verify normal email and password login flow is completely intact."""
        # Create a test student in DB
        hashed = hash_password("testpassword123")
        conn = get_db()
        conn.execute(
            """
            INSERT OR REPLACE INTO users (name, email, password, role, approved, target_role, created_at)
            VALUES ('Email User', 'oauth_test_user@example.com', ?, 'student', 1, 'Software Developer', '2026-01-01 00:00:00')
            """,
            (hashed,)
        )
        conn.commit()
        conn.close()

        resp = self.client.post("/login", data={
            "email": "oauth_test_user@example.com",
            "password": "testpassword123"
        }, follow_redirects=False)

        self.assertEqual(resp.status_code, 302)
        self.assertIn("/dashboard", resp.location)


if __name__ == "__main__":
    unittest.main()
