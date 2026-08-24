from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LLM_API_KEY: str = ""
    TEMPERATURE: float = 0.1
    
    REDIS_HOST: str
    REDIS_PORT: int

    SECRET_KEY: str

    OTEL_EXPORTER_OTLP_ENDPOINT: str

    AI_DATABASE_URL: str

    EMBEDDING_MODEL: str = "Qwen/Qwen3-Embedding-0.6B"

    CHUNK_OVERLAP: int = 50
    CHUNK_SIZE: int = 500

    AUTH_BASE_URL: str = "http://auth_service:9001"
    
    class Config:
        env_file = ".env"

settings = Settings()