def test_list_children_returns_onboarded_kids_with_cards(client):
    client.post(
        "/auth/register",
        json={"login": "parentC@test.by", "password": "Password1!", "full_name": "Parent C"},
    )
    client.post(
        "/family/onboarding",
        json={"child_full_name": "Kid One", "age": 10, "consent_given": True},
    )
    client.post(
        "/family/onboarding",
        json={"child_full_name": "Teen One", "age": 15, "consent_given": True},
    )

    resp = client.get("/family/children")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = {c["user"]["full_name"] for c in data}
    assert names == {"Kid One", "Teen One"}
    for c in data:
        assert c["card"]["id"]
        assert c["card"]["status"] == "active"


def test_list_children_requires_parent_role(client):
    client.post(
        "/auth/register",
        json={"login": "parentD@test.by", "password": "Password1!", "full_name": "Parent D"},
    )
    onboarding = client.post(
        "/family/onboarding",
        json={"child_full_name": "Kid D", "age": 10, "consent_given": True},
    )
    child_login = onboarding.json()["login"]
    child_password = onboarding.json()["temporary_password"]

    client.post("/auth/logout")
    client.post("/auth/login", json={"login": child_login, "password": child_password})

    resp = client.get("/family/children")
    assert resp.status_code == 403


def test_my_card_endpoint_for_child(client):
    client.post(
        "/auth/register",
        json={"login": "parentE@test.by", "password": "Password1!", "full_name": "Parent E"},
    )
    onboarding = client.post(
        "/family/onboarding",
        json={"child_full_name": "Kid E", "age": 10, "consent_given": True},
    )
    onboarding_data = onboarding.json()
    child_login = onboarding_data["login"]
    child_password = onboarding_data["temporary_password"]
    expected_card_id = onboarding_data["card_id"]

    client.post("/auth/logout")
    client.post("/auth/login", json={"login": child_login, "password": child_password})

    resp = client.get("/cards/me")
    assert resp.status_code == 200
    assert resp.json()["id"] == expected_card_id


def test_onboarding_response_includes_full_card_object(client):
    client.post(
        "/auth/register",
        json={"login": "parentF@test.by", "password": "Password1!", "full_name": "Parent F"},
    )
    resp = client.post(
        "/family/onboarding",
        json={"child_full_name": "Kid F", "age": 10, "consent_given": True},
    )
    data = resp.json()
    assert data["card"]["id"] == data["card_id"]
    assert data["card"]["status"] == "active"
    assert data["card"]["design"] == "child"
