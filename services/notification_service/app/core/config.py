from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    KAFKA_CLIENT_ID: str
    KAFKA_BOOTSTRAP_SERVERS: str
    SERVICE_SHARED_KEY: str
    
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://otel-collector:4317"
    
    EMAIL_PROVIDER: str = "mailpit"
    RESEND_API_KEY: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    MAILPIT_HOST: str = "mailpit"
    MAILPIT_PORT: int = 1025
    EMAIL_FROM: str = "noreply@example.com"

    class Config:
        env_file = ".env"

settings = Settings()