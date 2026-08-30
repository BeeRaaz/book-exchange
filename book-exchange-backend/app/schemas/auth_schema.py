from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Request payload for email/password authentication."""

    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Request payload carrying a JWT token for refresh operations."""

    token: str


class TokenResponse(BaseModel):
    """API payload returned after successful login, registration, or token refresh."""

    id: int | None = None
    access_token: str
    token_type: str = "bearer"
