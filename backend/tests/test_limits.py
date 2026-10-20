def _register_parent_and_child(client, age=10):
    client.post(
        "/auth/register",
        json={"login": "parent@test.by", "password": "Password1!", "full_name": "Parent"},
    )
    onboarding = client.post(
        "/family/onboarding",
        json={"child_full_name": "Kid", "age": age, "consent_given": True},
    )
    assert onboarding.status_code == 200
    data = onboarding.json()
    return data["user"]["id"], data["card_id"]


def test_set_limit_and_simulate_within_limit_approved(client):
    child_id, card_id = _register_parent_and_child(client)

    limit_resp = client.put(
        "/limits",
        json={"child_id": child_id, "category": "sweets", "amount": 50, "period": "week"},
    )
    assert limit_resp.status_code == 200

    sim_resp = client.post(
        "/transactions/simulate",
        json={"card_id": card_id, "amount": 20, "category": "sweets", "merchant": "Candy shop"},
    )
    assert sim_resp.status_code == 200
    data = sim_resp.json()
    assert data["blocked"] is False
    assert data["transaction"]["status"] == "approved"


def test_simulate_over_limit_blocked(client):
    child_id, card_id = _register_parent_and_child(client)

    client.put(
        "/limits",
        json={"child_id": child_id, "category": "sweets", "amount": 50, "period": "week"},
    )

    # First purchase within limit.
    client.post(
        "/transactions/simulate",
        json={"card_id": card_id, "amount": 40, "category": "sweets", "merchant": "Candy shop"},
    )

    # Second purchase pushes total over the 50 BYN/week limit.
    sim_resp = client.post(
        "/transactions/simulate",
        json={"card_id": card_id, "amount": 20, "category": "sweets", "merchant": "Candy shop"},
    )
    assert sim_resp.status_code == 200
    data = sim_resp.json()
    assert data["blocked"] is True
    assert data["transaction"]["status"] == "blocked_by_limit"
    assert data["reason"] is not None
