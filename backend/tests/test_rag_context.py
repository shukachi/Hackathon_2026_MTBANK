"""Тесты RAG-контекста и клиента Ollama.

После перехода на `qwen3:8b` модель должна получать в контексте готовые суммы
по категориям — иначе вместо конкретной суммы она отвечает общими словами.
"""

from app.core.config import settings
from app.models.transaction import CategoryEnum
from app.services import ollama_client, rag


def _register_parent(client, login: str = "rag-parent@test.by") -> int:
    resp = client.post(
        "/auth/register",
        json={"login": login, "password": "Password1!", "full_name": "RAG Parent"},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def _onboard_child(client, name: str = "RAG Child", age: int = 10) -> dict:
    resp = client.post(
        "/family/onboarding",
        json={"child_full_name": name, "age": age, "consent_given": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    return {
        "user_id": data["user"]["id"],
        "card_id": data["card_id"],
        "login": data["login"],
        "password": data["temporary_password"],
    }


def test_context_contains_category_totals(db, client):
    """В контексте есть суммы по категориям за 30 дней."""
    _register_parent(client)
    child = _onboard_child(client)

    client.post(f"/cards/{child['card_id']}/top-up", json={"amount": 100.0})
    for amount, category, merchant in (
        (20.0, "toys", "Детский мир"),
        (30.0, "toys", "Игрушки.by"),
        (10.0, "food", "Соседи"),
    ):
        client.post(
            "/transactions/simulate",
            json={
                "card_id": child["card_id"],
                "amount": amount,
                "category": category,
                "merchant": merchant,
            },
        )

    context, categories = rag.build_context(db, child["user_id"], "сколько я потратил на игрушки")

    assert CategoryEnum.toys in categories
    assert "Суммы трат по категориям" in context
    # Сумма по игрушкам сложена из двух покупок.
    assert "toys: 50.00 BYN" in context
    assert "2 покупок" in context
    assert "food: 10.00 BYN" in context


def test_context_excludes_blocked_transactions(db, client):
    """Заблокированная лимитом покупка не попадает в суммы трат."""
    _register_parent(client)
    child = _onboard_child(client)
    client.post(f"/cards/{child['card_id']}/top-up", json={"amount": 100.0})

    # Лимит 5 BYN на сладости — покупка на 50 пройдёт как заблокированная.
    limit_resp = client.put(
        "/limits",
        json={"child_id": child["user_id"], "category": "sweets", "amount": 5.0, "period": "month"},
    )
    assert limit_resp.status_code == 200, limit_resp.text
    client.post(
        "/transactions/simulate",
        json={
            "card_id": child["card_id"],
            "amount": 50.0,
            "category": "sweets",
            "merchant": "Кондитерская",
        },
    )

    context, _ = rag.build_context(db, child["user_id"], "сколько я потратил на сладости")
    # Заблокированная покупка не попала в суммы — категории со счётом 0 нет в сводке.
    assert "sweets" not in context.split("Последние транзакции")[0]
    # Но в списке транзакций она видна со статусом blocked_by_limit.
    assert "blocked_by_limit" in context


def test_ollama_client_passes_think_flag(monkeypatch):
    """Клиент передаёт флаг `think` — иначе у qwen3 в ответ попадёт черновик рассуждения."""
    captured: dict = {}

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"message": {"content": "ответ"}}

    class _FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, url, json=None):
            captured["url"] = url
            captured["payload"] = json
            return _FakeResponse()

    monkeypatch.setattr(ollama_client.httpx, "Client", _FakeClient)
    monkeypatch.setattr(settings, "MODEL_NAME", "qwen3:8b")
    monkeypatch.setattr(settings, "OLLAMA_THINK", False)

    reply = ollama_client.chat("system", "user")

    assert reply == "ответ"
    assert captured["payload"]["model"] == "qwen3:8b"
    assert captured["payload"]["stream"] is False
    # Ключ think присутствует — Ollama без него оставит режим размышления включённым.
    assert "think" in captured["payload"]
    assert captured["payload"]["think"] is False


def test_default_model_is_configured():
    """Модель задаётся конфигом, а не захардкожена в коде."""
    assert settings.MODEL_NAME
    # Таймаут должен покрывать ответ 8B на CPU.
    assert settings.OLLAMA_TIMEOUT_SEC >= 120
