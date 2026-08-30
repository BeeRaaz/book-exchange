from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..database import Base

from ..common import get_utc_now


class Book(Base):
    """Database model for a user-owned book listing."""

    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    author = Column(String(150), nullable=False)
    description = Column(String(1000), nullable=True)
    genre = Column(String(100), nullable=True)
    condition = Column(String(50), nullable=True)
    available = Column(Boolean, default=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(
        DateTime,
        default=get_utc_now,
        onupdate=get_utc_now,
        nullable=False,
    )

    owner = relationship("User", back_populates="books")
