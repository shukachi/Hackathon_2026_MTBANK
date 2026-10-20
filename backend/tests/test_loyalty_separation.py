"""Проверка того, что орешки ребёнка и родителя НЕ пересекаются.

ТЗ п.4.3: «Баллы накапливаются отдельно и ребёнком, и родителями».
Ключевой риск — кешбэк должен начисляться владельцу карты, а не тому,
кто совершил операцию: если покупку делает родитель с карты ребёнка,
орешки получает ребёнок, а не родитель.
"""
from app.models.loyalty import LoyaltyAccount, LoyaltyHistory
from app.models.user import RoleEnum


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


def _points_of(client, user_id: int) -> int:
    resp = client.get(f"/loyalty/{user_id}")
    assert resp.status_code == 200
    return resp.json()["points"]


def _points_in_db(db, user_id: int) -> int:
    """Баланс орешков напрямую из БД — когда счёт чужой и API его не отдаёт."""
    acc = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == user_id).one()
    return acc.points


def test_parent_purchase_on_child_card_credits_child_not_parent(client):
    """Ключевой тест: покупку делает родитель, орешки получает ребёнок."""
    parent_id = _register_parent(client)
    child = _onboard_child(client)

    parent_before = _points_of(client, parent_id)
    child_before = _points_of(client, child["user_id"])

    resp = client.post(
        "/transactions/simulate",
        json={"card_id": child["card_id"], "amount": 20.0, "category": "toys", "merchant": "Игрушки.by"},
    )
    assert resp.status_code == 200
    assert resp.json()["cashback_points"] == 10

    assert _points_of(client, child["user_id"]) == child_before + 10
    assert _points_of(client, parent_id) == parent_before  # у родителя не изменилось


def test_child_purchase_credits_child(client, db):
    parent_id = _register_parent(client)
    child = _onboard_child(client)

    client.post(
        "/auth/login",
        json={"login": child["login"], "password": child["password"]},
    )

    # Счёт родителя ребёнку не виден (403) — смотрим его напрямую в БД.
    parent_before = _points_in_db(db, parent_id)
    child_before = _points_of(client, child["user_id"])

    resp = client.post(
        "/transactions/simulate",
        json={"card_id": child["card_id"], "amount": 20.0, "category": "toys", "merchant": "Игрушки.by"},
    )
    assert resp.status_code == 200
    assert resp.json()["cashback_points"] == 10

    assert _points_of(client, child["user_id"]) == child_before + 10
    assert _points_in_db(db, parent_id) == parent_before


def test_each_child_has_own_account(client):
    """Орешки одного ребёнка не попадают на счёт другого."""
    _register_parent(client)
    child_a = _onboard_child(client, "Child A")
    child_b = _onboard_child(client, "Child B")

    resp = client.post(
        "/transactions/simulate",
        json={"card_id": child_a["card_id"], "amount": 20.0, "category": "toys", "merchant": "Игрушки.by"},
    )
    assert resp.status_code == 200

    assert _points_of(client, child_a["user_id"]) == 10
    assert _points_of(client, child_b["user_id"]) == 0


def test_history_entries_belong_to_own_account_only(client):
    """История начислений не смешивается между счетами."""
    parent_id = _register_parent(client)
    child = _onboard_child(client)

    client.post(
        "/transactions/simulate",
        json={"card_id": child["card_id"], "amount": 20.0, "category": "toys", "merchant": "Игрушки.by"},
    )

    child_account = client.get(f"/loyalty/{child['user_id']}").json()
    parent_account = client.get(f"/loyalty/{parent_id}").json()

    child_reasons = [h["reason"] for h in child_account["history"]]
    parent_reasons = [h["reason"] for h in parent_account["history"]]

    assert any("Кешбэк" in r for r in child_reasons)
    assert not any("Кешбэк" in r for r in parent_reasons)


def test_one_account_per_user_in_db(client, db):
    """В БД не может быть двух счетов орешков на одного пользователя."""
    _register_parent(client)
    child = _onboard_child(client)

    accounts = db.query(LoyaltyAccount).all()
    by_user: dict[int, int] = {}
    for acc in accounts:
        by_user[acc.user_id] = by_user.get(acc.user_id, 0) + 1

    assert all(count == 1 for count in by_user.values()), f"Дубли счетов орешков: {by_user}"


def test_parent_can_see_child_account_but_child_cannot_see_parent(client):
    parent_id = _register_parent(client)
    child = _onboard_child(client)

    # Родитель видит счёт ребёнка.
    assert client.get(f"/loyalty/{child['user_id']}").status_code == 200

    # Ребёнок не видит счёт родителя.
    client.post(
        "/auth/login",
        json={"login": child["login"], "password": child["password"]},
    )
    assert client.get(f"/loyalty/{parent_id}").status_code == 403


def test_conversion_affects_only_own_account(client):
    parent_id = _register_parent(client)
    child = _onboard_child(client)

    client.post(
        "/transactions/simulate",
        json={"card_id": child["card_id"], "amount": 20.0, "category": "toys", "merchant": "Игрушки.by"},
    )
    client.post(
        "/auth/login",
        json={"login": child["login"], "password": child["password"]},
    )

    resp = client.post("/loyalty/convert", json={"points": 10})
    assert resp.status_code == 200

    child_account = client.get(f"/loyalty/{child['user_id']}").json()
    assert child_account["points"] == 0
    assert child_account["converted_byn"] == 1

    # Счёт родителя не тронут.
    client.post("/auth/logout")
    client.post(
        "/auth/login",
        json={"login": "parent@test.by", "password": "Password1!"},
    )
    parent_account = client.get(f"/loyalty/{parent_id}").json()
    assert parent_account["points"] == 0
    assert parent_account["converted_byn"] == 0
