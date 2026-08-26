from enum import Enum

from datetime import datetime, timezone


class ExchangeStatus(str, Enum):
    accepted = "accepted"
    rejected = "rejected"
    pending = "pending"


def get_utc_now():
    return datetime.now(timezone.utc)
