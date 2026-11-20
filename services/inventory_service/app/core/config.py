from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OTEL_SERVICE_NAME: str = "inventory_service"
    ALLOW_ORIGINS: str = "*"
    SENTRY_DSN: str = ""
    INVENTORY_DATABASE_URL: str
    JWT_PRIVATE_KEY: str
    KAFKA_CLIENT_ID: str
    KAFKA_BOOTSTRAP_SERVERS: str
    SERVICE_SHARED_KEY: str
    LOW_STOCK_THRESHOLD: int = 10

    AUTH_BASE_URL: str = "http://auth_service:9001"

    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://otel-collector:4317"
    MINIO_ENDPOINT: str = ""
    MINIO_PUBLIC_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = "product-images"
    MINIO_CORS_ORIGINS: str = "http://localhost:8081"
    MINIO_UPLOAD_URL_TTL_SECONDS: int = 300
    MINIO_MAX_IMAGE_SIZE_BYTES: int = 5242880
    MINIO_MAX_IMAGES_PER_PRODUCT: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
