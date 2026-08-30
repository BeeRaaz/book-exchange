from enum import Enum

from datetime import datetime, timezone


class ExchangeStatus(str, Enum):
    """Enum describing the lifecycle states of an exchange request."""

    accepted = "accepted"
    rejected = "rejected"
    pending = "pending"


def get_utc_now():
    """Return the current UTC timestamp for model timestamps."""

    return datetime.now(timezone.utc)
