from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str

    KAFKA_CLIENT_ID: str
    KAFKA_BOOTSTRAP_SERVERS: str

    AUTH_BASE_URL: str = "http://auth_service:9002"
    INVENTORY_BASE_URL: str = "http://inventory_service:9004"

    SECRET_KEY: str
    SERVICE_SHARED_KEY: str

    REDIS_HOST: str
    REDIS_PORT: int = 6379

    class Config:
        env_file = ".env"

settings = Settings()