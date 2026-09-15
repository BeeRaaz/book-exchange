from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum

from sqlalchemy.orm import relationship

from ..database import Base

from ..common import ExchangeStatus, get_utc_now


class Exchange(Base):
    """Database model representing a book exchange request and its lifecycle."""

    __tablename__ = "exchanges"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    requested_book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    offered_book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    status = Column(
        SQLEnum(ExchangeStatus), default=ExchangeStatus.pending, nullable=False, index=True
    )
    created_at = Column(DateTime, default=get_utc_now, nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=get_utc_now,
        onupdate=get_utc_now,
        nullable=False,
    )

    requester = relationship(
        "User", foreign_keys=[requester_id], back_populates="sent_exchanges"
    )
    receiver = relationship(
        "User", foreign_keys=[receiver_id], back_populates="received_exchanges"
    )
    requested_book = relationship("Book", foreign_keys=[requested_book_id])
    offered_book = relationship("Book", foreign_keys=[offered_book_id])
