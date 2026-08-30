from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    """Persist and query user records without enforcing business rules."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        """Return a user by primary key, or None when the record is absent."""

        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, user_email: str) -> User | None:
        """Return a user matching the supplied email, if present."""

        return self.db.query(User).filter(User.email == user_email).first()

    def get_by_username(self, user_username: str) -> User | None:
        """Return a user matching the supplied username, if present."""

        return self.db.query(User).filter(User.username == user_username).first()

    def create(
        self,
        username: str,
        email: str,
        password_hash: str,
    ) -> User:
        """Insert a new user and flush the SQLAlchemy session."""

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
        """Commit the current unit of work after a user mutation."""

        self.db.commit()
