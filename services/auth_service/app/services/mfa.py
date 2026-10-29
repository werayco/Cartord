import base64
import binascii
import hashlib
import hmac
import secrets
import struct
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlencode
from uuid import UUID
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.utils import get_tokens, verify_password
from app.db.redis_client import redis_client
from app.models.mfa_credential import MFACredential

MFA_ISSUER = "Cartord"
MFA_CODE_DIGITS = 6
MFA_PERIOD_SECONDS = 30
MFA_CHALLENGE_TTL_SECONDS = 300
MFA_ENROLLMENT_TTL_SECONDS = 600
MFA_MAX_CODE_ATTEMPTS = 5

_RECORD_ATTEMPT_SCRIPT = """
local attempts = redis.call('INCR', KEYS[1])
if attempts == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
if attempts > tonumber(ARGV[2]) then
    redis.call('DEL', KEYS[2])
    return 0
end
return 1
"""

def _fernet() -> Fernet:
    key = settings.MFA_ENCRYPTION_KEY
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MFA is not configured",
        )
    try:
        return Fernet(key.encode("ascii"))
    except (UnicodeEncodeError, ValueError, binascii.Error) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MFA encryption key is invalid",
        ) from error

def _decrypt_secret(encrypted_secret: str) -> str:
    try:
        return _fernet().decrypt(encrypted_secret.encode("ascii")).decode("ascii")
    except InvalidToken as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stored MFA secret cannot be decrypted; check MFA_ENCRYPTION_KEY",
        ) from error

def _new_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")

def _totp_code(secret: str, counter: int) -> str:
    padded_secret = secret + "=" * (-len(secret) % 8)
    key = base64.b32decode(padded_secret, casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{value % 10**MFA_CODE_DIGITS:0{MFA_CODE_DIGITS}d}"

def matching_totp_counter(
    secret: str, code: str, at: datetime | None = None
) -> int | None:
    if len(code) != MFA_CODE_DIGITS or not code.isascii() or not code.isdigit():
        return None

    timestamp = at or datetime.now(timezone.utc)
    counter = int(timestamp.timestamp()) // MFA_PERIOD_SECONDS
    for offset in (0, -1, 1):
        matching_counter = counter + offset
        if hmac.compare_digest(_totp_code(secret, matching_counter), code):
            return matching_counter
    return None

def verify_totp(secret: str, code: str, at: datetime | None = None) -> bool:
    return matching_totp_counter(secret, code, at) is not None


def _enrollment_key(account_type: str, user_id: UUID) -> str:
    return f"mfa:enrollment:{account_type}:{user_id}"


def _challenge_key(challenge_id: str) -> str:
    return f"mfa:challenge:{challenge_id}"

def _attempt_key(key: str) -> str:
    return f"{key}:attempts"

def _allow_code_attempt(
    attempt_key: str, target_key: str, ttl_seconds: int
) -> bool:
    return bool(
        redis_client.eval(
            _RECORD_ATTEMPT_SCRIPT,
            2,
            _attempt_key(attempt_key),
            target_key,
            ttl_seconds,
            MFA_MAX_CODE_ATTEMPTS,
        )
    )


async def start_enrollment(
    user, account_type: str, password: str, db: AsyncSession
) -> dict[str, str | int]:
    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )
    _fernet()

    result = await db.execute(
        select(MFACredential).where(
            MFACredential.account_type == account_type,
            MFACredential.user_id == user.id,
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="MFA is already enabled",
        )

    secret = _new_totp_secret()
    enrollment_key = _enrollment_key(account_type, user.id)
    redis_client.set(
        enrollment_key,
        _fernet().encrypt(secret.encode("ascii")).decode("ascii"),
        ex=MFA_ENROLLMENT_TTL_SECONDS,
    )
    redis_client.delete(_attempt_key(enrollment_key))
    label = quote(f"{MFA_ISSUER}:{user.username}", safe="")
    uri = (
        f"otpauth://totp/{label}?"
        + urlencode(
            {
                "secret": secret,
                "issuer": MFA_ISSUER,
                "algorithm": "SHA1",
                "digits": MFA_CODE_DIGITS,
                "period": MFA_PERIOD_SECONDS,
            }
        )
    )
    return {
        "secret": secret,
        "otpauth_uri": uri,
        "expires_in": MFA_ENROLLMENT_TTL_SECONDS,
    }


async def confirm_enrollment(
    user, account_type: str, code: str, db: AsyncSession
) -> dict[str, str]:
    result = await db.execute(
        select(MFACredential).where(
            MFACredential.account_type == account_type,
            MFACredential.user_id == user.id,
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="MFA is already enabled",
        )

    enrollment_key = _enrollment_key(account_type, user.id)
    encrypted_secret = redis_client.get(enrollment_key)
    if not encrypted_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enrollment expired; start enrollment again",
        )
    if not _allow_code_attempt(
        enrollment_key, enrollment_key, MFA_ENROLLMENT_TTL_SECONDS
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many invalid codes; start enrollment again",
        )
    secret = _decrypt_secret(encrypted_secret)
    matched_counter = matching_totp_counter(secret, code)
    if matched_counter is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authentication code",
        )

    db.add(
        MFACredential(
            account_type=account_type,
            user_id=user.id,
            encrypted_secret=_fernet().encrypt(secret.encode("ascii")).decode("ascii"),
            last_used_counter=matched_counter,
        )
    )
    await db.commit()
    redis_client.delete(enrollment_key, _attempt_key(enrollment_key))
    return {"response": "MFA enabled"}


async def remove_credential(user_id: UUID, account_type: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(MFACredential).where(
            MFACredential.account_type == account_type,
            MFACredential.user_id == user_id,
        )
    )
    credential = result.scalar_one_or_none()
    if credential is not None:
        await db.delete(credential)
    redis_client.delete(_enrollment_key(account_type, user_id))


async def login_after_password(user, account_type: str, db: AsyncSession) -> dict:
    result = await db.execute(
        select(MFACredential).where(
            MFACredential.account_type == account_type,
            MFACredential.user_id == user.id,
        )
    )
    if result.scalar_one_or_none() is None:
        return {
            "response": "Login successful",
            "tokens": await get_tokens(user),
        }

    challenge_id = secrets.token_urlsafe(24)
    now = datetime.now(timezone.utc)
    challenge_token = jwt.encode(
        {
            "sub": str(user.id),
            "type": "mfa_challenge",
            "account_type": account_type,
            "jti": challenge_id,
            "iat": now,
            "exp": now + timedelta(seconds=MFA_CHALLENGE_TTL_SECONDS),
        },
        settings.JWT_PRIVATE_KEY,
        algorithm="HS256",
    )
    redis_client.set(
        _challenge_key(challenge_id),
        str(user.id),
        ex=MFA_CHALLENGE_TTL_SECONDS,
    )
    return {
        "response": "MFA required",
        "mfa_required": True,
        "challenge_token": challenge_token,
        "expires_in": MFA_CHALLENGE_TTL_SECONDS,
    }


async def complete_login(
    challenge_token: str, code: str, account_type: str, user_model, db: AsyncSession
) -> dict:
    try:
        payload = jwt.decode(
            challenge_token,
            settings.JWT_PRIVATE_KEY,
            algorithms=["HS256"],
        )
        if (
            payload.get("type") != "mfa_challenge"
            or payload.get("account_type") != account_type
        ):
            raise ValueError("Invalid MFA challenge")
        user_id = UUID(payload["sub"])
        challenge_id = payload["jti"]
    except (JWTError, ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA challenge",
        )

    result = await db.execute(select(user_model).where(user_model.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA challenge",
        )

    result = await db.execute(
        select(MFACredential).where(
            MFACredential.account_type == account_type,
            MFACredential.user_id == user.id,
        )
    )
    credential = result.scalar_one_or_none()
    if credential is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA challenge",
        )

    challenge_key = _challenge_key(challenge_id)
    login_attempt_key = f"mfa:login:{account_type}:{user.id}"
    if not _allow_code_attempt(
        login_attempt_key, challenge_key, MFA_CHALLENGE_TTL_SECONDS
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many invalid codes; log in again",
        )
    secret = _decrypt_secret(credential.encrypted_secret)
    matched_counter = matching_totp_counter(secret, code)
    if matched_counter is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication code",
        )

    update_result = await db.execute(
        update(MFACredential)
        .where(
            MFACredential.account_type == account_type,
            MFACredential.user_id == user.id,
            or_(
                MFACredential.last_used_counter.is_(None),
                MFACredential.last_used_counter < matched_counter,
            ),
        )
        .values(last_used_counter=matched_counter)
    )
    if update_result.rowcount != 1:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication code",
        )
    await db.commit()

    consume_challenge_script = """
    local value = redis.call('GET', KEYS[1])
    if value then
        redis.call('DEL', KEYS[1])
    end
    return value
    """
    challenge_user_id = redis_client.eval(consume_challenge_script, 1, challenge_key)
    if not challenge_user_id or not hmac.compare_digest(
        challenge_user_id, str(user.id)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA challenge",
        )
    redis_client.delete(_attempt_key(login_attempt_key))

    return {
        "response": "Login successful",
        "tokens": await get_tokens(user),
    }
