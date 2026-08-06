from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., env=["INVENTORY_DATABASE_URL", "DATABASE_URL"])
    SECRET_KEY: str
    KAFKA_CLIENT_ID: str
    KAFKA_BOOTSTRAP_SERVERS: str
    SERVICE_SHARED_KEY: str

    AUTH_BASE_URL: str = "http://auth_service:9002"

    class Config:
        env_file = ".env"

settings = Settings()