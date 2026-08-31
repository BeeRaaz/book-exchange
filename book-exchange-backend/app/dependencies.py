from fastapi import Depends, HTTPException

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .auth import decode_access_token
from .repositories import (
    BookRepository,
    ExchangeRepository,
    UserRepository,
)
from .services import (
    AuthService,
    BookService,
    ExchangeService,
    UserService,
)

security = HTTPBearer(auto_error=False)


def get_book_repo(db: Session = Depends(get_db)) -> BookRepository:
    """Create a repository instance bound to the current request database session."""

    return BookRepository(db)


def get_book_service(repo: BookRepository = Depends(get_book_repo)) -> BookService:
    """Resolve the book service with its repository dependency."""

    return BookService(repo)


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    """Create a repository instance bound to the current request database session."""

    return UserRepository(db)


def get_user_service(repo: UserRepository = Depends(get_user_repo)) -> UserService:
    """Resolve the user service with its repository dependency."""

    return UserService(repo)


def get_exchange_repo(db: Session = Depends(get_db)) -> ExchangeRepository:
    """Create an exchange repository bound to the current request session."""

    return ExchangeRepository(db)


def get_exchange_service(
    repo: ExchangeRepository = Depends(get_exchange_repo),
    books: BookRepository = Depends(get_book_repo),
) -> ExchangeService:
    """Resolve the exchange service with exchange and book persistence."""

    return ExchangeService(repo, books)


def get_auth_service(
    users: UserService = Depends(get_user_service),
    repo: UserRepository = Depends(get_user_repo),
) -> AuthService:
    """Resolve auth with user creation rules and shared user persistence."""

    return AuthService(users, repo)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    """Validate the bearer token and return the authenticated user."""

    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=403, detail="Not authenticated")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        ) from exc

    user_id = payload.get("user_id")
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized User")

    return user
