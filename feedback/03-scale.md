# Layer 3 — Scale & performance

**Why this layer:** the app works fine for a handful of users, but a traffic spike (your
"1,000 requests at once" question) would expose a few bottlenecks. These changes let one server
handle real load, and let you grow safely. (Covers #9 and #10.)

> **About "load balancing":** true load balancing is an *infrastructure* job — running several
> copies of the app behind a load balancer. Inside the app, the things that decide whether a
> single copy survives a spike are: **pagination, database connection-pool size, worker count,
> async I/O, caching, and rate limiting.** That's what this layer is about.

| Item | Where | Why we need it (plain terms) | Fix direction |
|------|-------|------------------------------|---------------|
| 🔴 No pagination | `list_books`, `list_exchanges` | These return **every** row (`.all()`). With a large table one request can eat all the memory and time out. | Add `limit`/`offset` (or cursor) paging + a sensible default cap |
| 🟠 Small DB connection pool | `database.py` (defaults) | Default ~15 DB connections vs ~40 request threads → requests queue up and stall under load. | Tune `pool_size` / `max_overflow`; add `pool_pre_ping=True` |
| 🟠 Fully synchronous stack | routes + `psycopg2` | Works, but each request holds a thread while waiting on the DB, which caps concurrency. | Run multiple workers now (gunicorn + uvicorn workers); consider async SQLAlchemy + `asyncpg` later |
| 🟠 No migrations | `main.py:8` (`create_all`) | Tables are created from code at startup — fine locally, risky in production (no versioned schema changes). | Adopt **Alembic** migrations |
| 🟠 No automated tests | whole project | Nothing catches regressions as you refactor Layers 1–2. This is the safety net for everything else. | Add `pytest` + a small suite (do this alongside Layer 1) |
| 🟡 Search can't use an index | `routers/books.py:44` | `ILIKE '%term%'` scans the whole table, which gets slow as books grow. | Add proper indexes / Postgres full-text search |
| 🟡 No observability | whole project | When something breaks in production there are no logs, request IDs, or metrics to debug it. | Add structured logging + a DB-aware health check |

---

### Quick "will it handle 1,000 at once?" summary

As-is: **no** — the first thing to break would be the connection pool (requests waiting for a
free DB connection), followed by memory/timeouts on the un-paginated list endpoints.

The realistic path to "yes":
1. **Pagination** on list endpoints (biggest single win).
2. **Tune the connection pool** to match your worker/thread count.
3. **Run multiple workers** (and multiple app instances behind a load balancer as you grow).
4. **Add caching** for hot, rarely-changing reads (e.g. book listings) when needed.
5. **Move to async DB** if you're still I/O-bound after the above.

None of this is needed on day one — it's the order to reach for as traffic climbs.
