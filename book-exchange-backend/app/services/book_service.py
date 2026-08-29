from fastapi import HTTPException

from app.models import Book, User
from app.repositories import BookRepository
from app.schemas import BookCreate, BookUpdate


class BookService:
    """Apply book business rules while delegating persistence to a repository."""

    def __init__(self, repo: BookRepository):
        self.repo = repo

    def get_or_404(self, book_id: int) -> Book:
        """Return a book or raise the standard not-found error."""

        book = self.repo.get_by_id(book_id)

        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        return book

    def get_all_books(
        self,
        available: bool | None = None,
        search: str | None = None,
    ) -> list[Book]:
        """Return books matching the optional public filters."""

        return self.repo.get_all(available, search)

    def create_book(self, current_user: User, payload: BookCreate) -> Book:
        """Create a book owned by the authenticated user."""
        return self.repo.create(
            payload.title,
            payload.author,
            payload.description,
            payload.genre,
            payload.condition,
            payload.available,
            current_user.id,
        )

    def update_book(
        self, book_id: int, payload: BookUpdate, current_user: User
    ) -> Book:
        """Update a book only when it belongs to the authenticated user."""

        book = self.get_or_404(book_id)

        if book.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        updates = payload.model_dump(exclude_unset=True)

        return self.repo.update(book_id, updates)

    def delete_book(self, book_id: int, current_user: User) -> None:
        """Delete a book only when it belongs to the authenticated user."""

        book = self.get_or_404(book_id)

        if book.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        self.repo.delete(book_id)
