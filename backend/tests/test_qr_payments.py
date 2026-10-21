"""Тесты временных QR-платежей (вкладка Step).

Проверяем сквозной сценарий: ребёнок/подросток выбирает категорию и карту,
генерирует одноразовый QR-код, терминал сканирует его — деньги списываются
с выбранной карты, создаётся транзакция и начисляется кешбэк орешками.
"""


def _register_parent(client, login: str = "parent@test.by") -> int:
    resp = client.post(
        "/auth/register",
        json={"login": login, "password": "Password1!", "full_name": "Parent Test"},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def _onboard_child(client, name: str = "Child Test", age: int = 10) -> dict:
    """Создаёт ребёнка (или подростка) и возвращает его данные и карту."""
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


def _login_as_child(client, child: dict) -> None:
    resp = client.post(
        "/auth/login",
        json={"login": child["login"], "password": child["password"]},
    )
    assert resp.status_code == 200


def _generate(client, card_id, category: str = "toys", amount=None, ttl: int = 10) -> dict:
    body = {"category": category, "card_id": card_id, "ttl_minutes": ttl}
    if amount is not None:
        body["amount"] = amount
    resp = client.post("/qr/generate", json=body)
    assert resp.status_code == 200, resp.text
    return resp.json()


# --- Кто может генерировать QR ---

def test_child_can_generate_qr(client):
    _register_parent(client)
    child = _onboard_child(client)
    _login_as_child(client, child)

    res = _generate(client, child["card_id"], category="toys", amount=15.0)
    assert res["token"]
    assert res["payload"] == f"moby://pay/{res['token']}"
    assert res["ttl_minutes"] == 10
    assert res["expires_at"]


def test_teen_can_generate_qr(client):
    _register_parent(client)
    teen = _onboard_child(client, name="Teen Test", age=15)
    _login_as_child(client, teen)

    res = _generate(client, teen["card_id"], category="games", amount=5.0)
    assert res["token"]


def test_parent_cannot_generate_qr(client):
    """QR для оплаты — только ребёнку и подростку, родителю нельзя."""
    parent_id = _register_parent(client)
    child = _onboard_child(client)

    # Родитель остаётся залогинен (он и так логинился при регистрации).
    resp = client.post(
        "/qr/generate",
        json={"category": "toys", "card_id": child["card_id"], "ttl_minutes": 10},
    )
    #generate-endpoint: only child/teen — parent gets 403 (access control), not 400 (validation).
    assert resp.status_code == 403
    assert "ребёнку" in resp.json()["detail"]


def test_cannot_generate_qr_for_foreign_card(client):
    """Нельзя выбрать чужую карту — списание идёт только со своей."""
    _register_parent(client)
    child = _onboard_child(client)
    other = _onboard_child(client, name="Other Child")
    _login_as_child(client, child)

    resp = client.post(
        "/qr/generate",
        json={"category": "toys", "card_id": other["card_id"], "ttl_minutes": 10},
    )
    assert resp.status_code == 403


def test_category_and_card_are_required(client):
    """Категория и карта — обязательные поля: без них QR не создаётся."""
    _register_parent(client)
    child = _onboard_child(client)
    _login_as_child(client, child)

    no_category = client.post("/qr/generate", json={"card_id": child["card_id"]})
    assert no_category.status_code == 422

    no_card = client.post("/qr/generate", json={"category": "toys"})
    assert no_card.status_code == 422

    bad_category = client.post(
        "/qr/generate",
        json={"category": "crypto", "card_id": child["card_id"]},
    )
    assert bad_category.status_code == 422


# --- Оплата по QR ---

def test_pay_qr_debits_card_and_creates_transaction(client):
    _register_parent(client)
    child = _onboard_child(client)
    # Родитель кладёт карманные деньги на карту.
    assert client.post(f"/cards/{child['card_id']}/top-up", json={"amount": 100.0}).status_code == 200
    _login_as_child(client, child)

    qr = _generate(client, child["card_id"], category="toys", amount=15.0)
    resp = client.post(f"/qr/{qr['token']}/pay", json={"merchant": "Студия танцев"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["debited_amount"] == 15.0
    assert body["card_balance_left"] == 85.0
    assert body["qr_payment"]["status"] == "paid"
    assert body["qr_payment"]["merchant"] == "Студия танцев"

    # Транзакция появилась в истории операций.
    tx = client.get(f"/transactions?user_id={child['user_id']}")
    assert tx.status_code == 200
    assert any(t["id"] == body["transaction_id"] for t in tx.json())


def test_pay_qr_awards_cashback_nuts(client):
    _register_parent(client)
    child = _onboard_child(client)
    client.post(f"/cards/{child['card_id']}/top-up", json={"amount": 100.0})
    _login_as_child(client, child)

    qr = _generate(client, child["card_id"], category="toys", amount=20.0)
    resp = client.post(f"/qr/{qr['token']}/pay", json={})
    assert resp.status_code == 200

    # 5% от 20 BYN = 1 BYN = 10 орешков.
    loyalty = client.get(f"/loyalty/{child['user_id']}")
    assert loyalty.json()["points"] == 10


def test_pay_qr_is_one_time_only(client):
    """Один QR — одна оплата. Второе сканирование отклоняется."""
    _register_parent(client)
    child = _onboard_child(client)
    client.post(f"/cards/{child['card_id']}/top-up", json={"amount": 100.0})
    _login_as_child(client, child)

    qr = _generate(client, child["card_id"], category="toys", amount=10.0)
    assert client.post(f"/qr/{qr['token']}/pay", json={}).status_code == 200

    second = client.post(f"/qr/{qr['token']}/pay", json={})
    assert second.status_code == 400
    assert "уже использован" in second.json()["detail"].lower()


def test_pay_qr_without_amount_fails(client):
    """Суммы нет ни в коде, ни в запросе — оплата не проходит."""
    _register_parent(client)
    child = _onboard_child(client)
    _login_as_child(client, child)

    qr = _generate(client, child["card_id"], category="toys")
    resp = client.post(f"/qr/{qr['token']}/pay", json={})
    assert resp.status_code == 400
    assert "сумма" in resp.json()["detail"].lower()


def test_zero_amount_rejected_consistently(client):
    """Нулевая сумма отклоняется одинаково и при генерации, и при оплате."""
    _register_parent(client)
    child = _onboard_child(client)
    _login_as_child(client, child)

    # Генерация с нулевой суммой — 422 (валидация), а не «код без суммы».
    gen = client.post(
        "/qr/generate",
        json={"category": "toys", "card_id": child["card_id"], "amount": 0.0},
    )
    assert gen.status_code == 422

    # Оплата с нулевой суммой — тоже 422.
    qr = _generate(client, child["card_id"], category="toys", amount=10.0)
    pay = client.post(f"/qr/{qr['token']}/pay", json={"amount": 0})
    assert pay.status_code == 422


def test_pay_qr_amount_from_terminal(client):
    """Сумму может прислать терминал в момент сканирования."""
    _register_parent(client)
    child = _onboard_child(client)
    client.post(f"/cards/{child['card_id']}/top-up", json={"amount": 100.0})
    _login_as_child(client, child)

    qr = _generate(client, child["card_id"], category="food")
    resp = client.post(f"/qr/{qr['token']}/pay", json={"amount": 12.5, "merchant": "Магазин"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["debited_amount"] == 12.5
    assert body["card_balance_left"] == 87.5


def test_expired_qr_cannot_be_paid(client):
    """Истёкший код оплатить нельзя — он помечается истёкшим."""
    _register_parent(client)
    child = _onboard_child(client)
    client.post(f"/cards/{child['card_id']}/top-up", json={"amount": 100.0})
    _login_as_child(client, child)

    qr = _generate(client, child["card_id"], category="toys", amount=10.0, ttl=1)

    # Отматываем время назад на 2 минуты — код «состарился».
    from datetime import datetime, timedelta, timezone

    from app.db import get_db  # noqa: F401  (для контекста импорта)
    from app.models.qr_payment import QrPayment

    from tests.conftest import TestingSessionLocal

    session = TestingSessionLocal()
    try:
        row = session.query(QrPayment).filter(QrPayment.token == qr["token"]).one()
        row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=2)
        session.commit()
    finally:
        session.close()

    resp = client.post(f"/qr/{qr['token']}/pay", json={})
    assert resp.status_code == 400
    assert "истёк" in resp.json()["detail"].lower()

    # В списке он числится истёкшим.
    mine = client.get("/qr/my")
    assert mine.status_code == 200
    statuses = {q["token"]: q["status"] for q in mine.json()}
    assert statuses[qr["token"]] == "expired"


def test_cancel_qr(client):
    _register_parent(client)
    child = _onboard_child(client)
    client.post(f"/cards/{child['card_id']}/top-up", json={"amount": 100.0})
    _login_as_child(client, child)

    qr = _generate(client, child["card_id"], category="toys", amount=10.0)
    resp = client.post(f"/qr/{qr['token']}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"

    # Отменённый код оплатить нельзя.
    pay = client.post(f"/qr/{qr['token']}/pay", json={})
    assert pay.status_code == 400
    assert "отмен" in pay.json()["detail"].lower()


def test_cancel_already_paid_qr_fails(client):
    _register_parent(client)
    child = _onboard_child(client)
    client.post(f"/cards/{child['card_id']}/top-up", json={"amount": 100.0})
    _login_as_child(client, child)

    qr = _generate(client, child["card_id"], category="toys", amount=10.0)
    assert client.post(f"/qr/{qr['token']}/pay", json={}).status_code == 200

    cancel = client.post(f"/qr/{qr['token']}/cancel")
    assert cancel.status_code == 400


# --- Разграничение доступа ---

def test_other_child_cannot_pay_my_qr(client):
    """Чужой QR оплатить и отменить нельзя."""
    _register_parent(client)
    child = _onboard_child(client)
    other = _onboard_child(client, name="Other Child")
    _login_as_child(client, child)

    qr = _generate(client, child["card_id"], category="toys", amount=10.0)

    _login_as_child(client, other)
    assert client.post(f"/qr/{qr['token']}/pay", json={}).status_code == 403
    assert client.post(f"/qr/{qr['token']}/cancel").status_code == 403
    # И сам QR другого ребёнка в списке не светится.
    mine = client.get("/qr/my")
    assert all(q["token"] != qr["token"] for q in mine.json())


def test_parent_cannot_pay_child_qr(client):
    """Родитель видит QR ребёнка, но оплатить его не может — платит терминал от имени ребёнка."""
    _register_parent(client)
    child = _onboard_child(client)
    client.post(f"/cards/{child['card_id']}/top-up", json={"amount": 100.0})
    _login_as_child(client, child)
    qr = _generate(client, child["card_id"], category="toys", amount=10.0)

    # Родитель логинится обратно.
    client.post("/auth/login", json={"login": "parent@test.by", "password": "Password1!"})
    assert client.post(f"/qr/{qr['token']}/pay", json={}).status_code == 403
    # Но посмотреть может (родитель видит QR своего ребёнка).
    assert client.get(f"/qr/{qr['token']}").status_code == 200


def test_qr_list_contains_generated_codes(client):
    _register_parent(client)
    child = _onboard_child(client)
    _login_as_child(client, child)

    qr = _generate(client, child["card_id"], category="toys", amount=10.0)
    mine = client.get("/qr/my")
    assert mine.status_code == 200
    rows = mine.json()
    assert len(rows) == 1
    assert rows[0]["token"] == qr["token"]
    assert rows[0]["category"] == "toys"
    assert rows[0]["status"] == "active"
    assert rows[0]["amount"] == 10.0
