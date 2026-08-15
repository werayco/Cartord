from datetime import timedelta
from aiobreaker import CircuitBreaker
from app.core.config import settings

breaker = CircuitBreaker(fail_max=settings.CIRCUIT_BREAKER_FAIL_MAX,timeout_duration=timedelta(seconds=settings.CIRCUIT_BREAKER_TIMEOUT_DURATION))