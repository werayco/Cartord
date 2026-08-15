from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ELASTICSEARCH_HOST: str
    ELASTICSEARCH_PORT: int

    SECRET_KEY: str

    KAFKA_CLIENT_ID: str
    KAFKA_BOOTSTRAP_SERVERS: str
    
    AUTH_BASE_URL: str = "http://auth_service:9001"

    OTEL_EXPORTER_OTLP_ENDPOINT: str

    class Config:
        env_file = ".env"

settings = Settings()