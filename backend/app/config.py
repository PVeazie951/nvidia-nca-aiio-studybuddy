"""Application settings, overridable via environment or .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://studybuddy:studybuddy@127.0.0.1:5432/studybuddy"
    upload_dir: str = "/home/shawn/projects/nvidia-studybuddy/data/uploads"
    host: str = "127.0.0.1"
    port: int = 8077
    cors_origins: str = "http://127.0.0.1:5273,http://localhost:5273"


settings = Settings()
