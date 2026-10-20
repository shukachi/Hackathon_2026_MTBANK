"""API-тесты лояльности: счёт орешков, кешбэк за покупку, конвертация в рубли."""


def _register_parent(client, login: str = "parent@test.by") -> int:
    resp = client.post(
        "/auth/register",
        json={"login": login, "password": "Password1!", "full_name": "Parent Test"},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def _onboard_child(client, name: str = "Child Test", age: int = 10) -> dict:
    """Создаёт ребёнка и возвращает его id, card_id, логин и временный пароль."""
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
    """Логинится под ребёнком — орешки и квесты принадлежат именно ему."""
    resp = client.post(
        "/auth/login",
        json={"login": child["login"], "password": child["password"]},
    )
    assert resp.status_code == 200


def test_new_child_has_empty_nut_account(client):
    _register_parent(client)
    child = _onboard_child(client)

    resp = client.get(f"/loyalty/{child['user_id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["points"] == 0
    assert body["converted_byn"] == 0
    assert body["points_per_byn"] == 10


def test_parent_has_own_nut_account(client):
    parent_id = _register_parent(client)

    resp = client.get(f"/loyalty/{parent_id}")
    assert resp.status_code == 200
    assert resp.json()["points"] == 0
    assert resp.json()["points_per_byn"] == 10


def test_cashback_awarded_on_purchase(client):
    _register_parent(client)
    child = _onboard_child(client)

    # Покупку делаем из-под родителя — орешки начисляются владельцу карты (ребёнку).
    resp = client.post(
        "/transactions/simulate",
        json={"card_id": child["card_id"], "amount": 20.0, "category": "toys", "merchant": "Игрушки.by"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["blocked"] is False
    assert body["cashback_points"] == 10  # 5% от 20 BYN = 1 BYN = 10 орешков

    loyalty = client.get(f"/loyalty/{child['user_id']}")
    assert loyalty.json()["points"] == 10
    assert any("Кешбэк" in h["reason"] for h in loyalty.json()["history"])


def test_no_cashback_for_games(client):
    _register_parent(client)
    child = _onboard_child(client)

    resp = client.post(
        "/transactions/simulate",
        json={"card_id": child["card_id"], "amount": 20.0, "category": "games", "merchant": "Steam"},
    )
    assert resp.status_code == 200
    assert resp.json()["cashback_points"] == 0
    assert client.get(f"/loyalty/{child['user_id']}").json()["points"] == 0


def test_blocked_transaction_gives_no_cashback(client):
    _register_parent(client)
    child = _onboard_child(client)

    # Лимит 5 BYN в неделю на сладости
    client.put(
        "/limits",
        json={"child_id": child["user_id"], "category": "sweets", "amount": 5, "period": "week"},
    )

    resp = client.post(
        "/transactions/simulate",
        json={"card_id": child["card_id"], "amount": 10.0, "category": "sweets", "merchant": "Кондитерская"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["blocked"] is True
    assert body["cashback_points"] == 0
    assert client.get(f"/loyalty/{child['user_id']}").json()["points"] == 0


def test_quest_reward_credits_nuts(client):
    _register_parent(client)
    child = _onboard_child(client)

    quest = client.post(
        "/quests",
        json={
            "child_id": child["user_id"],
            "title": "Помой посуду",
            "description": "Помой посуду",
            "reward_points": 15,
        },
    )
    assert quest.status_code == 200
    quest_id = quest.json()["id"]

    # Квест завершает сам ребёнок — награда идёт на его счёт орешков.
    _login_as_child(client, child)
    resp = client.post(f"/quests/{quest_id}/complete")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"

    loyalty = client.get(f"/loyalty/{child['user_id']}")
    assert loyalty.json()["points"] == 15
    assert any("Квест выполнен" in h["reason"] for h in loyalty.json()["history"])


def test_convert_points_to_byn(client):
    _register_parent(client)
    child = _onboard_child(client)

    # 20 BYN в игрушках = 10 орешков на счёте ребёнка
    client.post(
        "/transactions/simulate",
        json={"card_id": child["card_id"], "amount": 20.0, "category": "toys", "merchant": "Игрушки.by"},
    )

    # Конвертирует ребёнок — деньги попадают на его счёт.
    _login_as_child(client, child)
    resp = client.post("/loyalty/convert", json={"points": 10})
    assert resp.status_code == 200
    body = resp.json()
    assert body["points_spent"] == 10
    assert body["byn_amount"] == 1
    assert body["points_left"] == 0
    assert body["converted_byn"] == 1
    assert body["account"]["converted_byn"] == 1


def test_convert_rejects_non_multiple_of_10(client):
    _register_parent(client)
    resp = client.post("/loyalty/convert", json={"points": 7})
    assert resp.status_code == 400
    assert "кратное" in resp.json()["detail"]


def test_convert_rejects_more_than_balance(client):
    _register_parent(client)
    resp = client.post("/loyalty/convert", json={"points": 10})
    assert resp.status_code == 400
    assert "орешков" in resp.json()["detail"]


def test_child_cannot_see_other_family_nut_account(client):
    _register_parent(client, "parentA@test.by")
    child_a = _onboard_child(client, "Child A")

    client.post("/auth/logout")
    _register_parent(client, "parentB@test.by")
    child_b = _onboard_child(client, "Child B")

    resp = client.get(f"/loyalty/{child_a['user_id']}")
    assert resp.status_code == 403
