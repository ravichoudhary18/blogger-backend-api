from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status


class AuthTestBase(TestCase):
    """Shared setup for auth tests."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/auth/register/"
        self.login_url = "/api/auth/login/"

        self.valid_register_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "first_name": "New",
            "last_name": "User",
        }


# ──────────────────────────────────────────────
#  REGISTER TESTS
# ──────────────────────────────────────────────
class RegisterTest(AuthTestBase):
    """POST /api/auth/register/"""

    def test_register_success(self):
        resp = self.client.post(
            self.register_url, self.valid_register_data, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_returns_user_data(self):
        resp = self.client.post(
            self.register_url, self.valid_register_data, format="json"
        )
        self.assertEqual(resp.data["username"], "newuser")
        self.assertEqual(resp.data["email"], "newuser@example.com")
        self.assertNotIn("password", resp.data)

    def test_register_password_mismatch(self):
        data = {**self.valid_register_data, "confirm_password": "WrongPass456!"}
        resp = self.client.post(self.register_url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        User.objects.create_user(username="newuser", password="pass123")
        resp = self.client.post(
            self.register_url, self.valid_register_data, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        User.objects.create_user(
            username="existing", email="newuser@example.com", password="pass123"
        )
        resp = self.client.post(
            self.register_url, self.valid_register_data, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_username(self):
        data = {**self.valid_register_data}
        del data["username"]
        resp = self.client.post(self.register_url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_email(self):
        data = {**self.valid_register_data}
        del data["email"]
        resp = self.client.post(self.register_url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_first_name(self):
        data = {**self.valid_register_data}
        del data["first_name"]
        resp = self.client.post(self.register_url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_last_name(self):
        data = {**self.valid_register_data}
        del data["last_name"]
        resp = self.client.post(self.register_url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
#  LOGIN TESTS
# ──────────────────────────────────────────────
class LoginTest(AuthTestBase):
    """POST /api/auth/login/"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
        )

    def test_login_with_username(self):
        resp = self.client.post(
            self.login_url,
            {"username": "testuser", "password": "TestPass123!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_with_email(self):
        resp = self.client.post(
            self.login_url,
            {"username": "test@example.com", "password": "TestPass123!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)

    def test_login_returns_user_info(self):
        resp = self.client.post(
            self.login_url,
            {"username": "testuser", "password": "TestPass123!"},
            format="json",
        )
        self.assertIn("user", resp.data)
        self.assertEqual(resp.data["user"]["username"], "testuser")
        self.assertEqual(resp.data["user"]["email"], "test@example.com")

    def test_login_wrong_password(self):
        resp = self.client.post(
            self.login_url,
            {"username": "testuser", "password": "WrongPass!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        resp = self.client.post(
            self.login_url,
            {"username": "ghost", "password": "TestPass123!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_username(self):
        resp = self.client.post(
            self.login_url,
            {"password": "TestPass123!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_password(self):
        resp = self.client.post(
            self.login_url,
            {"username": "testuser"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_blank_username(self):
        resp = self.client.post(
            self.login_url,
            {"username": "", "password": "TestPass123!"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_blank_password(self):
        resp = self.client.post(
            self.login_url,
            {"username": "testuser", "password": ""},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ──────────────────────────────────────────────
#  TOKEN REFRESH TEST
# ──────────────────────────────────────────────
class TokenRefreshTest(AuthTestBase):
    """POST /api/auth/token/refresh/"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="testuser", password="TestPass123!"
        )
        # Login to get tokens
        resp = self.client.post(
            self.login_url,
            {"username": "testuser", "password": "TestPass123!"},
            format="json",
        )
        self.refresh_token = resp.data["refresh"]

    def test_refresh_token_success(self):
        resp = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": self.refresh_token},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)

    def test_refresh_token_invalid(self):
        resp = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": "invalid.token.here"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
