import logging

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import get_allowed_origins
from .rate_limiter import limiter
from .routers import auth, books, exchanges
from .database import get_db
from .logging_config import setup_logging
from .middleware import RequestLoggingMiddleware

# Configure application logging
setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Book Exchange API",
    description="API for managing book exchanges",
    version="1.0.0",
)

# Add middleware for request logging and request ID
app.add_middleware(RequestLoggingMiddleware)

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
def health_check(db: Session = Depends(get_db)):
    """Return the health status of the API and database connectivity."""

    try:
        # Perform a simple database query to check connectivity
        db.execute(text("SELECT 1"))

        logger.info("Database health check passed")

        return {
            "status": "healthy",
            "database": "available",
        }
    except Exception:
        logger.exception("Health check failed. Database connectivity issue")

        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "unavailable",
            },
        )


@app.get("/")
def root():
    """Return a lightweight welcome payload for the API root endpoint."""

    return {"message": "Book Exchange API is running"}
