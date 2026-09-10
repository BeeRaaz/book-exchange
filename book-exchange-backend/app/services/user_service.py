from fastapi import HTTPException

from app.auth import hash_password
from app.models import User
from app.repositories import UserRepository
from app.schemas import RegisterRequest


class UserService:
    """Apply user-related business rules while delegating persistence to a repository."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def get_by_id_or_404(self, user_id: int) -> User:
        """Return a user by id or raise the standard not-found error."""

        user = self.repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=404, detail="User not found with the given id"
            )

        return user

    def get_by_email_or_404(self, user_email: str) -> User:
        """Return a user by email or raise a 404 error when no match exists."""

        user = self.repo.get_by_email(user_email)

        if not user:
            raise HTTPException(
                status_code=404, detail="User not found with the given email"
            )

        return user

    def get_by_username_or_404(self, user_username: str) -> User:
        """Return a user by username or raise a 404 error when no match exists."""

        user = self.repo.get_by_username(user_username)

        if not user:
            raise HTTPException(
                status_code=404, detail="User not found with the given username"
            )

        return user

    def create_user(self, payload: RegisterRequest) -> User:
        """Create a user after hashing the password and confirming uniqueness."""

        if self.repo.get_by_email(payload.email):
            raise HTTPException(
                status_code=409,
                detail="This email or username is already registered.",
            )

        if self.repo.get_by_username(payload.username):
            raise HTTPException(
                status_code=409,
                detail="This email or username is already registered.",
            )

        try:
            password_hash = hash_password(payload.password)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return self.repo.create(
            username=payload.username,
            email=payload.email,
            password_hash=password_hash,
        )
