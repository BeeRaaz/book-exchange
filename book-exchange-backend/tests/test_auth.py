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
    assert response.json()["refresh_token"]


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
    assert response.json()["detail"] == "This email or username is already registered."


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
    assert response.json()["detail"] == "This email or username is already registered."


def test_register_prevents_account_enumeration(client):
    """Verify that duplicate email and duplicate username return the same error message.

    This prevents attackers from discovering which emails/usernames are registered
    by comparing different error messages.
    """
    register_user(client, "alice", "alice@example.com")

    # Try registering with duplicate email
    dup_email_response = client.post(
        "/auth/register",
        json={
            "username": "bob",
            "email": "alice@example.com",
            "password": "password",
        },
    )

    # Try registering with duplicate username
    dup_username_response = client.post(
        "/auth/register",
        json={
            "username": "alice",
            "email": "bob@example.com",
            "password": "password",
        },
    )

    # Both should have the same status code and error message
    assert dup_email_response.status_code == 409
    assert dup_username_response.status_code == 409
    assert (
        dup_email_response.json()["detail"]
        == dup_username_response.json()["detail"]
        == "This email or username is already registered."
    )


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
        json={"email": registered_user["email"], "password": "wrongpassword"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials."


def test_login_rejects_inactive_user(client, registered_user, db_session):
    from app.models import User

    # Deactivate the user
    user_id = registered_user["id"]
    user = db_session.query(User).filter(User.id == user_id).first()
    user.is_active = False
    db_session.commit()

    response = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "User account is inactive."


def test_protected_endpoint_requires_authentication(client):
    response = client.get("/auth/me")

    assert response.status_code == 403


def test_refresh_returns_a_new_access_token(client, registered_user):
    refreshed = client.post(
        "/auth/refresh", json={"token": registered_user["refresh_token"]}
    )

    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]
    assert refreshed.json()["refresh_token"]


def test_refresh_rejects_an_access_token(client, registered_user):
    response = client.post(
        "/auth/refresh", json={"token": registered_user["access_token"]}
    )

    assert response.status_code == 401


def test_logout_revokes_refresh_token(client, registered_user):
    logout_response = client.post(
        "/auth/logout",
        json={"refresh_token": registered_user["refresh_token"]},
        headers=auth_headers(registered_user["access_token"]),
    )

    assert logout_response.status_code == 200
    assert logout_response.json()["detail"] == "Logged out successfully"

    # Attempt to refresh with the revoked token
    refresh_response = client.post(
        "/auth/refresh", json={"token": registered_user["refresh_token"]}
    )

    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] == "Token has been revoked."


def test_refresh_rejects_deleted_user(client, registered_user, db_session):
    from app.models import User

    # Delete the user from the database
    user_id = registered_user["id"]
    user = db_session.query(User).filter(User.id == user_id).first()
    db_session.delete(user)
    db_session.commit()

    response = client.post(
        "/auth/refresh", json={"token": registered_user["refresh_token"]}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "User no longer exists."


def test_refresh_rejects_inactive_user(client, registered_user, db_session):
    from app.models import User

    # Deactivate the user
    user_id = registered_user["id"]
    user = db_session.query(User).filter(User.id == user_id).first()
    user.is_active = False
    db_session.commit()

    response = client.post(
        "/auth/refresh", json={"token": registered_user["refresh_token"]}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "User account is inactive."


def test_protected_endpoint_rejects_inactive_user(client, registered_user, db_session):
    from app.models import User

    # Deactivate the user after they have a valid access token
    user_id = registered_user["id"]
    user = db_session.query(User).filter(User.id == user_id).first()
    user.is_active = False
    db_session.commit()

    # Attempt to access a protected endpoint with an access token from an inactive user
    profile = client.get(
        "/auth/me", headers=auth_headers(registered_user["access_token"])
    )

    assert profile.status_code == 401
    assert profile.json()["detail"] == "User account is inactive."
