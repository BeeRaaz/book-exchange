from sqlalchemy import Column, Integer, String, ForeignKey, DateTime

from ..common import get_utc_now

from ..database import Base


class RevokedToken(Base):
    """Database model representing a revoked JWT token."""

    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    revoked_at = Column(DateTime, default=get_utc_now, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
