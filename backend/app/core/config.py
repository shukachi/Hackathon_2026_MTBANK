"""Конфигурация приложения, читается из .env (см. .env.example)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DB_URL: str = "sqlite:///./app.db"

    JWT_SECRET: str = "dev-secret-change-me"
    JWT_EXPIRE_MIN: int = 60
    JWT_ALGORITHM: str = "HS256"

    OLLAMA_URL: str = "http://localhost:11434"
    MODEL_NAME: str = "qwen2.5:1.5b"

    FRONTEND_ORIGIN: str = "http://localhost:5173"


settings = Settings()
