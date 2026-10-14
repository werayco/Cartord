import asyncio
import time
import aiohttp
from app.core.config import settings
from app.core.logging import logger

DELEGATE_PATH = "/internal/v1/token/delegate"
REFRESH_MARGIN_SECONDS = 30 
MAX_CACHE_ENTRIES = 2048

_cache: dict[tuple[str, str], tuple[str, float]] = {}
_locks: dict[tuple[str, str], asyncio.Lock] = {}


class TokenDelegationError(Exception):
    """The auth service could not issue a delegated token."""


def _fresh(entry: tuple[str, float] | None) -> bool:
    return entry is not None and entry[1] - REFRESH_MARGIN_SECONDS > time.monotonic()


def _prune() -> None:
    now = time.monotonic()
    for key in [k for k, (_, exp) in _cache.items() if exp <= now]:
        _cache.pop(key, None)
    while len(_cache) > MAX_CACHE_ENTRIES:
        _cache.pop(next(iter(_cache)))
    for key in [k for k, lock in _locks.items() if k not in _cache and not lock.locked()]:
        _locks.pop(key, None)


def invalidate(user_id: str, scope: str) -> None:
    _cache.pop((str(user_id), scope), None)


async def _mint(user_id: str, scope: str) -> tuple[str, float]:
    url = f"{settings.AUTH_BASE_URL}{DELEGATE_PATH}"
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                url,
                json={"user_id": user_id, "scopes": [scope]},
                headers={"X-Service-Secret": settings.AUTH_DELEGATION_SECRET},
            ) as response:
                if response.status != 200:
                    raise TokenDelegationError(f"auth service returned {response.status}")
                data = await response.json()
        return data["access_token"], float(data["expires_in"])
    except TokenDelegationError:
        raise
    except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, ValueError, TypeError) as e:
        raise TokenDelegationError(f"{type(e).__name__}: {e}") from e

async def get_token(user_id: str, scope: str) -> str:
    key = (str(user_id), scope)
    entry = _cache.get(key)
    if _fresh(entry):
        return entry[0]

    async with _locks.setdefault(key, asyncio.Lock()):
        entry = _cache.get(key)
        if _fresh(entry):
            return entry[0]
        token, expires_in = await _mint(key[0], scope)
        _cache[key] = (token, time.monotonic() + expires_in)
        if len(_cache) > MAX_CACHE_ENTRIES:
            _prune()
        logger.debug(f"minted delegated token for scope={scope}")
        return token
