from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.dependencies import get_auth_service, get_current_user
from app.models import User
from app.rate_limiter import (
    limiter,
    LOGIN_RATE_LIMIT,
    REGISTER_RATE_LIMIT,
    REFRESH_RATE_LIMIT,
    LOGOUT_RATE_LIMIT,
    ME_RATE_LIMIT,
)
from app.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
    LogoutRequest,
)
from app.services import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(REGISTER_RATE_LIMIT)
def register_user(
    request: Request,
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Register a new user through the auth service and return an access token."""

    return service.register(payload)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(LOGIN_RATE_LIMIT)
def login_user(
    request: Request,
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Authenticate a user through the auth service and return a JWT token."""

    return service.login(payload)


@router.get("/me", response_model=UserOut)
@limiter.limit(ME_RATE_LIMIT)
def get_current_user_profile(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Return the authenticated user’s profile information."""

    return user


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(REFRESH_RATE_LIMIT)
def refresh_token(
    request: Request,
    payload: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Validate an existing token and issue a replacement access token."""

    return service.refresh(payload)


@router.post("/logout", status_code=status.HTTP_200_OK)
@limiter.limit(LOGOUT_RATE_LIMIT)
def logout(
    request: Request,
    payload: LogoutRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: AuthService = Depends(get_auth_service),
):
    """Revoke the refresh token and end the user's session."""

    service.logout(payload.refresh_token, current_user.id)
    return {"detail": "Logged out successfully"}
