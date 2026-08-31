from sqlalchemy.orm import Session

from app.models import Book


class BookRepository:
    """Persist and query books without applying authorization rules."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, book_id: int) -> Book | None:
        """Return a book by primary key, or None when absent."""

        return self.db.query(Book).filter(Book.id == book_id).first()

    def get_all(
        self, available: bool | None = None, search: str | None = None
    ) -> list[Book]:
        """Return books ordered newest first with optional filters."""

        query = self.db.query(Book)
        if available is not None:
            query = query.filter(Book.available == available)
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                (Book.title.ilike(search_term)) | (Book.author.ilike(search_term))
            )
        return query.order_by(Book.created_at.desc()).all()

    def create(
        self,
        title: str,
        author: str,
        description: str | None,
        genre: str | None,
        condition: str | None,
        available: bool,
        owner_id: int,
    ) -> Book:
        """Add a book and flush it so generated fields are available."""

        book = Book(
            title=title,
            author=author,
            description=description,
            genre=genre,
            condition=condition,
            available=available,
            owner_id=owner_id,
        )

        self.db.add(book)
        self.db.flush()
        self.db.refresh(book)
        return book

    def update(self, book_id: int, updates: dict) -> Book | None:
        """Apply supplied fields to a book without committing the transaction."""

        book = self.get_by_id(book_id)
        if not book:
            return None
        for field, value in updates.items():
            setattr(book, field, value)
        self.db.flush()
        return book

    def delete(self, book_id: int) -> bool:
        """Delete a book and return whether a record was actually removed."""

        book = self.get_by_id(book_id)
        if not book:
            return False
        self.db.delete(book)
        self.db.flush()
        return True

    def commit(self) -> None:
        """Persist the current unit of work after a book mutation."""

        self.db.commit()
