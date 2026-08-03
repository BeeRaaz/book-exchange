from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_allowed_origins
from .database import Base, engine
from .routers import auth, books, exchanges

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Book Exchange API",
    description="API for managing book exchanges",
    version="1.0.0",
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
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Book Exchange API is running"}
