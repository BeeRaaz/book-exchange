from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_current_user, get_book_service
from app.models import User
from app.schemas import BookCreate, BookOut, BookUpdate
from app.services import BookService

router = APIRouter(prefix="/books", tags=["books"])


@router.post("", response_model=BookOut, status_code=status.HTTP_201_CREATED)
def create_book(
    payload: BookCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: BookService = Depends(get_book_service),
):
    """Create a new book owned by the authenticated user."""

    return service.create_book(current_user, payload)


@router.get("", response_model=list[BookOut])
def list_books(
    available: bool | None = None,
    search: str | None = Query(default=None),
    service: BookService = Depends(get_book_service),
):
    """List books using the service-layer filters and ordering rules."""

    return service.get_all_books(available, search)


@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, service: BookService = Depends(get_book_service)):
    """Fetch a single book by id using the shared not-found rule."""

    return service.get_or_404(book_id)


@router.put("/{book_id}", response_model=BookOut)
def update_book(
    book_id: int,
    payload: BookUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    service: BookService = Depends(get_book_service),
):
    """Update a book only when the authenticated user owns it."""

    return service.update_book(book_id, payload, current_user)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    service: BookService = Depends(get_book_service),
):
    """Delete a book after confirming ownership in the service layer."""

    service.delete_book(book_id, current_user)
    return None
