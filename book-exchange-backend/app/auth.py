from datetime import timedelta
from typing import Any
from uuid import uuid4

from .common import get_utc_now

import bcrypt
import jwt

from .config import (
    get_access_token_expire_minutes,
    get_refresh_token_expire_days,
    get_secret_key,
)

SECRET_KEY = get_secret_key()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = get_access_token_expire_minutes()
REFRESH_TOKEN_EXPIRE_DAYS = get_refresh_token_expire_days()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt. Validates that password is within bcrypt's 72-byte limit.

    Bcrypt silently ignores anything past 72 bytes, so we explicitly validate the length
    before hashing to ensure the full password is used.
    """
    # Validate password length respects bcrypt's 72-byte limit
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password must not exceed 72 bytes when encoded in UTF-8.")

    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def _create_token(
    data: dict[str, Any],
    token_type: str,
    expires_delta: timedelta,
) -> str:
    to_encode = data.copy()
    to_encode.update(
        {
            "jti": str(uuid4()),
            "exp": get_utc_now() + expires_delta,
            "type": token_type,
        }
    )
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict[str, Any], expires_delta: int | None = None) -> str:
    lifetime = expires_delta or ACCESS_TOKEN_EXPIRE_MINUTES
    return _create_token(data, "access", timedelta(minutes=lifetime))


def create_refresh_token(data: dict[str, Any], expires_delta: int | None = None) -> str:
    lifetime = expires_delta or REFRESH_TOKEN_EXPIRE_DAYS
    return _create_token(data, "refresh", timedelta(days=lifetime))


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if expected_type is not None and payload.get("type") != expected_type:
        raise ValueError("Unexpected token type")
    return payload


def decode_access_token(token: str) -> dict[str, Any]:
    return decode_token(token, expected_type="access")
