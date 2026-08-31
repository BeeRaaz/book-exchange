from sqlalchemy.orm import Session

from app.common import ExchangeStatus
from app.models import Exchange, User


class ExchangeRepository:
    """Persist and query exchange records without enforcing business rules."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, exchange_id: int) -> Exchange | None:
        """Return an exchange by id, or None when the record is absent."""

        return self.db.query(Exchange).filter(Exchange.id == exchange_id).first()

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

    def get_pending_involving_books(
        self, book_ids: list[int], except_exchange_id: int
    ) -> list[Exchange]:
        """Return pending exchanges that include any of the given books."""

        return (
            self.db.query(Exchange)
            .filter(
                Exchange.id != except_exchange_id,
                Exchange.status == ExchangeStatus.pending,
                (Exchange.requested_book_id.in_(book_ids))
                | (Exchange.offered_book_id.in_(book_ids)),
            )
            .all()
        )

    def create(
        self,
        requester_id: int,
        receiver_id: int,
        requested_book_id: int,
        offered_book_id: int,
    ) -> Exchange:
        """Create an exchange record linking the requester, receiver, and books."""

        exchange = Exchange(
            requester_id=requester_id,
            receiver_id=receiver_id,
            requested_book_id=requested_book_id,
            offered_book_id=offered_book_id,
        )

        self.db.add(exchange)
        self.db.flush()
        self.db.refresh(exchange)
        return exchange

    def update_status(self, exchange: Exchange, status: ExchangeStatus) -> Exchange:
        """Apply a new status to an exchange without committing."""

        exchange.status = status
        self.db.flush()
        return exchange

    def commit(self) -> None:
        """Persist the current unit of work after an exchange mutation."""

        self.db.commit()
