"""Тонкий клиент к локальной Ollama.

Ollama и модель — обязательная часть установки (см. scripts/setup-ollama.sh
и раздел «Установка» в README.md). Но backend всё равно не должен падать, если сервис
недоступен: функция ОБЯЗАНА graceful-fallback'ить на None при любой ошибке сети/таймаута,
чтобы демо не падало без локального AI-сервиса.
"""
import httpx

from app.core.config import settings


def _timeout() -> httpx.Timeout:
    return httpx.Timeout(settings.OLLAMA_TIMEOUT_SEC)


def chat(system_prompt: str, user_message: str) -> str | None:
    """Пытается получить ответ от Ollama /api/chat. Возвращает None при любой ошибке.

    У моделей семейства qwen3 есть режим «размышления»: модель сначала пишет
    черновик рассуждения в отдельное поле `thinking`, а готовый ответ — в
    `content`. Флаг `think` управляет этим режимом (`settings.OLLAMA_THINK`).
    Мы читаем только `content` — черновик рассуждения пользователю показывать
    не нужно, а при `think=false` его и не будет.
    """
    try:
        with httpx.Client(timeout=_timeout()) as client:
            response = client.post(
                f"{settings.OLLAMA_URL}/api/chat",
                json={
                    "model": settings.MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "stream": False,
                    # Поддерживается начиная с Ollama 0.9; на старых версиях
                    # лишний параметр просто игнорируется.
                    "think": settings.OLLAMA_THINK,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content")
    except (httpx.HTTPError, httpx.TimeoutException, ConnectionError, OSError, ValueError):
        return None


def status() -> dict:
    """Проверка доступности Ollama и наличия модели.

    Используется в /health, чтобы за один запрос увидеть, готов ли AI-слой.
    Никогда не бросает исключение наружу — только возвращает статус.
    """
    result: dict = {
        "url": settings.OLLAMA_URL,
        "model": settings.MODEL_NAME,
        "available": False,
        "model_present": False,
    }
    try:
        with httpx.Client(timeout=_timeout()) as client:
            response = client.get(f"{settings.OLLAMA_URL}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
    except (httpx.HTTPError, httpx.TimeoutException, ConnectionError, OSError, ValueError):
        return result

    result["available"] = True
    result["model_present"] = any(
        m.get("name") == settings.MODEL_NAME or m.get("model") == settings.MODEL_NAME
        for m in models
    )
    return result
