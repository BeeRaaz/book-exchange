"""Tests for rate limiting on auth endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.database import get_db
from app.main import app
from app.rate_limiter import limiter


@pytest.fixture
def rate_limit_client(db_session: Session):
    """Create a test client with rate limiting enabled and database configured."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Enable rate limiting for these tests
    limiter.enabled = True

    client = TestClient(app)
    yield client

    # Cleanup
    app.dependency_overrides.clear()
    limiter.enabled = False


def test_login_rate_limiting(rate_limit_client):
    """Verify that login endpoint enforces rate limiting (5/minute)."""

    # Make 5 requests that will fail on auth
    for i in range(5):
        response = rate_limit_client.post(
            "/auth/login",
            json={"email": f"user{i}@example.com", "password": "password"},
        )
        # All should get auth errors, not rate limit errors
        assert response.status_code == 401

    # The 6th request should be rate limited
    response = rate_limit_client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "password"},
    )
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]


def test_register_rate_limiting(rate_limit_client):
    """Verify that register endpoint enforces rate limiting (3/minute)."""

    # Make 3 requests
    for i in range(3):
        response = rate_limit_client.post(
            "/auth/register",
            json={
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "password": "password",
            },
        )
        # All should succeed or fail on validation, not rate limit
        assert response.status_code != 429

    # The 4th request should be rate limited
    response = rate_limit_client.post(
        "/auth/register",
        json={
            "username": "user3",
            "email": "user3@example.com",
            "password": "password",
        },
    )
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]


def test_refresh_rate_limiting(rate_limit_client):
    """Verify that refresh endpoint enforces rate limiting (10/minute)."""

    # Make 10 requests with invalid token
    for i in range(10):
        response = rate_limit_client.post(
            "/auth/refresh",
            json={"token": "invalid_token"},
        )
        # Should get auth error, not rate limit error
        assert response.status_code == 401

    # The 11th request should be rate limited
    response = rate_limit_client.post(
        "/auth/refresh",
        json={"token": "invalid_token"},
    )
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]
