"""Tests for input validation on auth endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_register_rejects_invalid_email(client):
    """Verify that registration rejects invalid email formats."""
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "not-an-email",
            "password": "password123",
        },
    )

    assert response.status_code == 422  # Validation error
    assert "email" in response.json()["detail"][0]["loc"]


def test_register_rejects_short_password(client):
    """Verify that registration rejects passwords shorter than 8 characters."""
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422  # Validation error
    assert "password" in str(response.json()["detail"][0]["loc"])


def test_register_rejects_very_long_password(client):
    """Verify that registration rejects passwords longer than 72 characters (bcrypt limit)."""
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "a" * 73,  # 73 characters
        },
    )

    assert response.status_code == 422  # Validation error
    assert "password" in str(response.json()["detail"][0]["loc"])


def test_register_rejects_short_username(client):
    """Verify that registration rejects usernames shorter than 3 characters."""
    response = client.post(
        "/auth/register",
        json={
            "username": "ab",  # Only 2 characters
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 422  # Validation error
    assert "username" in str(response.json()["detail"][0]["loc"])


def test_register_rejects_very_long_username(client):
    """Verify that registration rejects usernames longer than 50 characters."""
    response = client.post(
        "/auth/register",
        json={
            "username": "a" * 51,  # 51 characters
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 422  # Validation error
    assert "username" in str(response.json()["detail"][0]["loc"])


def test_register_accepts_valid_credentials(client):
    """Verify that registration accepts valid email, username, and password."""
    response = client.post(
        "/auth/register",
        json={
            "username": "validuser",
            "email": "valid@example.com",
            "password": "validpassword123",
        },
    )

    assert response.status_code == 201
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]


def test_login_rejects_invalid_email(client):
    """Verify that login rejects invalid email formats."""
    response = client.post(
        "/auth/login",
        json={
            "email": "not-an-email",
            "password": "password123",
        },
    )

    assert response.status_code == 422  # Validation error
    assert "email" in response.json()["detail"][0]["loc"]


def test_login_rejects_short_password(client):
    """Verify that login rejects passwords shorter than 8 characters."""
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422  # Validation error
    assert "password" in str(response.json()["detail"][0]["loc"])


def test_register_rejects_password_exceeding_bcrypt_byte_limit(client):
    """Verify that registration rejects passwords that exceed 72 bytes when UTF-8 encoded.

    Bcrypt silently truncates passwords beyond 72 bytes, so we reject them to ensure
    the full password is used for hashing.

    This test uses emoji characters (4 bytes each in UTF-8) to create a password
    that's within the character limit (Pydantic's max_length) but exceeds 72 bytes.
    """
    # Create a password with emoji: 19 emoji * 4 bytes = 76 bytes (exceeds 72)
    # Plus some regular characters to make it valid password length
    password_with_emoji = "password🔒" + ("🔐" * 19)  # ~76 bytes

    # This should pass Pydantic validation (it only counts characters, not bytes)
    # but fail at the bcrypt hashing stage
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": password_with_emoji,
        },
    )

    # Should get a 400 error because hash_password() raises ValueError
    assert response.status_code == 400
    assert "72 bytes" in response.json()["detail"]
