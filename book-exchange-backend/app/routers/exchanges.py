from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Book, Exchange, User
from ..routers.auth import get_current_user
from ..schemas import ExchangeCreate, ExchangeOut

router = APIRouter(prefix="/exchanges", tags=["exchanges"])


@router.post("", response_model=ExchangeOut, status_code=status.HTTP_201_CREATED)
def create_exchange(
    payload: ExchangeCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    requested_book = db.query(Book).filter(Book.id == payload.requested_book_id).first()
    offered_book = db.query(Book).filter(Book.id == payload.offered_book_id).first()

    if not requested_book or not offered_book:
        raise HTTPException(status_code=404, detail="One or more books not found")
    if requested_book.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot request your own book")
    if offered_book.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only offer your own books")

    exchange = Exchange(
        requester_id=current_user.id,
        receiver_id=requested_book.owner_id,
        requested_book_id=requested_book.id,
        offered_book_id=offered_book.id,
    )
    db.add(exchange)
    db.commit()
    db.refresh(exchange)
    return exchange


@router.get("", response_model=list[ExchangeOut])
def list_exchanges(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    exchanges = (
        db.query(Exchange)
        .filter(
            (Exchange.requester_id == current_user.id)
            | (Exchange.receiver_id == current_user.id)
        )
        .order_by(Exchange.created_at.desc())
        .all()
    )
    return exchanges


@router.patch("/{exchange_id}", response_model=ExchangeOut)
def update_exchange_status(
    exchange_id: int,
    status_value: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    exchange = db.query(Exchange).filter(Exchange.id == exchange_id).first()
    if not exchange:
        raise HTTPException(status_code=404, detail="Exchange not found")
    if exchange.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if status_value not in {"accepted", "rejected", "pending"}:
        raise HTTPException(status_code=400, detail="Invalid status")

    exchange.status = status_value
    db.commit()
    db.refresh(exchange)
    return exchange
