"""Конфигурация приложения, читается из .env (см. .env.example)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DB_URL: str = "sqlite:///./app.db"

    JWT_SECRET: str = "dev-secret-change-me"
    JWT_EXPIRE_MIN: int = 60
    JWT_ALGORITHM: str = "HS256"

    OLLAMA_URL: str = "http://localhost:11434"
    MODEL_NAME: str = "qwen3:8b"
    # Таймаут обращения к Ollama. Модель на CPU отвечает за десятки секунд
    # (8B заметно медленнее 1.5B), а первый запрос после перезапуска сервиса
    # подгружает модель в память — ещё дольше.
    OLLAMA_TIMEOUT_SEC: float = 300.0
    # У qwen3 есть режим «размышления»: модель сначала думает в поле `thinking`,
    # а ответ пишет в `content`. Thinking полезен для разбора сложных фраз,
    # но заметно замедляет ответ — поэтому его можно выключить.
    OLLAMA_THINK: bool = False

    FRONTEND_ORIGIN: str = "http://localhost:5173"


settings = Settings()
