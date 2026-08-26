"""
Environment configuration for VaultAPI.

Uses pydantic-settings (Pydantic v2 companion package) to load and validate
environment variables from a `.env` file at project root.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "VaultAPI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./vault.db"

    # --- JWT / Security ---
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- File Uploads ---
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_CONTENT_TYPES: str = "image/jpeg,image/png,image/gif,application/pdf"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_content_types_list(self) -> list[str]:
        return [c.strip() for c in self.ALLOWED_CONTENT_TYPES.split(",") if c.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (avoids re-parsing .env on every import)."""
    return Settings()


settings = get_settings()
