from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
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


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    author = Column(String(150), nullable=False)
    description = Column(String(1000), nullable=True)
    genre = Column(String(100), nullable=True)
    condition = Column(String(50), nullable=True)
    available = Column(Boolean, default=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    owner = relationship("User", back_populates="books")


class Exchange(Base):
    __tablename__ = "exchanges"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    requested_book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    offered_book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    status = Column(String(30), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
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
