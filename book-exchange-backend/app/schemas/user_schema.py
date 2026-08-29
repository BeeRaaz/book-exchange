from pydantic import BaseModel

from datetime import datetime


class RegisterRequest(BaseModel):
    """Payload used for registering a new user account."""

    username: str
    email: str
    password: str


class UserOut(BaseModel):
    """Public user profile returned by the API."""

    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
