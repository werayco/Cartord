from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ALLOW_ORIGINS: str = "*"
    ORDER_DATABASE_URL: str

    KAFKA_CLIENT_ID: str
    KAFKA_BOOTSTRAP_SERVERS: str

    AUTH_BASE_URL: str = "http://auth_service:9001"
    INVENTORY_BASE_URL: str = "http://inventory_service:9002/api/v1"

    JWT_PRIVATE_KEY: str
    SERVICE_SHARED_KEY: str

    REDIS_HOST: str
    REDIS_PORT: int = 6379

    CIRCUIT_BREAKER_TIMEOUT_DURATION: int = 30
    CIRCUIT_BREAKER_FAIL_MAX: int = 5

    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://otel-collector:4317"
    
    class Config:
        env_file = ".env"

settings = Settings()