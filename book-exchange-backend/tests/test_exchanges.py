from .conftest import auth_headers, register_user
from .test_books import create_book


def test_create_list_and_update_exchange(client, registered_user):
    requester_token = registered_user["access_token"]
    receiver = register_user(client, "bob", "bob@example.com")
    receiver_token = receiver["access_token"]
    requested_book = create_book(client, receiver_token, title="Requested Book").json()
    offered_book = create_book(client, requester_token, title="Offered Book").json()

    created = client.post(
        "/exchanges",
        json={
            "requested_book_id": requested_book["id"],
            "offered_book_id": offered_book["id"],
        },
        headers=auth_headers(requester_token),
    )

    assert created.status_code == 201
    exchange = created.json()
    assert exchange["status"] == "pending"
    assert exchange["receiver_id"] == receiver["id"]

    requester_exchanges = client.get(
        "/exchanges", headers=auth_headers(requester_token)
    )
    receiver_exchanges = client.get("/exchanges", headers=auth_headers(receiver_token))
    assert requester_exchanges.status_code == 200
    assert receiver_exchanges.status_code == 200
    assert requester_exchanges.json()[0]["id"] == exchange["id"]
    assert receiver_exchanges.json()[0]["id"] == exchange["id"]

    updated = client.patch(
        f"/exchanges/{exchange['id']}",
        json={"status": "accepted"},
        headers=auth_headers(receiver_token),
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "accepted"


def test_exchange_creation_validates_book_ownership(client, registered_user):
    requester_token = registered_user["access_token"]
    receiver = register_user(client, "bob", "bob@example.com")
    receiver_token = receiver["access_token"]
    requested_book = create_book(client, receiver_token).json()
    receiver_book = create_book(
        client, receiver_token, title="Wrong Owner Offer"
    ).json()

    response = client.post(
        "/exchanges",
        json={
            "requested_book_id": requested_book["id"],
            "offered_book_id": receiver_book["id"],
        },
        headers=auth_headers(requester_token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You can only offer your own books"


def test_exchange_creation_rejects_own_book_and_missing_books(client, registered_user):
    token = registered_user["access_token"]
    own_book = create_book(client, token).json()

    own_book_response = client.post(
        "/exchanges",
        json={"requested_book_id": own_book["id"], "offered_book_id": own_book["id"]},
        headers=auth_headers(token),
    )
    missing_book_response = client.post(
        "/exchanges",
        json={"requested_book_id": 999, "offered_book_id": own_book["id"]},
        headers=auth_headers(token),
    )

    assert own_book_response.status_code == 400
    assert missing_book_response.status_code == 404


def test_only_receiver_can_update_exchange(client, registered_user):
    requester_token = registered_user["access_token"]
    receiver = register_user(client, "bob", "bob@example.com")
    requested_book = create_book(client, receiver["access_token"]).json()
    offered_book = create_book(client, requester_token).json()
    exchange = client.post(
        "/exchanges",
        json={
            "requested_book_id": requested_book["id"],
            "offered_book_id": offered_book["id"],
        },
        headers=auth_headers(requester_token),
    ).json()

    response = client.patch(
        f"/exchanges/{exchange['id']}",
        json={"status": "rejected"},
        headers=auth_headers(requester_token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized"
