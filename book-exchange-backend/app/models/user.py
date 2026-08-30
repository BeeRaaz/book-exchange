from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base

from ..common import get_utc_now


class User(Base):
    """Database model representing an authenticated application user."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime,
        default=get_utc_now,
        onupdate=get_utc_now,
        nullable=False,
    )

    books = relationship("Book", back_populates="owner", cascade="all, delete-orphan")
    sent_exchanges = relationship(
        "Exchange",
        foreign_keys="Exchange.requester_id",
        back_populates="requester",
        cascade="all, delete-orphan",
    )
    received_exchanges = relationship(
        "Exchange",
        foreign_keys="Exchange.receiver_id",
        back_populates="receiver",
        cascade="all, delete-orphan",
    )
