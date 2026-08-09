# Layer 0 — Immediate fixes

**Why this layer:** these are small, safe changes that remove real bugs and inconsistencies
without restructuring anything. Low risk, quick to do, and they clean up the codebase before the
bigger work. A day or two total.

| Item | Where | Why we need it (plain terms) | Fix direction |
|------|-------|------------------------------|---------------|
| 🟠 `/me` duplicates the auth dependency | `routers/auth.py:76` vs `:120` | The exact same "decode token → load user" logic exists twice. Two copies drift apart and you fix bugs twice. | Make `/me` just use `Depends(get_current_user)` and delete the duplicate body |
| 🟠 `get_db` is `async` but uses a **sync** session | `database.py:18` | It's declared the "concurrent" way but does blocking work — a mismatch that can quietly stall the server under load. | Change it to a normal `def get_db()` |
| 🟡 Deprecated `datetime.utcnow()` | `models.py` (all timestamps) | Deprecated in Python 3.12 (will warn now, break later) and inconsistent with `auth.py`, which already uses the modern form. | Standardize on `datetime.now(timezone.utc)` (or DB-side `func.now()`) |
| 🟡 Auth dependency lives inside a router | `routers/auth.py:120`, imported by `books.py` & `exchanges.py` | Routers importing from other routers tangles the code. A shared helper should live somewhere neutral. | Move `get_current_user` into a new `app/dependencies.py` |
| 🟡 Exchange status is a raw query string | `routers/exchanges.py:62` (`status_value: str`) | Any text can be sent; it's easy to pass an invalid status and there's no self-documenting contract. | Accept a request body with an `Enum` of allowed statuses (`pending`/`accepted`/`rejected`) |
| 🟢 Unknown-user token returns 404 instead of 401 | `routers/auth.py:136` | Returning "not found" for a token we shouldn't trust leaks information; the honest answer is "unauthorized." | Return `401` |
| 🟢 Dependency named `dotenv` | `pyproject.toml:9` | `dotenv` is a thin wrapper package; the real library is `python-dotenv`. Depending on the wrapper is a footgun. | Depend on `python-dotenv` directly |

---

### Example — the duplicate `/me` fix

**Today** (`routers/auth.py`) — two functions doing the same thing:

```python
@router.get("/me", response_model=UserOut)
def get_current_user_profile(credentials=Depends(security), db=Depends(get_db)):
    token = credentials.credentials
    payload = decode_access_token(token)        # ← same as get_current_user
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    ...

def get_current_user(credentials=Depends(security), db=Depends(get_db)) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)        # ← duplicated logic
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    ...
```

**After** — `/me` reuses the one dependency:

```python
@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user
```

One source of truth. This is the smallest example of the reuse principle that Layer 1 applies to
the whole codebase.
