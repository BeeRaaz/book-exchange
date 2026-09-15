from fastapi import HTTPException

from app.common import ExchangeStatus
from app.models import Book, Exchange, User
from app.repositories import BookRepository, ExchangeRepository
from app.schemas import ExchangeCreate, ExchangeStatusUpdate


class ExchangeService:
    """Encapsulate business rules for exchange creation and status updates."""

    def __init__(self, repo: ExchangeRepository, books: BookRepository):
        self.repo = repo
        self.books = books

    def get_or_404(self, exchange_id: int) -> Exchange:
        """Return an exchange or raise a 404 error when it does not exist."""

        exchange = self.repo.get_by_id(exchange_id)

        if not exchange:
            raise HTTPException(status_code=404, detail="Exchange not found")

        return exchange

    def get_all_exchanges(
        self,
        current_user: User,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Exchange]:
        """Return every exchange involving the current user."""

        return self.repo.get_all(current_user, limit, offset)

    def _validate_book_pair(
        self, current_user: User, payload: ExchangeCreate
    ) -> tuple[Book, Book]:
        """Fetch both books and reject invalid ownership or duplicate request combinations."""

        requested_book = self.books.get_by_id(payload.requested_book_id)
        offered_book = self.books.get_by_id(payload.offered_book_id)

        if requested_book is None or offered_book is None:
            missing_book_id = (
                payload.requested_book_id
                if requested_book is None
                else payload.offered_book_id
            )
            raise HTTPException(
                status_code=404, detail=f"Book {missing_book_id} not found"
            )

        if requested_book.owner_id == current_user.id:
            raise HTTPException(
                status_code=400, detail="You cannot request your own book"
            )

        if offered_book.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only offer your own books",
            )

        if requested_book.id == offered_book.id:
            raise HTTPException(
                status_code=400, detail="You cannot exchange a book with itself"
            )

        existing = self.repo.get_pending_by_books(
            current_user.id,
            payload.requested_book_id,
            payload.offered_book_id,
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Pending exchange already exists",
            )

        return requested_book, offered_book

    def create_exchange(self, current_user: User, payload: ExchangeCreate) -> Exchange:
        """Create a new exchange after validating ownership, availability, and duplicate rules."""

        requested_book, offered_book = self._validate_book_pair(current_user, payload)

        if not requested_book.available:
            raise HTTPException(
                status_code=409,
                detail="Requested book is not available",
            )

        if not offered_book.available:
            raise HTTPException(
                status_code=409,
                detail="Offered book is not available",
            )

        exchange = self.repo.create(
            requester_id=current_user.id,
            receiver_id=requested_book.owner_id,
            requested_book_id=requested_book.id,
            offered_book_id=offered_book.id,
        )
        self.repo.commit()
        return exchange

    def update_exchange(
        self, exchange_id: int, payload: ExchangeStatusUpdate, current_user: User
    ) -> Exchange:
        """Apply a status change while enforcing receiver-only permission checks."""

        exchange = self.get_or_404(exchange_id)

        if exchange.receiver_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized",
            )

        if (
            exchange.status != ExchangeStatus.pending
            and payload.status == ExchangeStatus.pending
        ):
            raise HTTPException(
                status_code=409,
                detail="An exchange cannot return to pending once it has been decided.",
            )

        if payload.status == ExchangeStatus.accepted:
            self._accept_exchange(exchange)

        updated = self.repo.update_status(exchange, payload.status)
        self.repo.commit()
        return updated

    def _accept_exchange(self, exchange: Exchange) -> None:
        """Mark both books unavailable and reject competing pending offers."""

        requested_book = self.books.get_by_id(exchange.requested_book_id)
        offered_book = self.books.get_by_id(exchange.offered_book_id)

        if requested_book is None or offered_book is None:
            missing_book_id = (
                exchange.requested_book_id
                if requested_book is None
                else exchange.offered_book_id
            )
            raise HTTPException(
                status_code=404, detail=f"Book {missing_book_id} not found"
            )

        self.books.update(requested_book.id, {"available": False})
        self.books.update(offered_book.id, {"available": False})

        competitors = self.repo.get_pending_involving_books(
            [requested_book.id, offered_book.id],
            except_exchange_id=exchange.id,
        )
        for competitor in competitors:
            self.repo.update_status(competitor, ExchangeStatus.rejected)
