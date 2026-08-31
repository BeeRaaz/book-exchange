from .conftest import auth_headers, register_user
from .test_books import create_book


def request_exchange(client, token, requested_book_id, offered_book_id):
    return client.post(
        "/exchanges",
        json={
            "requested_book_id": requested_book_id,
            "offered_book_id": offered_book_id,
        },
        headers=auth_headers(token),
    )


def test_create_list_and_update_exchange(client, registered_user):
    requester_token = registered_user["access_token"]
    receiver = register_user(client, "bob", "bob@example.com")
    receiver_token = receiver["access_token"]
    requested_book = create_book(client, receiver_token, title="Requested Book").json()
    offered_book = create_book(client, requester_token, title="Offered Book").json()

    created = request_exchange(
        client, requester_token, requested_book["id"], offered_book["id"]
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
    assert client.get(f"/books/{requested_book['id']}").json()["available"] is False
    assert client.get(f"/books/{offered_book['id']}").json()["available"] is False


def test_exchange_creation_validates_book_ownership(client, registered_user):
    requester_token = registered_user["access_token"]
    receiver = register_user(client, "bob", "bob@example.com")
    receiver_token = receiver["access_token"]
    requested_book = create_book(client, receiver_token).json()
    receiver_book = create_book(
        client, receiver_token, title="Wrong Owner Offer"
    ).json()

    response = request_exchange(
        client, requester_token, requested_book["id"], receiver_book["id"]
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You can only offer your own books"


def test_exchange_creation_rejects_own_book_and_missing_books(client, registered_user):
    token = registered_user["access_token"]
    own_book = create_book(client, token).json()

    own_book_response = request_exchange(client, token, own_book["id"], own_book["id"])
    missing_book_response = request_exchange(client, token, 999, own_book["id"])

    assert own_book_response.status_code == 400
    assert missing_book_response.status_code == 404


def test_only_receiver_can_update_exchange(client, registered_user):
    requester_token = registered_user["access_token"]
    receiver = register_user(client, "bob", "bob@example.com")
    requested_book = create_book(client, receiver["access_token"]).json()
    offered_book = create_book(client, requester_token).json()
    exchange = request_exchange(
        client, requester_token, requested_book["id"], offered_book["id"]
    ).json()

    response = client.patch(
        f"/exchanges/{exchange['id']}",
        json={"status": "rejected"},
        headers=auth_headers(requester_token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized"


def test_cannot_exchange_unavailable_books(client, registered_user):
    requester_token = registered_user["access_token"]
    receiver = register_user(client, "bob", "bob@example.com")
    requested_book = create_book(
        client, receiver["access_token"], title="Taken Book", available=False
    ).json()
    offered_book = create_book(client, requester_token, title="My Offer").json()

    response = request_exchange(
        client, requester_token, requested_book["id"], offered_book["id"]
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Requested book is not available"


def test_duplicate_pending_exchange_is_rejected(client, registered_user):
    requester_token = registered_user["access_token"]
    receiver = register_user(client, "bob", "bob@example.com")
    requested_book = create_book(client, receiver["access_token"]).json()
    offered_book = create_book(client, requester_token).json()

    first = request_exchange(
        client, requester_token, requested_book["id"], offered_book["id"]
    )
    duplicate = request_exchange(
        client, requester_token, requested_book["id"], offered_book["id"]
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Pending exchange already exists"


def test_cannot_move_decided_exchange_back_to_pending(client, registered_user):
    requester_token = registered_user["access_token"]
    receiver = register_user(client, "bob", "bob@example.com")
    requested_book = create_book(client, receiver["access_token"]).json()
    offered_book = create_book(client, requester_token).json()
    exchange = request_exchange(
        client, requester_token, requested_book["id"], offered_book["id"]
    ).json()

    client.patch(
        f"/exchanges/{exchange['id']}",
        json={"status": "rejected"},
        headers=auth_headers(receiver["access_token"]),
    )
    reverted = client.patch(
        f"/exchanges/{exchange['id']}",
        json={"status": "pending"},
        headers=auth_headers(receiver["access_token"]),
    )

    assert reverted.status_code == 409
    assert reverted.json()["detail"] == (
        "An exchange cannot return to pending once it has been decided."
    )


def test_accepting_rejects_competing_pending_exchanges(client, registered_user):
    alice_token = registered_user["access_token"]
    bob = register_user(client, "bob", "bob@example.com")
    carol = register_user(client, "carol", "carol@example.com")
    requested_book = create_book(client, bob["access_token"], title="Bob Book").json()
    alice_offer = create_book(client, alice_token, title="Alice Offer").json()
    carol_offer = create_book(
        client, carol["access_token"], title="Carol Offer"
    ).json()

    alice_exchange = request_exchange(
        client, alice_token, requested_book["id"], alice_offer["id"]
    ).json()
    carol_exchange = request_exchange(
        client, carol["access_token"], requested_book["id"], carol_offer["id"]
    ).json()

    accepted = client.patch(
        f"/exchanges/{alice_exchange['id']}",
        json={"status": "accepted"},
        headers=auth_headers(bob["access_token"]),
    )

    competing = client.get("/exchanges", headers=auth_headers(carol["access_token"]))

    assert accepted.status_code == 200
    assert competing.json()[0]["id"] == carol_exchange["id"]
    assert competing.json()[0]["status"] == "rejected"
    assert client.get(f"/books/{carol_offer['id']}").json()["available"] is True
