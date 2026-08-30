from .conftest import auth_headers, register_user

BOOK = {
    "title": "The Dispossessed",
    "author": "Ursula K. Le Guin",
    "description": "A thoughtful science-fiction novel",
    "genre": "Science fiction",
    "condition": "Good",
}


def create_book(client, token, **overrides):
    return client.post(
        "/books", json={**BOOK, **overrides}, headers=auth_headers(token)
    )


def test_create_get_update_and_delete_book(client, registered_user):
    token = registered_user["access_token"]
    created = create_book(client, token)

    assert created.status_code == 201
    book = created.json()
    assert book["title"] == BOOK["title"]
    assert book["owner_id"] == registered_user["id"]

    fetched = client.get(f"/books/{book['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == book["id"]

    updated = client.put(
        f"/books/{book['id']}",
        json={"available": False, "condition": "Fair"},
        headers=auth_headers(token),
    )
    assert updated.status_code == 200
    assert updated.json()["available"] is False
    assert updated.json()["condition"] == "Fair"

    deleted = client.delete(f"/books/{book['id']}", headers=auth_headers(token))
    assert deleted.status_code == 204
    assert client.get(f"/books/{book['id']}").status_code == 404


def test_list_books_filters_by_availability_and_search(client, registered_user):
    token = registered_user["access_token"]
    create_book(client, token, title="Available Novel", available=True)
    create_book(client, token, title="Unavailable Novel", available=False)

    response = client.get("/books", params={"available": True, "search": "available"})

    assert response.status_code == 200
    assert [book["title"] for book in response.json()] == ["Available Novel"]


def test_book_operations_reject_non_owner(client, registered_user):
    book = create_book(client, registered_user["access_token"]).json()
    other_user = register_user(client, "bob", "bob@example.com")

    update = client.put(
        f"/books/{book['id']}",
        json={"title": "Changed"},
        headers=auth_headers(other_user["access_token"]),
    )
    delete = client.delete(
        f"/books/{book['id']}", headers=auth_headers(other_user["access_token"])
    )

    assert update.status_code == 403
    assert delete.status_code == 403


def test_book_endpoints_return_not_found_for_missing_book(client, registered_user):
    headers = auth_headers(registered_user["access_token"])

    assert client.get("/books/999").status_code == 404
    assert (
        client.put("/books/999", json={"title": "Missing"}, headers=headers).status_code
        == 404
    )
    assert client.delete("/books/999", headers=headers).status_code == 404
