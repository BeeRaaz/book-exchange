from fastapi import APIRouter, Depends, status

from app.dependencies import get_auth_service, get_current_user
from app.models import User
from app.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.services import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: RegisterRequest, service: AuthService = Depends(get_auth_service)
):
    """Register a new user through the auth service and return an access token."""

    return service.register(payload)


@router.post("/login", response_model=TokenResponse)
def login_user(payload: LoginRequest, service: AuthService = Depends(get_auth_service)):
    """Authenticate a user through the auth service and return a JWT token."""

    return service.login(payload)


@router.get("/me", response_model=UserOut)
def get_current_user_profile(user: User = Depends(get_current_user)):
    """Return the authenticated user’s profile information."""

    return user


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest, service: AuthService = Depends(get_auth_service)
):
    """Validate an existing token and issue a replacement access token."""

    return service.refresh(payload)
