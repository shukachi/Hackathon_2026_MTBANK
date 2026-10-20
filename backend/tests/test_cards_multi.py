"""Тесты нескольких карт: выпуск от родителя, пополнение баланса, баланс в реквизитах."""
from app.models.card import Card


def _register_parent(client, login: str = "parent@test.by") -> int:
    resp = client.post(
        "/auth/register",
        json={"login": login, "password": "Password1!", "full_name": "Parent Test"},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def _onboard_child(client, name: str = "Child Test", age: int = 10) -> dict:
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


def test_child_can_have_multiple_cards(client):
    _register_parent(client)
    child = _onboard_child(client)

    resp = client.post(
        "/cards",
        json={"child_id": child["user_id"], "balance": 50.0},
    )
    assert resp.status_code == 200
    new_card = resp.json()
    assert new_card["user_id"] == child["user_id"]
    assert new_card["balance"] == 50.0
    assert new_card["id"] != child["card_id"]

    # Родитель видит обе карты ребёнка.
    resp = client.get(f"/cards?user_id={child['user_id']}")
    assert resp.status_code == 200
    cards = resp.json()
    assert len(cards) == 2
    assert {c["id"] for c in cards} == {child["card_id"], new_card["id"]}
    assert all(c["user_id"] == child["user_id"] for c in cards)

    # И сам ребёнок видит свои карты.
    client.post(
        "/auth/login",
        json={"login": child["login"], "password": child["password"]},
    )
    resp = client.get("/cards")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_issued_card_has_own_number(client):
    _register_parent(client)
    child = _onboard_child(client)

    resp = client.post("/cards", json={"child_id": child["user_id"]})
    assert resp.status_code == 200
    new_number = resp.json()["masked_number"]
    assert new_number != "**** **** **** 1001"


def test_parent_cannot_issue_card_for_other_family(client):
    _register_parent(client, "parentA@test.by")
    child_a = _onboard_child(client, "Child A")

    client.post("/auth/logout")
    _register_parent(client, "parentB@test.by")

    resp = client.post("/cards", json={"child_id": child_a["user_id"]})
    assert resp.status_code == 403


def test_child_cannot_issue_cards(client):
    _register_parent(client)
    child = _onboard_child(client)

    client.post(
        "/auth/login",
        json={"login": child["login"], "password": child["password"]},
    )
    resp = client.post("/cards", json={"child_id": child["user_id"]})
    assert resp.status_code == 403


def test_parent_can_top_up_child_card(client):
    _register_parent(client)
    child = _onboard_child(client)

    resp = client.post(f"/cards/{child['card_id']}/top-up", json={"amount": 40.0})
    assert resp.status_code == 200
    assert resp.json()["balance"] == 40.0

    # Повторное пополнение суммируется.
    resp = client.post(f"/cards/{child['card_id']}/top-up", json={"amount": 10.0})
    assert resp.json()["balance"] == 50.0


def test_parent_cannot_top_up_other_family_card(client):
    _register_parent(client, "parentA@test.by")
    child_a = _onboard_child(client, "Child A")

    client.post("/auth/logout")
    _register_parent(client, "parentB@test.by")

    resp = client.post(f"/cards/{child_a['card_id']}/top-up", json={"amount": 40.0})
    assert resp.status_code == 403


def test_balance_visible_in_card_out(client):
    """Реквизиты карты содержат баланс."""
    _register_parent(client)
    child = _onboard_child(client)

    resp = client.get(f"/cards/{child['card_id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert "balance" in body
    assert body["balance"] == 0.0


def test_balance_decreases_after_purchase(client):
    _register_parent(client)
    child = _onboard_child(client)

    client.post(f"/cards/{child['card_id']}/top-up", json={"amount": 100.0})

    resp = client.post(
        "/transactions/simulate",
        json={"card_id": child["card_id"], "amount": 30.0, "category": "toys", "merchant": "Игрушки.by"},
    )
    assert resp.status_code == 200
    assert resp.json()["card"]["balance"] == 70.0

    # И в GET /cards тоже актуальный баланс.
    assert client.get(f"/cards/{child['card_id']}").json()["balance"] == 70.0


def test_blocked_transaction_does_not_spend_balance(client):
    _register_parent(client)
    child = _onboard_child(client)

    client.post(f"/cards/{child['card_id']}/top-up", json={"amount": 100.0})
    client.put(
        "/limits",
        json={"child_id": child["user_id"], "category": "sweets", "amount": 5, "period": "week"},
    )

    resp = client.post(
        "/transactions/simulate",
        json={"card_id": child["card_id"], "amount": 50.0, "category": "sweets", "merchant": "Кондитерская"},
    )
    assert resp.status_code == 200
    assert resp.json()["blocked"] is True
    assert resp.json()["card"]["balance"] == 100.0


def test_each_card_has_own_balance(client):
    _register_parent(client)
    child = _onboard_child(client)

    second = client.post("/cards", json={"child_id": child["user_id"], "balance": 25.0}).json()
    client.post(f"/cards/{child['card_id']}/top-up", json={"amount": 100.0})

    assert client.get(f"/cards/{child['card_id']}").json()["balance"] == 100.0
    assert client.get(f"/cards/{second['id']}").json()["balance"] == 25.0


def test_family_children_returns_all_cards(client):
    _register_parent(client)
    child = _onboard_child(client)
    client.post("/cards", json={"child_id": child["user_id"], "balance": 15.0})

    resp = client.get("/family/children")
    assert resp.status_code == 200
    family = resp.json()
    assert len(family) == 1
    assert len(family[0]["cards"]) == 2
    # Основная карта — первая выпущенная.
    assert family[0]["card"]["id"] == child["card_id"]


def test_cards_are_persisted_for_child(client, db):
    _register_parent(client)
    child = _onboard_child(client)
    client.post("/cards", json={"child_id": child["user_id"]})

    cards = db.query(Card).filter(Card.user_id == child["user_id"]).all()
    assert len(cards) == 2
