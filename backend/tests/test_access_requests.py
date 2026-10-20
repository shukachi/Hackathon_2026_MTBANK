def test_access_request_flow_and_cross_family_denied(client):
    # Family A
    client.post(
        "/auth/register",
        json={"login": "parentA2@test.by", "password": "Password1!", "full_name": "Parent A"},
    )
    onboarding = client.post(
        "/family/onboarding",
        json={"child_full_name": "Teen A", "age": 16, "consent_given": True},
    )
    assert onboarding.status_code == 200
    onboarding_data = onboarding.json()
    child_login = onboarding_data["login"]
    child_password = onboarding_data["temporary_password"]
    family_a_id = onboarding_data["user"]["family_id"]

    client.post("/auth/logout")

    # Login as the child/teen and create an access request.
    client.post("/auth/login", json={"login": child_login, "password": child_password})
    req_resp = client.post("/access-requests", json={"feature": "subscription"})
    assert req_resp.status_code == 200
    request_id = req_resp.json()["id"]
    assert req_resp.json()["status"] == "pending"

    client.post("/auth/logout")

    # Login as parent A and approve.
    client.post("/auth/login", json={"login": "parentA2@test.by", "password": "Password1!"})

    list_resp = client.get(f"/access-requests?family_id={family_a_id}")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    decide_resp = client.post(f"/access-requests/{request_id}/decide", json={"decision": "approved"})
    assert decide_resp.status_code == 200
    assert decide_resp.json()["status"] == "approved"

    client.post("/auth/logout")

    # Family B parent cannot decide on family A's request.
    client.post(
        "/auth/register",
        json={"login": "parentB2@test.by", "password": "Password1!", "full_name": "Parent B"},
    )
    onboarding_b = client.post(
        "/family/onboarding",
        json={"child_full_name": "Teen B", "age": 16, "consent_given": True},
    )
    assert onboarding_b.status_code == 200
    teen_b_login = onboarding_b.json()["login"]
    teen_b_password = onboarding_b.json()["temporary_password"]

    client.post("/auth/logout")
    client.post("/auth/login", json={"login": teen_b_login, "password": teen_b_password})
    req_b = client.post("/access-requests", json={"feature": "savings_product"})
    assert req_b.status_code == 200
    request_b_id = req_b.json()["id"]

    client.post("/auth/logout")
    client.post("/auth/login", json={"login": "parentA2@test.by", "password": "Password1!"})

    cross_decide = client.post(f"/access-requests/{request_b_id}/decide", json={"decision": "approved"})
    assert cross_decide.status_code == 403
