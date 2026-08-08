from aiobreaker import CircuitBreaker
from app.config import settings

breaker = CircuitBreaker(fail_max=settings.CIRCUIT_BREAKER_FAIL_MAX, timeout_duration=settings.CIRCUIT_BREAKER_TIMEOUT_DURATION)