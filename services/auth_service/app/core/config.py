from pydantic import Field, computed_field
from pydantic_settings import BaseSettings
import base64

class Settings(BaseSettings):
    ALLOW_ORIGINS: str = "*"
    AUTH_DATABASE_URL: str
    REDIS_HOST: str
    REDIS_PORT: int

    JWT_PRIVATE_KEY: str
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    ADMIN_COUNT: int
    ADMIN_NAME: str
    ADMIN_PASSWORD: str
    ADMIN_EMAIL: str
    ADMIN_USERNAME: str

    OTEL_EXPORTER_OTLP_ENDPOINT: str

    CIRCUIT_BREAKER_TIMEOUT_DURATION: int = 30
    CIRCUIT_BREAKER_FAIL_MAX: int = 5

    PAYMENT_BASE_URL: str
    SERVICE_SHARED_KEY: str
    
    class Config:
        env_file = ".env"

settings = Settings()