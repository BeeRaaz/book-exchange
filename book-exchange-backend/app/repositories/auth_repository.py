from sqlalchemy.orm import Session

from app.models import User


class AuthRepository:
    """Repository for authentication-related user persistence operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        """Return a user by primary key, or None when the user does not exist."""

        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, user_email: str) -> User | None:
        """Return a user matching the supplied email address."""

        return self.db.query(User).filter(User.email == user_email).first()

    def get_by_username(self, user_username: str) -> User | None:
        """Return a user matching the supplied username."""

        return self.db.query(User).filter(User.username == user_username).first()

    def create(self, username: str, email: str, password_hash: str) -> User:
        """Create and flush a new user record."""

        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
        )

        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user

    def commit(self) -> None:
        """Persist the current transaction for authentication-related writes."""

        self.db.commit()
