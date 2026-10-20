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
    # Таймаут обращения к Ollama. Модель qwen2.5:1.5b на CPU отвечает за 2-5 секунд,
    # но первый запрос после перезапуска сервиса подгружает модель в память — дольше.
    OLLAMA_TIMEOUT_SEC: float = 60.0

    FRONTEND_ORIGIN: str = "http://localhost:5173"


settings = Settings()
