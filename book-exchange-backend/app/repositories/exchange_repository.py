from sqlalchemy.orm import Session

from app.common import ExchangeStatus
from app.models import Book, Exchange, User


class ExchangeRepository:
    """Persist and query exchange records without enforcing business rules."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, exchange_id: int) -> Exchange | None:
        """Return an exchange by id, or None when the record is absent."""

        return self.db.query(Exchange).filter(Exchange.id == exchange_id).first()

    def get_book_by_id(self, book_id: int) -> Book | None:
        """Fetch a book instance used by the exchange service for validation."""

        return self.db.query(Book).filter(Book.id == book_id).first()

    def get_all(self, current_user: User) -> list[Exchange]:
        """Return all exchanges involving the supplied user, ordered newest first."""

        return (
            self.db.query(Exchange)
            .filter(
                (Exchange.requester_id == current_user.id)
                | (Exchange.receiver_id == current_user.id)
            )
            .order_by(Exchange.created_at.desc())
            .all()
        )

    def get_pending_by_books(
        self,
        requester_id: int,
        requested_book_id: int,
        offered_book_id: int,
    ) -> Exchange | None:
        """Check whether a pending exchange already exists for the same book pair."""

        return (
            self.db.query(Exchange)
            .filter(
                Exchange.requester_id == requester_id,
                Exchange.requested_book_id == requested_book_id,
                Exchange.offered_book_id == offered_book_id,
                Exchange.status == ExchangeStatus.pending,
            )
            .first()
        )

    def create(
        self, current_user: User, requested_book_id: int, offered_book_id: int
    ) -> Exchange:
        """Create an exchange record linking the requester, receiver, and books."""

        requested_book = self.get_book_by_id(requested_book_id)
        offered_book = self.get_book_by_id(offered_book_id)

        exchange = Exchange(
            requester_id=current_user.id,
            receiver_id=requested_book.owner_id,
            requested_book_id=requested_book.id,
            offered_book_id=offered_book.id,
        )

        self.db.add(exchange)
        self.db.commit()
        self.db.refresh(exchange)
        return exchange

    def update(self, exchange_id: int, status: ExchangeStatus) -> Exchange:
        """Update the exchange status and persist the transaction."""

        exchange = self.db.query(Exchange).filter(Exchange.id == exchange_id).first()

        exchange.status = status

        if status == ExchangeStatus.accepted:
            requested_book = self.get_book_by_id(exchange.requested_book_id)
            offered_book = self.get_book_by_id(exchange.offered_book_id)
            if requested_book:
                requested_book.available = False
            if offered_book:
                offered_book.available = False

        self.db.commit()
        self.db.refresh(exchange)
        return exchange
