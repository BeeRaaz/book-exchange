import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _read_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    return value.strip()


def normalize_database_url(value: str | None) -> str | None:
    if not value:
        return value

    cleaned = value.strip()
    if cleaned.startswith("psql"):
        cleaned = cleaned[len("psql") :].strip()

    if cleaned.startswith("'") and cleaned.endswith("'"):
        cleaned = cleaned[1:-1].strip()

    if cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1].strip()

    return cleaned


def get_database_url() -> str:
    value = normalize_database_url(_read_env("DATABASE_URL"))
    if not value:
        raise RuntimeError("DATABASE_URL is required")
    return value


def get_secret_key() -> str:
    value = _read_env("SECRET_KEY")
    if not value:
        raise RuntimeError("SECRET_KEY is required")
    return value


def get_access_token_expire_minutes() -> int:
    value = _read_env("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    if not value:
        return 30
    return int(value)


def get_allowed_origins(raw_value: str | None = None) -> List[str]:
    resolved_value = raw_value or _read_env(
        "ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    )
    if not resolved_value:
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    return [origin.strip() for origin in resolved_value.split(",") if origin.strip()]
