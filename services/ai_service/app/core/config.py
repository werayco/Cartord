from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LLM_API_KEY: str = ""
    TEMPERATURE: float = 0.1

    REDIS_HOST: str
    REDIS_PORT: int

    KAFKA_BOOTSTRAP_SERVERS: str

    SECRET_KEY: str

    OTEL_EXPORTER_OTLP_ENDPOINT: str

    AI_DATABASE_URL: str

    LOCAL_EMBEDDING_MODEL: str = "Qwen/Qwen3-Embedding-0.6B"

    USE_LOCAL_EMBEDDING_MODEL: bool = True

    GEMINI_API_KEY: str = ""
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"

    CHUNK_OVERLAP: int = 50
    CHUNK_SIZE: int = 500

    AUTH_BASE_URL: str = "http://auth_service:9001"
    ORDER_BASE_URL: str = "http://order_service:9004"
    INVENTORY_BASE_URL: str = "http://inventory_service:9002"

    class Config:
        env_file = ".env"

settings = Settings()