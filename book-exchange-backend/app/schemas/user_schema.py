from pydantic import BaseModel, EmailStr, Field

from datetime import datetime


class RegisterRequest(BaseModel):
    """Payload used for registering a new user account."""

    username: str = Field(
        min_length=3,
        max_length=50,
        description="Username must be 3-50 characters",
    )
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=72,
        description="Password must be 8-72 characters",
    )


class UserOut(BaseModel):
    """Public user profile returned by the API."""

    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
