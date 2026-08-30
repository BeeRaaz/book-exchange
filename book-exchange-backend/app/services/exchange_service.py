from fastapi import HTTPException

from app.common import ExchangeStatus
from app.models import Exchange, User
from app.repositories import ExchangeRepository
from app.schemas import ExchangeCreate, ExchangeStatusUpdate


class ExchangeService:
    """Encapsulate business rules for exchange creation and status updates."""

    def __init__(self, repo: ExchangeRepository):
        self.repo = repo

    def get_or_404(self, exchange_id: int) -> Exchange:
        """Return an exchange or raise a 404 error when it does not exist."""

        exchange = self.repo.get_by_id(exchange_id)

        if not exchange:
            raise HTTPException(status_code=404, detail="Exchange not found")

        return exchange

    def get_all_exchanges(self, current_user: User) -> list[Exchange]:
        """Return every exchange involving the current user."""

        return self.repo.get_all(current_user)

    def _validate_book_pair(
        self, current_user: User, payload: ExchangeCreate
    ) -> tuple[Exchange, Exchange]:
        """Fetch both books and reject invalid ownership or duplicate request combinations."""

        requested_book = self.repo.get_book_by_id(payload.requested_book_id)
        offered_book = self.repo.get_book_by_id(payload.offered_book_id)

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

        return self.repo.create(
            current_user,
            payload.requested_book_id,
            payload.offered_book_id,
        )

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

        return self.repo.update(exchange_id, payload.status)
