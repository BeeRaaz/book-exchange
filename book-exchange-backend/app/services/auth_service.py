from fastapi import HTTPException

from app.auth import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from app.repositories import UserRepository
from app.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.user_service import UserService


class AuthService:
    """Issue tokens and verify credentials; persist users through UserService."""

    def __init__(self, users: UserService, repo: UserRepository):
        self.users = users
        self.repo = repo

    def register(self, payload: RegisterRequest) -> TokenResponse:
        """Register a new user and return a signed access token."""

        if not payload.email or not payload.password:
            raise HTTPException(
                status_code=400, detail="Email and password are required."
            )

        user = self.users.create_user(payload)
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
