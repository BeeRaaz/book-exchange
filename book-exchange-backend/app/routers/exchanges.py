from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user, get_exchange_service
from app.models import User
from app.schemas import ExchangeCreate, ExchangeOut, ExchangeStatusUpdate
from app.services import ExchangeService

router = APIRouter(prefix="/exchanges", tags=["exchanges"])


@router.post("", response_model=ExchangeOut, status_code=status.HTTP_201_CREATED)
def create_exchange(
    payload: ExchangeCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: ExchangeService = Depends(get_exchange_service),
):
    """Create a book exchange after validating ownership and availability rules."""

    return service.create_exchange(current_user, payload)


@router.get("", response_model=list[ExchangeOut])
def list_exchanges(
    current_user: Annotated[User, Depends(get_current_user)],
    service: ExchangeService = Depends(get_exchange_service),
):
    """Return all exchanges where the current user is involved."""

    return service.get_all_exchanges(current_user)


@router.patch("/{exchange_id}", response_model=ExchangeOut)
def update_exchange_status(
    exchange_id: int,
    payload: ExchangeStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: ExchangeService = Depends(get_exchange_service),
):
    """Update an exchange status in a single service-managed workflow."""

    return service.update_exchange(exchange_id, payload, current_user)
