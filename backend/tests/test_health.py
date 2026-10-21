from fastapi.testclient import TestClient

from app.core.config import settings
from app.services import ollama_client


def test_health_reports_ollama_status(client: TestClient):
    """`/health` всегда отвечает и сообщает состояние локального AI-слоя."""
    response = client.get("/health")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert "ai_ready" in body

    ollama = body["ollama"]
    # Модель берётся из конфига — тест не должен ломаться при её смене.
    assert ollama["model"] == settings.MODEL_NAME
    assert ollama["url"]
    # Доступность Ollama на тестовой машине не гарантирована — проверяем только форму ответа.
    assert isinstance(ollama["available"], bool)
    assert isinstance(ollama["model_present"], bool)


def test_ollama_status_never_raises(monkeypatch):
    """`ollama_client.status()` не бросает исключение, даже если сервис недоступен."""

    def _boom(*args, **kwargs):
        raise OSError("connection refused")

    monkeypatch.setattr(ollama_client.httpx, "Client", _boom)
    result = ollama_client.status()

    assert result["available"] is False
    assert result["model_present"] is False
