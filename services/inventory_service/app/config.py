from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    KAFKA_CLIENT_ID: str
    KAFKA_BOOTSTRAP_SERVERS: str
    SERVICE_SHARED_KEY: str
    class Config:
        env_file = ".env"

settings = Settings()