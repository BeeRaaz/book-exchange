# Backend Feedback — Book Exchange

Hey 👋 This folder is a step-by-step review of the backend. It's split into small files so you
can take it **one layer at a time** instead of all at once. This is a solid first version — the
notes below are the things that turn a working prototype into a production backend, with the
*why* behind each so it's clear it's worth doing.

**Read in this order:**

1. [`00-immediate-fixes.md`](./00-immediate-fixes.md) — quick, safe wins → **start here**
2. [`01-architecture.md`](./01-architecture.md) — how to structure the code as it grows
3. [`02-security.md`](./02-security.md) — closing the auth & abuse gaps
4. [`03-scale.md`](./03-scale.md) — surviving real traffic

Severity tags used throughout: 🔴 Critical · 🟠 High · 🟡 Medium · 🟢 Low

---

## What the backend does today

An HTTP API for a book-swapping app: **accounts** (register/login/JWT), **books** (add / edit /
delete / list / search), and **exchanges** (offer your book for someone else's; they accept or
reject).

**How a request flows through the code:**

```
HTTP request
   → CORS middleware (main.py)
   → router (routers/auth.py | books.py | exchanges.py)
   → get_current_user   (decodes the JWT, loads the User)   ← auth check
   → get_db             (opens a database session)
   → the handler runs db.query(...) directly and applies the rules
   → Pydantic schema (schemas.py) shapes the JSON response
   → HTTP response
```

**File map:**

| File | Role |
|------|------|
| `app/main.py` | Entry point — creates tables, sets up CORS, mounts routers |
| `app/config.py` | Reads environment variables (DB URL, secret key, CORS origins) |
| `app/database.py` | DB engine, session factory, `get_db` dependency |
| `app/models.py` | Database tables as classes: `User`, `Book`, `Exchange` |
| `app/schemas.py` | Request/response shapes (Pydantic) |
| `app/auth.py` | Password hashing (bcrypt) + JWT create/decode helpers |
| `app/routers/*.py` | The endpoints **+ all business logic + all DB queries** |

The key thing to notice: today the app is really **two layers** — routers and database models.
Everything a bigger backend usually separates out (business rules, database access) currently
lives inside the routers. Fixing that is Layer 1.

---

## Scorecard (the 11 criteria)

| # | Criterion | Verdict | One-liner | Covered in |
|---|-----------|---------|-----------|-----------|
| 1 | Layered (MVC-style) architecture | ⚠️ Partial | No service or repository layer | 01 |
| 2 | Components reused, not copy-pasted | ⚠️ Weak | Some duplication | 00, 01 |
| 3 | No duplicate functions | ❌ | `/me` duplicates `get_current_user` | 00 |
| 4 | Class-based with proper structure | ⚠️ Partial | Models are classes; no service/repo classes | 01 |
| 5 | Naming & type annotations | ✅ Good | Consistent `snake_case` + type hints | — |
| 6 | Services accessed from routers | ❌ | Routers hit the DB directly | 01 |
| 7 | Dedicated query/data-access classes | ❌ | `db.query(...)` scattered everywhere | 01 |
| 8 | Authentication present | ⚠️ Leaky | Works, but refresh & validation are weak | 02 |
| 9 | Sync vs async handled correctly | ❌ | `get_db` is `async` with a sync session | 00, 03 |
| 10 | Handles ~1,000 concurrent requests | ❌ | No pagination, small pool, single worker | 03 |
| 11 | Rate limiter | ❌ | None — login can be brute-forced | 02 |

**What's already good (keep doing it):** clean naming & type hints (Python's `snake_case` /
`PascalCase` conventions are followed correctly), a well-related data model with cascades and
indexes, ownership checks on edit/delete, bcrypt-hashed passwords, JWT auth, and CORS origins
that are explicitly restricted rather than wide open.

---

## Suggested order (this is not an overnight job)

1. **Layer 0** — quick wins, no risk. Good warm-up.
2. **A small test suite** — do this *before* the big refactor so nothing breaks silently.
3. **Layer 1** — the architecture change. Everything else sits on top of it.
4. **Layer 2** — security, especially the refresh-token fix and rate limiting.
5. **Layer 3** — scale work, as traffic grows.

Order matters: **correctness → structure → security → scale.** Doing security/scale on top of
the current router-heavy code means redoing it after the Layer 1 refactor.

---

## Mini-glossary

- **Service layer** — classes holding the *business rules* (e.g. "you can't request your own
  book"), separate from the web code. Makes logic reusable and testable.
- **Repository / data-access layer** — classes whose only job is talking to the database.
- **JWT** — a signed token handed out at login and sent back to prove who you are.
  **Refresh token** — a separate, longer-lived token used to get new login tokens.
- **Rate limiting** — capping requests per client per time window to stop brute-force/abuse.
- **Pagination** — returning results in pages (e.g. 20 at a time) instead of everything at once.
- **Connection pool** — a fixed set of reusable database connections shared across requests.
- **Migrations (Alembic)** — versioned, reviewable database schema changes instead of
  auto-creating tables from code.
