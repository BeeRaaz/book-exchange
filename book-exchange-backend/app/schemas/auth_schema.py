from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Request payload for email/password authentication."""

    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=72,
        description="Password must be 8-72 characters",
    )


class RefreshTokenRequest(BaseModel):
    """Request payload carrying a JWT token for refresh operations."""

    token: str


class TokenResponse(BaseModel):
    """API payload returned after successful authentication or token refresh."""

    id: int | None = None
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    """Request payload for logging out and revoking a refresh token."""

    refresh_token: str
