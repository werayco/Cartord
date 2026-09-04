import json
import pathlib
import sys
import unittest
import urllib.error
import urllib.request
from uuid import uuid4

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.core.config import settings


class AuthServiceEndpointTests(unittest.TestCase):
    base_url = "http://localhost:9001"

    @classmethod
    def setUpClass(cls):
        suffix = uuid4().hex[:10]
        cls.password = "Password123!"
        cls.new_password = "NewPassword123!"
        cls.buyer = {
            "email": f"buyer_{suffix}@example.com",
            "name": "Test Buyer",
            "username": f"buyer_{suffix}",
            "password": cls.password,
            "shipping_address": "1 Test Street",
        }
        cls.seller = {
            "email": f"seller_{suffix}@example.com",
            "name": "Test Seller",
            "username": f"seller_{suffix}",
            "password": cls.password,
        }
        cls.admin = {
            "username": settings.ADMIN_USERNAME,
            "password": settings.ADMIN_PASSWORD,
        }

    def request(self, method, path, payload=None, token=None, expected_status=None):
        body = None if payload is None else json.dumps(payload).encode()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request) as response:
                status = response.status
                response_body = response.read()
        except urllib.error.HTTPError as error:
            status = error.code
            response_body = error.read()
        except urllib.error.URLError as error:
            self.fail(f"Unable to reach auth service: {error.reason}")
        try:
            data = json.loads(response_body.decode()) if response_body else {}
        except json.JSONDecodeError:
            data = response_body.decode()
        if expected_status is not None:
            self.assertEqual(status, expected_status, data)
        return data

    @staticmethod
    def access_token(data):
        return data["tokens"]["access_token"]

    @staticmethod
    def refresh_token(data):
        return data["tokens"]["refresh_token"]

    def test_health(self):
        data = self.request("GET", "/api/v1/health", expected_status=200)
        self.assertEqual(data["message"], "Welcome to the Auth Service")
        self.assertIn(data["redis"], {"connected", "disconnected"})

    def test_buyer_endpoints(self):
        registration = self.request(
            "POST", "/api/v1/auth/buyer/register", self.buyer, expected_status=201
        )
        self.assertEqual(registration["response"], "Registration successful")
        buyer_access = self.access_token(registration)
        buyer_refresh = self.refresh_token(registration)

        login = self.request(
            "POST",
            "/api/v1/auth/buyer/login",
            {"username": self.buyer["username"], "password": self.password},
            expected_status=200,
        )
        self.assertEqual(login["response"], "Login successful")

        profile = self.request(
            "GET", "/api/v1/auth/buyer/me", token=buyer_access, expected_status=200
        )
        self.assertEqual(profile["username"], self.buyer["username"])

        refreshed = self.request(
            "POST",
            "/api/v1/auth/buyer/refresh",
            {"refresh_token": buyer_refresh},
            token=buyer_access,
            expected_status=200,
        )
        buyer_access = self.access_token(refreshed)

        updated = self.request(
            "PATCH",
            "/api/v1/auth/buyer/update",
            {"name": "Updated Buyer", "shipping_address": "2 Test Street"},
            token=buyer_access,
            expected_status=200,
        )
        self.assertEqual(updated["response"], "Update successful")

        changed = self.request(
            "POST",
            "/api/v1/auth/buyer/change-password",
            {"old_password": self.password, "new_password": self.new_password},
            token=buyer_access,
            expected_status=200,
        )
        self.assertEqual(changed["response"], "Password changed successfully")

        self.request(
            "POST",
            "/api/v1/auth/buyer/login",
            {"username": self.buyer["username"], "password": self.new_password},
            expected_status=200,
        )

        deleted = self.request(
            "DELETE",
            "/api/v1/auth/buyer/delete",
            {"username": self.buyer["username"], "password": self.new_password},
            token=buyer_access,
            expected_status=200,
        )
        self.assertEqual(deleted["response"], "Account deleted successfully")

    def test_seller_endpoints(self):
        registration = self.request(
            "POST", "/api/v1/auth/seller/register", self.seller, expected_status=201
        )
        self.assertEqual(registration["message"], "Seller registered successfully")

        login = self.request(
            "POST",
            "/api/v1/auth/seller/login",
            {"username": self.seller["username"], "password": self.password},
            expected_status=200,
        )
        seller_access = self.access_token(login)
        seller_refresh = self.refresh_token(login)

        profile = self.request(
            "GET", "/api/v1/auth/seller/me", token=seller_access, expected_status=200
        )
        self.assertEqual(profile["username"], self.seller["username"])
        self.assertEqual(profile["role"], "seller")

        self.request(
            "GET", "/api/v1/auth/seller/sellers", token=seller_access, expected_status=403
        )

        refreshed = self.request(
            "POST",
            "/api/v1/auth/seller/refresh",
            {"refresh_token": seller_refresh},
            token=seller_access,
            expected_status=200,
        )
        seller_access = self.access_token(refreshed)

        changed = self.request(
            "POST",
            "/api/v1/auth/seller/change-password",
            {"old_password": self.password, "new_password": self.new_password},
            token=seller_access,
            expected_status=200,
        )
        self.assertEqual(changed["response"], "Password changed successfully")

        self.request(
            "POST",
            "/api/v1/auth/seller/login",
            {"username": self.seller["username"], "password": self.new_password},
            expected_status=200,
        )

        deleted = self.request(
            "DELETE",
            f"/api/v1/auth/seller/{self.seller['username']}",
            token=seller_access,
            expected_status=400,
        )
        self.assertIn("detail", deleted)

    def test_admin_endpoints(self):
        login = self.request(
            "POST", "/api/v1/auth/seller/login", self.admin, expected_status=200
        )
        admin_access = self.access_token(login)

        sellers = self.request(
            "GET", "/api/v1/auth/seller/sellers", token=admin_access, expected_status=201
        )
        self.assertIsInstance(sellers, list)

        count = self.request(
            "GET", "/api/v1/auth/admin/users/count", token=admin_access, expected_status=200
        )
        self.assertIsInstance(count["total_users"], int)

        statistics = self.request(
            "GET",
            "/api/v1/auth/admin/customers/statistics?period=all",
            token=admin_access,
            expected_status=200,
        )
        self.assertEqual(statistics["period"], "all")
        self.assertIsInstance(statistics["new_customers"], int)


if __name__ == "__main__":
    unittest.main()