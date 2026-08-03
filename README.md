# Book Exchange

A full-stack book exchange application. This repository currently contains the FastAPI backend in `book-exchange-backend`, with the frontend to be added later.

## Project structure

- `book-exchange-backend/` — FastAPI backend API
- `README.md` — project overview
- `book-exchange-frontend/` — planned frontend app (to be added)

## Backend

The backend is built with:

- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT auth with `python-jose`
- bcrypt password hashing
- CORS support

### Features

- User registration and login
- JWT authentication
- Book CRUD
- Book search and filtering
- Book exchange requests
- Exchange status updates

## API overview

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/refresh`

### Books

- `POST /books`
- `GET /books`
- `GET /books/{book_id}`
- `PUT /books/{book_id}`
- `DELETE /books/{book_id}`

### Exchanges

- `POST /exchanges`
- `GET /exchanges`
- `PATCH /exchanges/{exchange_id}`
