from datetime import datetime

from pydantic import BaseModel

from app.common import ExchangeStatus


class ExchangeCreate(BaseModel):
    """Payload used to initiate a new exchange request."""

    requested_book_id: int
    offered_book_id: int


class ExchangeStatusUpdate(BaseModel):
    """Payload used to change an exchange status to a new enum value."""

    status: ExchangeStatus


class ExchangeOut(BaseModel):
    """Exchange representation returned by the API."""

    id: int
    requester_id: int
    receiver_id: int
    requested_book_id: int
    offered_book_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
