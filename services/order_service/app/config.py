from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., env=["ORDER_DATABASE_URL", "DATABASE_URL"])

    KAFKA_CLIENT_ID: str
    KAFKA_BOOTSTRAP_SERVERS: str

    AUTH_BASE_URL: str = "http://auth_service:9002"
    INVENTORY_BASE_URL: str = "http://inventory_service:9004"

    SECRET_KEY: str
    SERVICE_SHARED_KEY: str

    REDIS_HOST: str
    REDIS_PORT: int = 6379

    CIRCUIT_BREAKER_TIMEOUT_DURATION: int = 30
    CIRCUIT_BREAKER_FAIL_MAX: int = 5

    class Config:
        env_file = ".env"

settings = Settings()