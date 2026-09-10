from sqlalchemy.orm import Session

from datetime import datetime
from ..models import RevokedToken
from ..common import get_utc_now


class RevokedTokenRepository:
    """Persist and query revoked JWT tokens without enforcing business rules."""

    def __init__(self, db: Session):
        self.db = db

    def revoke(self, jti: str, user_id: int, expires_at: datetime) -> RevokedToken:
        """Store a revoked token identifier for blacklisting."""

        revoked_token = RevokedToken(
            jti=jti,
            user_id=user_id,
            expires_at=expires_at,
        )
        self.db.add(revoked_token)
        self.db.flush()
        self.db.refresh(revoked_token)
        return revoked_token

    def is_revoked(self, jti: str) -> bool:
        """Check if a token has been revoked by its JWT ID."""

        return (
            self.db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
            is not None
        )

    def cleanup_expired(self) -> None:
        """Delete expired revoked token records from the database."""

        self.db.query(RevokedToken).filter(
            RevokedToken.expires_at < get_utc_now()
        ).delete()
        self.db.flush()

    def commit(self) -> None:
        """Persist the current unit of work after revocation."""

        self.db.commit()
