def test_register_login_me(client):
    resp = client.post(
        "/auth/register",
        json={"login": "parent1@test.by", "password": "Password1!", "full_name": "Parent One"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["login"] == "parent1@test.by"
    assert data["role"] == "parent"

    # register sets cookie already, but let's explicitly login too
    resp = client.post("/auth/login", json={"login": "parent1@test.by", "password": "Password1!"})
    assert resp.status_code == 200
    assert "access_token" in resp.cookies

    resp = client.get("/auth/me")
    assert resp.status_code == 200
    me = resp.json()
    assert me["login"] == "parent1@test.by"
    assert me["full_name"] == "Parent One"


def test_protected_route_without_cookie_401(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_parent_cannot_access_other_family_child(client):
    # Family A: parent + child via onboarding
    client.post(
        "/auth/register",
        json={"login": "parentA@test.by", "password": "Password1!", "full_name": "Parent A"},
    )
    onboarding_resp = client.post(
        "/family/onboarding",
        json={"child_full_name": "Child A", "age": 10, "consent_given": True},
    )
    assert onboarding_resp.status_code == 200
    child_a_id = onboarding_resp.json()["user"]["id"]

    client.post("/auth/logout")

    # Family B: different parent
    client.post(
        "/auth/register",
        json={"login": "parentB@test.by", "password": "Password1!", "full_name": "Parent B"},
    )
    client.post("/auth/login", json={"login": "parentB@test.by", "password": "Password1!"})

    # Parent B tries to set a limit for child belonging to family A -> 403
    resp = client.put(
        "/limits",
        json={"child_id": child_a_id, "category": None, "amount": 100, "period": "week"},
    )
    assert resp.status_code == 403
