from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PAYMENT_DATABASE_URL: str
    SERVICE_SHARED_KEY: str
    OTEL_EXPORTER_OTLP_ENDPOINT: str

    JWT_PRIVATE_KEY: str

    KAFKA_BOOTSTRAP_SERVERS: str

    AUTH_BASE_URL: str = "http://localhost:9001/api/v1"

    CIRCUIT_BREAKER_TIMEOUT_DURATION: int = 30
    CIRCUIT_BREAKER_FAIL_MAX: int = 5

    
    class Config:
        env_file = ".env"

settings = Settings()