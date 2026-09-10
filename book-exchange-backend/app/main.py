from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

from .config import get_allowed_origins
from .database import Base, engine
from .rate_limiter import limiter
from .routers import auth, books, exchanges

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Book Exchange API",
    description="API for managing book exchanges",
    version="1.0.0",
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    lambda request, exc: JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Too many requests."},
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(exchanges.router)


@app.get("/health")
def health_check():
    """Return a basic readiness response for service checks."""

    return {"status": "ok"}


@app.get("/")
def root():
    """Return a lightweight welcome payload for the API root endpoint."""

    return {"message": "Book Exchange API is running"}
