# Layer 1 — Foundational architecture

**Why this layer:** right now every endpoint mixes three jobs — handling the web request,
applying the business rules, and talking to the database. That's fine for a tiny app, but it
makes code hard to test, easy to duplicate, and risky to change. Splitting those jobs into
layers is the single biggest step toward a maintainable backend. (Covers criteria #1, #4, #6, #7.)

## The idea: thin routers, logic in classes

```
app/
  routers/        HTTP only — read the request, call a service, return the response
  services/       Business rules as classes   (BookService, ExchangeService, AuthService)
  repositories/   Database access as classes   (BookRepository, UserRepository, ...)
  models/         Database tables (unchanged)
  schemas/        Request/response shapes (unchanged)
  dependencies.py Shared dependencies (get_current_user, service wiring)
```

- **Repository layer** — the *only* place that runs `db.query(...)`. One class per table with
  methods like `get_by_id`, `list`, `create`.
- **Service layer** — business rules live here, in classes that call repositories. The router
  simply calls `service.do_the_thing(...)`.
- This also removes the repeated **"fetch object or raise 404"** block that appears in almost
  every handler today.

## Before / after (concrete)

**Today** — the router does everything (`routers/books.py:52`):

```python
@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()   # DB access
    if not book:                                               # business rule
        raise HTTPException(status_code=404, detail="Book not found")
    return book
```

**After** — three small pieces, each with one job:

```python
# repositories/book_repository.py — DB access only
class BookRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, book_id: int) -> Book | None:
        return self.db.query(Book).filter(Book.id == book_id).first()


# services/book_service.py — business rules only
class BookService:
    def __init__(self, repo: BookRepository):
        self.repo = repo

    def get_or_404(self, book_id: int) -> Book:
        book = self.repo.get_by_id(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return book


# routers/books.py — HTTP only, now tiny
@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, service: BookService = Depends(get_book_service)):
    return service.get_or_404(book_id)
```

Note the classes have proper `__init__` methods and receive their dependencies — that's the
"class-based with proper init" and "service called from the router" pattern in one shot.

## Business rules that are currently missing

These belong in the new service layer (they're not enforced anywhere today):

- 🟠 An exchange can be created even if the offered/requested book isn't **available**.
- 🟠 Nothing stops **duplicate pending** exchange requests for the same pair of books.
- 🟠 **Accepting** an exchange doesn't mark the books unavailable or reject competing offers.
- 🟡 An exchange status can be moved **back to `pending`** after it was decided.

Putting these in a `ExchangeService` keeps the rules in one readable place instead of spread
across route handlers.

> **Tip:** add a few tests *before* this refactor (see `03-scale.md`). They let you move code
> between layers with confidence that behavior didn't change.
