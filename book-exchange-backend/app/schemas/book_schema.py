from pydantic import BaseModel

from datetime import datetime


class BookBase(BaseModel):
    """Common book fields shared by create and response models."""

    title: str
    author: str
    description: str | None = None
    genre: str | None = None
    condition: str | None = None
    available: bool = True


class BookCreate(BookBase):
    """Payload used when creating a new book listing."""

    pass


class BookUpdate(BaseModel):
    """Partial update payload for book mutation operations."""

    title: str | None = None
    author: str | None = None
    description: str | None = None
    genre: str | None = None
    condition: str | None = None
    available: bool | None = None


class BookOut(BookBase):
    """Book representation returned by the API."""

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
