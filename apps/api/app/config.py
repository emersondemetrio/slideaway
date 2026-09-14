from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://slideaway:slideaway@localhost:5432/slideaway"

    jwt_secret: str = "change-me-in-.env"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "slideaway"
    minio_secret_key: str = "slideaway-dev-secret"
    minio_bucket: str = "slideaway-decks"
    minio_secure: bool = False

    default_user_storage_quota_bytes: int = 500 * 1024 * 1024
    max_single_upload_bytes: int = 50 * 1024 * 1024

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
