from uuid import uuid4


def unique_email() -> str:
    return f"user-{uuid4().hex}@example.com"


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "voice-ai-dsa-mentor-api"}


def test_signin_creates_a_new_user_on_first_login(client):
    email = unique_email()

    response = client.post("/api/auth/signin", json={"email": email, "password": "hunter2"})

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == email
    assert body["lastProblemId"] == 0
    assert body["token"]


def test_signin_rejects_an_invalid_email(client):
    response = client.post("/api/auth/signin", json={"email": "not-an-email", "password": "hunter2"})

    assert response.status_code == 422


def test_signin_accepts_the_correct_password_for_an_existing_user(client):
    email = unique_email()
    client.post("/api/auth/signin", json={"email": email, "password": "hunter2"})

    response = client.post("/api/auth/signin", json={"email": email, "password": "hunter2"})

    assert response.status_code == 200


def test_signin_rejects_the_wrong_password_for_an_existing_user(client):
    email = unique_email()
    client.post("/api/auth/signin", json={"email": email, "password": "hunter2"})

    response = client.post("/api/auth/signin", json={"email": email, "password": "wrong-password"})

    assert response.status_code == 401


def test_signin_is_rate_limited_after_too_many_attempts_for_the_same_email(client):
    email = unique_email()
    client.post("/api/auth/signin", json={"email": email, "password": "hunter2"})

    # 4 more attempts brings the total to 5 (the configured limit).
    for _ in range(4):
        response = client.post("/api/auth/signin", json={"email": email, "password": "wrong-password"})
        assert response.status_code == 401

    blocked_response = client.post("/api/auth/signin", json={"email": email, "password": "wrong-password"})

    assert blocked_response.status_code == 429


def test_last_problem_requires_authentication(client):
    response = client.get("/api/users/me/last-problem")

    assert response.status_code == 401


def test_last_problem_rejects_an_unknown_token(client):
    response = client.get(
        "/api/users/me/last-problem",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401


def test_last_problem_can_be_read_and_updated_after_signin(client):
    email = unique_email()
    signin_response = client.post("/api/auth/signin", json={"email": email, "password": "hunter2"})
    token = signin_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    initial = client.get("/api/users/me/last-problem", headers=headers)
    assert initial.status_code == 200
    assert initial.json()["lastProblemId"] == 0

    updated = client.patch("/api/users/me/last-problem", json={"problemId": 2}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["lastProblemId"] == 2

    confirmed = client.get("/api/users/me/last-problem", headers=headers)
    assert confirmed.json()["lastProblemId"] == 2


def test_sign_out_invalidates_the_token(client):
    email = unique_email()
    signin_response = client.post("/api/auth/signin", json={"email": email, "password": "hunter2"})
    token = signin_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    sign_out_response = client.delete("/api/auth/signout", headers=headers)
    assert sign_out_response.status_code == 204

    after_signout = client.get("/api/users/me/last-problem", headers=headers)
    assert after_signout.status_code == 401
