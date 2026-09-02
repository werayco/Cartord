from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    INVENTORY_DATABASE_URL: str
    JWT_PRIVATE_KEY: str
    KAFKA_CLIENT_ID: str
    KAFKA_BOOTSTRAP_SERVERS: str
    SERVICE_SHARED_KEY: str
    LOW_STOCK_THRESHOLD: int = 10

    AUTH_BASE_URL: str = "http://auth_service:9001"

    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://otel-collector:4317"

    class Config:
        env_file = ".env"

settings = Settings()