from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LLM_API_KEY: str
    TEMPERATURE: str
    
    REDIS_HOST: str
    REDIS_PORT: int

    SECRET_KEY: str

    OTEL_EXPORTER_OTLP_ENDPOINT: str

    AI_DATABASE_URL: str
    
    class Config:
        env_file = ".env"

settings = Settings()