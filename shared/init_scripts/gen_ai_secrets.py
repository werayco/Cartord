import hashlib
import secrets


def generated_values() -> dict[str, str]:
    secret = secrets.token_urlsafe(48)
    secret_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    print(f"AI_AGENT_SECRET={secret}")
    print(f"AI_AGENT_SECRET_HASH={secret_hash}")
    print(f"AUTH_DELEGATION_SECRET={secret}")


generated_values()
