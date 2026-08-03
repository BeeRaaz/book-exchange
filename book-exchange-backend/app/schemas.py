from datetime import datetime

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BookBase(BaseModel):
    title: str
    author: str
    description: str | None = None
    genre: str | None = None
    condition: str | None = None
    available: bool = True


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    description: str | None = None
    genre: str | None = None
    condition: str | None = None
    available: bool | None = None


class BookOut(BookBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExchangeCreate(BaseModel):
    requested_book_id: int
    offered_book_id: int


class ExchangeOut(BaseModel):
    id: int
    requester_id: int
    receiver_id: int
    requested_book_id: int
    offered_book_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
