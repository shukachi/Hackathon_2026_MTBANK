"""Тонкий клиент к локальной Ollama. На этой машине Ollama не установлена —
функция ОБЯЗАНА graceful-fallback'ить на None при любой ошибке сети/таймаута,
чтобы backend и демо не падали без локального AI-сервиса.
"""
import httpx

from app.core.config import settings

TIMEOUT_SECONDS = 3.0


def chat(system_prompt: str, user_message: str) -> str | None:
    """Пытается получить ответ от Ollama /api/chat. Возвращает None при любой ошибке."""
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            response = client.post(
                f"{settings.OLLAMA_URL}/api/chat",
                json={
                    "model": settings.MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content")
    except (httpx.HTTPError, httpx.TimeoutException, ConnectionError, OSError, ValueError):
        return None
