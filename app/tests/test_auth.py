def test_register_creates_user(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "diver@example.com", "password": "correcthorsebattery"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "diver@example.com"
    assert body["role"] == "user"
    assert "hashed_password" not in body  # never leak the hash


def test_register_duplicate_email_returns_409(client):
    payload = {"email": "dup@example.com", "password": "correcthorsebattery"}
    client.post("/api/auth/register", json=payload)
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409


def test_login_returns_access_token(client):
    client.post(
        "/api/auth/register",
        json={"email": "captain@example.com", "password": "correcthorsebattery"},
    )
    response = client.post(
        "/api/auth/login",
        data={"username": "captain@example.com", "password": "correcthorsebattery"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password_returns_401(client):
    client.post(
        "/api/auth/register",
        json={"email": "wrongpass@example.com", "password": "correcthorsebattery"},
    )
    response = client.post(
        "/api/auth/login",
        data={"username": "wrongpass@example.com", "password": "not-the-password"},
    )
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user_with_valid_token(client):
    client.post(
        "/api/auth/register",
        json={"email": "researcher@example.com", "password": "correcthorsebattery"},
    )
    login_response = client.post(
        "/api/auth/login",
        data={"username": "researcher@example.com", "password": "correcthorsebattery"},
    )
    token = login_response.json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "researcher@example.com"
