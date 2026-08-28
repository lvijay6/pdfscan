import unittest
import uuid
import pyotp
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import Base, engine

class TestAuthAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    def test_signup_and_login(self):
        uid = str(uuid.uuid4())[:8]
        email = f"jane_signup_{uid}@example.com"
        res = self.client.post("/api/v1/auth/signup", json={
            "name": "Jane Doe",
            "email": email,
            "password": "Password123!"
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.json())

        res_login = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "Password123!"
        })
        self.assertEqual(res_login.status_code, 200)
        self.assertIn("access_token", res_login.json())

    def test_mfa_flow(self):
        uid = str(uuid.uuid4())[:8]
        email = f"mfa_user_{uid}@example.com"
        self.client.post("/api/v1/auth/signup", json={
            "name": "MFA User",
            "email": email,
            "password": "Password123!"
        })
        res_setup = self.client.post(f"/api/v1/auth/mfa/setup?email={email}")
        self.assertEqual(res_setup.status_code, 200)
        secret = res_setup.json()["secret"]

        # Generate valid TOTP token using pyotp
        totp = pyotp.TOTP(secret)
        code = totp.now()

        res_enable = self.client.post("/api/v1/auth/mfa/enable", json={
            "email": email,
            "code": code
        })
        self.assertEqual(res_enable.status_code, 200)

        res_verify = self.client.post("/api/v1/auth/mfa/verify", json={
            "email": email,
            "code": code
        })
        self.assertEqual(res_verify.status_code, 200)
        self.assertIn("access_token", res_verify.json())

    def test_social_login(self):
        uid = str(uuid.uuid4())[:8]
        email = f"social_{uid}@example.com"
        res = self.client.post("/api/v1/auth/social-login", json={
            "provider": "google",
            "token": "valid_google_oauth_token_12345",
            "email": email,
            "name": "Social User"
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.json())

if __name__ == "__main__":
    unittest.main()
