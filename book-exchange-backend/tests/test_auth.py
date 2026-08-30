from .conftest import auth_headers, register_user


def test_register_returns_access_token(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "password",
        },
    )

    assert response.status_code == 201
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_register_rejects_duplicate_email(client):
    register_user(client, "alice", "alice@example.com")

    response = client.post(
        "/auth/register",
        json={
            "username": "different",
            "email": "alice@example.com",
            "password": "password",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered."


def test_register_rejects_duplicate_username(client):
    register_user(client, "alice", "alice@example.com")

    response = client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "different@example.com",
            "password": "password",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Username already taken."


def test_login_and_current_user_profile(client, registered_user):
    response = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200

    profile = client.get(
        "/auth/me", headers=auth_headers(response.json()["access_token"])
    )

    assert profile.status_code == 200
    assert profile.json()["username"] == "alice"
    assert profile.json()["email"] == "alice@example.com"


def test_login_rejects_invalid_credentials(client, registered_user):
    response = client.post(
        "/auth/login",
        json={"email": registered_user["email"], "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials."


def test_protected_endpoint_requires_authentication(client):
    response = client.get("/auth/me")

    assert response.status_code == 403


def test_refresh_returns_a_new_access_token(client, registered_user):
    refreshed = client.post(
        "/auth/refresh", json={"token": registered_user["access_token"]}
    )

    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]
