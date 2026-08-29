from fastapi import HTTPException

from app.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.repositories import AuthRepository
from app.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)


class AuthService:
    """Apply authentication rules while delegating persistence to an auth repository."""

    def __init__(self, repo: AuthRepository):
        self.repo = repo

    def register(self, payload: RegisterRequest) -> TokenResponse:
        """Register a new user and return a signed access token."""

        if not payload.email or not payload.password:
            raise HTTPException(
                status_code=400, detail="Email and password are required."
            )

        if self.repo.get_by_email(payload.email):
            raise HTTPException(status_code=409, detail="Email already registered.")

        if self.repo.get_by_username(payload.username):
            raise HTTPException(status_code=409, detail="Username already taken.")

        user = self.repo.create(
            payload.username,
            payload.email,
            hash_password(payload.password),
        )
        self.repo.commit()

        return TokenResponse(
            id=user.id,
            access_token=create_access_token(
                {"sub": user.username, "user_id": user.id}
            ),
        )

    def login(self, payload: LoginRequest) -> TokenResponse:
        """Verify credentials and return an access token for an authenticated user."""

        user = self.repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials.")

        return TokenResponse(
            id=user.id,
            access_token=create_access_token(
                {"sub": user.username, "user_id": user.id}
            ),
        )

    def refresh(self, payload: RefreshTokenRequest) -> TokenResponse:
        """Validate an existing token and issue a replacement access token."""

        try:
            decoded = decode_access_token(payload.token)
        except Exception as exc:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token."
            ) from exc

        if not decoded.get("sub") or not decoded.get("user_id"):
            raise HTTPException(status_code=401, detail="Invalid token payload.")

        return TokenResponse(
            id=decoded.get("user_id"),
            access_token=create_access_token(
                {"sub": decoded["sub"], "user_id": decoded["user_id"]}
            ),
        )
