from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str

    REDIS_HOST: str
    REDIS_PORT: int

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    ADMIN_COUNT: int
    ADMIN_NAME: str
    ADMIN_PASSWORD: str
    ADMIN_EMAIL: str
    
    class Config:
        env_file = ".env"

settings = Settings()