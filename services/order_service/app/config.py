from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    KAFKA_CLIENT_ID: str
    KAFKA_BOOTSTRAP_SERVERS: str
    AUTH_BASE_URL: str = "http://auth_service:9002"
    class Config:
        env_file = ".env"

settings = Settings()