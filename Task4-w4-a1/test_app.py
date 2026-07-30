import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app import app


class TestAuthApi(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_public_info(self):
        """Verify GET /public/info returns 200 OK without authentication."""
        response = self.client.get("/public/info")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome stranger! This info is public."})

    def test_signup_missing_fields(self):
        """Verify POST /auth/signup returns 400 Bad Request if fields are empty."""
        response = self.client.post("/auth/signup", json={"email": "", "password": ""})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Email and password are required"})

    def test_login_missing_fields(self):
        """Verify POST /auth/login returns 400 Bad Request if fields are empty."""
        response = self.client.post("/auth/login", json={"email": "  ", "password": ""})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Email and password are required"})

    def test_protected_profile_missing_token(self):
        """Verify GET /protected/profile returns 401 Unauthorized when Authorization header is missing."""
        response = self.client.get("/protected/profile")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "Access token required"})

    @patch("httpx.AsyncClient.get")
    def test_protected_profile_invalid_token(self, mock_get):
        """Verify GET /protected/profile returns 401 Unauthorized when token is invalid."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        response = self.client.get("/protected/profile", headers={"Authorization": "Bearer invalid_fake_token"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "Invalid or expired token"})

    @patch("httpx.AsyncClient.post")
    def test_signup_success(self, mock_post):
        """Verify POST /auth/signup returns 201 Created on successful registration."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "user": {
                "id": "usr_12345",
                "email": "newuser@example.com",
                "created_at": "2026-07-30T19:00:00Z"
            }
        }
        mock_post.return_value = mock_resp

        response = self.client.post("/auth/signup", json={"email": "newuser@example.com", "password": "password123"})
        self.assertEqual(response.status_code, 201)
        res_data = response.json()
        self.assertEqual(res_data["message"], "User registered successfully")
        self.assertEqual(res_data["user"]["id"], "usr_12345")

    @patch("httpx.AsyncClient.post")
    def test_login_success(self, mock_post):
        """Verify POST /auth/login returns 200 OK with tokens on valid credentials."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "mock_jwt_access_token_xyz",
            "refresh_token": "mock_jwt_refresh_token_abc",
            "user": {
                "id": "usr_12345",
                "email": "test@example.com"
            }
        }
        mock_post.return_value = mock_resp

        response = self.client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data["access_token"], "mock_jwt_access_token_xyz")
        self.assertEqual(res_data["token_type"], "bearer")

    @patch("httpx.AsyncClient.get")
    def test_protected_profile_valid_token(self, mock_get):
        """Verify GET /protected/profile returns 200 OK with user metadata on valid token."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "usr_12345",
            "email": "test@example.com",
            "created_at": "2026-07-30T19:00:00Z",
            "user_metadata": {"role": "intern"}
        }
        mock_get.return_value = mock_resp

        response = self.client.get("/protected/profile", headers={"Authorization": "Bearer mock_valid_jwt"})
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data["user_id"], "usr_12345")
        self.assertEqual(res_data["email"], "test@example.com")

    @patch("httpx.AsyncClient.get")
    @patch("httpx.AsyncClient.post")
    def test_logout_success(self, mock_post, mock_get):
        """Verify POST /auth/logout returns 204 No Content on valid token."""
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {
            "id": "usr_12345",
            "email": "test@example.com",
            "created_at": "2026-07-30T19:00:00Z",
            "user_metadata": {}
        }
        mock_get.return_value = mock_get_resp

        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 204
        mock_post.return_value = mock_post_resp

        response = self.client.post("/auth/logout", headers={"Authorization": "Bearer mock_valid_jwt"})
        self.assertEqual(response.status_code, 204)


if __name__ == "__main__":
    unittest.main()
