from fastapi import HTTPException
from datetime import datetime

from app.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.repositories import UserRepository, RevokedTokenRepository
from app.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.user_service import UserService


class AuthService:
    """Issue tokens and verify credentials; persist users through UserService."""

    def __init__(
        self,
        users: UserService,
        repo: UserRepository,
        revoked_tokens: RevokedTokenRepository,
    ):
        self.users = users
        self.repo = repo
        self.revoked_tokens = revoked_tokens

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
            refresh_token=create_refresh_token(
                {"sub": user.username, "user_id": user.id}
            ),
        )

    def login(self, payload: LoginRequest) -> TokenResponse:
        """Verify credentials and return an access token for an authenticated user."""

        user = self.repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials.")

        if not user.is_active:
            raise HTTPException(status_code=401, detail="User account is inactive.")

        return TokenResponse(
            id=user.id,
            access_token=create_access_token(
                {"sub": user.username, "user_id": user.id}
            ),
            refresh_token=create_refresh_token(
                {"sub": user.username, "user_id": user.id}
            ),
        )

    def refresh(self, payload: RefreshTokenRequest) -> TokenResponse:
        """Validate refresh token, check revocation, re-verify user, and issue new tokens."""

        try:
            decoded = decode_token(payload.token, expected_type="refresh")
        except Exception as exc:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token."
            ) from exc

        if not decoded.get("sub") or not decoded.get("user_id"):
            raise HTTPException(status_code=401, detail="Invalid token payload.")

        jti = decoded.get("jti")
        if not jti:
            raise HTTPException(status_code=401, detail="Token missing JTI.")

        # Check if the refresh token has been revoked
        if self.revoked_tokens.is_revoked(jti):
            raise HTTPException(status_code=401, detail="Token has been revoked.")

        # Re-fetch the user to detect deletion or deactivation
        user_id = decoded.get("user_id")
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User no longer exists.")

        if not user.is_active:
            raise HTTPException(status_code=401, detail="User account is inactive.")

        return TokenResponse(
            id=user.id,
            access_token=create_access_token(
                {"sub": user.username, "user_id": user.id}
            ),
            refresh_token=create_refresh_token(
                {"sub": user.username, "user_id": user.id}
            ),
        )

    def logout(self, refresh_token: str, user_id: int) -> None:
        """Revoke a refresh token to end the user's session."""

        try:
            decoded = decode_token(refresh_token, expected_type="refresh")
        except Exception as exc:
            raise HTTPException(
                status_code=401, detail="Invalid or expired token."
            ) from exc

        jti = decoded.get("jti")
        if not jti:
            raise HTTPException(status_code=400, detail="Token missing JTI.")

        exp_timestamp = decoded.get("exp")
        if not exp_timestamp:
            raise HTTPException(status_code=400, detail="Token missing expiration.")

        # Convert Unix timestamp to datetime
        expires_at = datetime.fromtimestamp(exp_timestamp)

        self.revoked_tokens.revoke(jti, user_id, expires_at)
        self.revoked_tokens.commit()
