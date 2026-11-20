import asyncio
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from cryptography.fernet import Fernet
from fastapi import HTTPException

for name, value in {
    "AUTH_DATABASE_URL": "postgresql+asyncpg://user:password@localhost/auth",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "JWT_PRIVATE_KEY": "test-key",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
    "REFRESH_TOKEN_EXPIRE_DAYS": "7",
    "ADMIN_COUNT": "1",
    "ADMIN_NAME": "Test Admin",
    "ADMIN_PASSWORD": "test-password",
    "ADMIN_EMAIL": "admin@example.test",
    "ADMIN_USERNAME": "test-admin",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
    "PAYMENT_BASE_URL": "http://localhost:9005",
    "SERVICE_SHARED_KEY": "test-key",
}.items():
    os.environ.setdefault(name, value)

from app.core.config import settings
from app.core.utils import hash_password
from app.models.buyer import Buyer
from app.models.mfa_credential import MFACredential
from app.services.mfa import (
    _enrollment_key,
    _totp_code,
    complete_login,
    confirm_enrollment,
    login_after_password,
    start_enrollment,
    verify_totp,
)


class _Result:
    def __init__(self, value, rowcount=None):
        self.value = value
        self.rowcount = rowcount

    def scalar_one_or_none(self):
        return self.value


class _FakeDatabase:
    def __init__(self, user):
        self.user = user
        self.credential = None
        self.committed = False

    async def execute(self, statement):
        if statement.is_update:
            counter = next(iter(statement._values.values())).value
            if (
                self.credential.last_used_counter is None
                or self.credential.last_used_counter < counter
            ):
                self.credential.last_used_counter = counter
                return _Result(None, rowcount=1)
            return _Result(None, rowcount=0)
        entity = statement.column_descriptions[0]["entity"]
        return _Result(
            self.credential if entity is MFACredential else self.user
        )

    def add(self, credential):
        self.credential = credential

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass


class _FakeRedis:
    def __init__(self):
        self.values = {}
        self.attempts = {}
        self.expirations = {}

    def set(self, key, value, ex=None):
        self.values[key] = value
        self.expirations[key] = ex
        return True

    def get(self, key):
        return self.values.get(key)

    def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)

    def eval(self, script, number_of_keys, *keys_and_arguments):
        keys = keys_and_arguments[:number_of_keys]
        if "INCR" in script:
            attempt_key, target_key = keys
            attempts = self.attempts.get(attempt_key, 0) + 1
            self.attempts[attempt_key] = attempts
            if attempts > int(keys_and_arguments[-1]):
                self.values.pop(target_key, None)
                return 0
            return 1
        return self.values.pop(keys[0], None)


class TOTPTests(unittest.TestCase):
    def test_rfc_6238_sha1_vector(self):
        secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        timestamp = datetime.fromtimestamp(59, timezone.utc)

        self.assertEqual(_totp_code(secret, 59 // 30), "287082")
        self.assertTrue(verify_totp(secret, "287082", timestamp))
        self.assertFalse(verify_totp(secret, "287083", timestamp))

    def test_rejects_non_six_digit_codes(self):
        timestamp = datetime.fromtimestamp(59, timezone.utc)

        secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        self.assertFalse(verify_totp(secret, "28708", timestamp))
        self.assertFalse(verify_totp(secret, "٢٨٧٠٨٢", timestamp))


class MFAFlowTests(unittest.TestCase):
    def test_enrollment_then_one_time_mfa_login(self):
        encryption_key = Fernet.generate_key()
        user = Buyer(
            id=uuid4(),
            email="buyer@example.test",
            name="Test Buyer",
            username="mfa-buyer",
            password=hash_password("test-password"),
            shipping_address="1 Test Street",
        )
        database = _FakeDatabase(user)
        redis = _FakeRedis()
        with (
            patch.object(settings, "MFA_ENCRYPTION_KEY", encryption_key.decode()),
            patch("app.services.mfa.redis_client", redis),
            patch(
                "app.services.mfa.get_tokens",
                new=AsyncMock(
                    return_value={
                        "access_token": "access",
                        "refresh_token": "refresh",
                    }
                ),
            ),
        ):
            enrollment = asyncio.run(
                start_enrollment(user, "buyer", "test-password", database)
            )
            key = _enrollment_key("buyer", user.id)
            stored_secret = redis.get(key)
            secret = Fernet(encryption_key).decrypt(stored_secret.encode()).decode()
            self.assertEqual(enrollment["secret"], secret)

            counter = int(datetime.now(timezone.utc).timestamp()) // 30
            code = _totp_code(secret, counter)
            result = asyncio.run(
                confirm_enrollment(user, "buyer", code, database)
            )
            self.assertEqual(result["response"], "MFA enabled")
            self.assertTrue(database.committed)
            self.assertNotEqual(database.credential.encrypted_secret, secret)

            challenge = asyncio.run(login_after_password(user, "buyer", database))
            self.assertTrue(challenge["mfa_required"])
            login_code = _totp_code(secret, counter + 1)
            login = asyncio.run(
                complete_login(
                    challenge["challenge_token"],
                    login_code,
                    "buyer",
                    Buyer,
                    database,
                )
            )
            self.assertEqual(login["tokens"]["access_token"], "access")
            with self.assertRaises(HTTPException):
                asyncio.run(
                    complete_login(
                        challenge["challenge_token"],
                        login_code,
                        "buyer",
                        Buyer,
                        database,
                    )
                )
            replay_challenge = asyncio.run(
                login_after_password(user, "buyer", database)
            )
            with self.assertRaises(HTTPException):
                asyncio.run(
                    complete_login(
                        replay_challenge["challenge_token"],
                        login_code,
                        "buyer",
                        Buyer,
                        database,
                    )
                )


if __name__ == "__main__":
    unittest.main()
