"""
test_reservations.py — pytest tests for:
  createCustomer   POST /customers
  listDiningTables GET /tables
  createReservation POST /reservations
  getReservation   GET /reservations/{id}

Assumes the database has been seeded by run-tests.sh before pytest runs.
Uses distinct emails to avoid UNIQUE conflicts with other test modules.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from app import app as flask_app


@pytest.fixture(scope="module")
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture(scope="module")
def customer_id(client):
    """Create a customer for use across reservation tests."""
    r = client.post("/customers", json={
        "name":  "Reservation Tester",
        "email": "res_tester@example.test",
    })
    assert r.status_code == 201
    return r.get_json()["id"]


@pytest.fixture(scope="module")
def first_table(client):
    """Return the first table from the seeded data."""
    r = client.get("/tables")
    assert r.status_code == 200
    tables = r.get_json()
    assert len(tables) > 0
    return tables[0]


# ── createCustomer ────────────────────────────────────────────────────────────

def test_create_customer_returns_201(client):
    r = client.post("/customers", json={
        "name": "Alice Unique", "email": "alice_res_unique@example.test"
    })
    assert r.status_code == 201


def test_create_customer_has_id_and_created_at(client):
    r = client.post("/customers", json={
        "name": "Bob Unique", "email": "bob_res_unique@example.test"
    })
    data = r.get_json()
    assert "id"         in data
    assert "created_at" in data
    assert isinstance(data["id"], int)


def test_create_customer_duplicate_email_returns_409(client):
    email = "dup_res@example.test"
    r1 = client.post("/customers", json={"name": "First",  "email": email})
    assert r1.status_code == 201
    r2 = client.post("/customers", json={"name": "Second", "email": email})
    assert r2.status_code == 409
    assert "error" in r2.get_json()


def test_create_customer_missing_name_returns_400(client):
    r = client.post("/customers", json={"email": "noname_res@example.test"})
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_create_customer_missing_email_returns_400(client):
    r = client.post("/customers", json={"name": "No Email Res"})
    assert r.status_code == 400
    assert "error" in r.get_json()


# ── listDiningTables ──────────────────────────────────────────────────────────

def test_list_tables_returns_200(client):
    assert client.get("/tables").status_code == 200


def test_list_tables_returns_list(client):
    assert isinstance(client.get("/tables").get_json(), list)


def test_list_tables_items_have_required_fields(client):
    tables = client.get("/tables").get_json()
    assert len(tables) > 0
    for t in tables:
        assert "id"           in t
        assert "table_number" in t
        assert "seats"        in t
        assert "status"       in t


# ── createReservation ─────────────────────────────────────────────────────────

def test_create_reservation_returns_201(client, customer_id, first_table):
    r = client.post("/reservations", json={
        "customer_id":      customer_id,
        "table_id":         first_table["id"],
        "party_size":       1,
        "reservation_time": "2025-11-01T18:00:00Z",
    })
    assert r.status_code == 201


def test_create_reservation_has_required_fields(client, customer_id, first_table):
    r = client.post("/reservations", json={
        "customer_id":      customer_id,
        "table_id":         first_table["id"],
        "party_size":       1,
        "reservation_time": "2025-11-02T18:00:00Z",
    })
    data = r.get_json()
    for field in ["id", "customer_id", "table_id", "party_size",
                  "reservation_time", "status", "created_at"]:
        assert field in data


def test_create_reservation_initial_status_is_active(client, customer_id, first_table):
    r = client.post("/reservations", json={
        "customer_id":      customer_id,
        "table_id":         first_table["id"],
        "party_size":       1,
        "reservation_time": "2025-11-03T18:00:00Z",
    })
    assert r.get_json()["status"] == "active"


def test_create_reservation_party_too_large_returns_400(client, customer_id, first_table):
    r = client.post("/reservations", json={
        "customer_id":      customer_id,
        "table_id":         first_table["id"],
        "party_size":       first_table["seats"] + 1,
        "reservation_time": "2025-11-10T18:00:00Z",
    })
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_create_reservation_party_size_zero_returns_400(client, customer_id, first_table):
    r = client.post("/reservations", json={
        "customer_id":      customer_id,
        "table_id":         first_table["id"],
        "party_size":       0,
        "reservation_time": "2025-11-11T18:00:00Z",
    })
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_create_reservation_double_booking_returns_409(client, customer_id, first_table):
    slot = "2025-11-20T20:00:00Z"
    r1 = client.post("/reservations", json={
        "customer_id":      customer_id,
        "table_id":         first_table["id"],
        "party_size":       1,
        "reservation_time": slot,
    })
    assert r1.status_code == 201

    r2 = client.post("/reservations", json={
        "customer_id":      customer_id,
        "table_id":         first_table["id"],
        "party_size":       1,
        "reservation_time": slot,
    })
    assert r2.status_code == 409
    assert "error" in r2.get_json()


def test_create_reservation_unknown_customer_returns_404(client, first_table):
    r = client.post("/reservations", json={
        "customer_id":      9999,
        "table_id":         first_table["id"],
        "party_size":       1,
        "reservation_time": "2025-12-01T18:00:00Z",
    })
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_create_reservation_unknown_table_returns_404(client, customer_id):
    r = client.post("/reservations", json={
        "customer_id":      customer_id,
        "table_id":         9999,
        "party_size":       1,
        "reservation_time": "2025-12-02T18:00:00Z",
    })
    assert r.status_code == 404
    assert "error" in r.get_json()


# ── getReservation ────────────────────────────────────────────────────────────

def test_get_reservation_returns_200(client, customer_id, first_table):
    r_create = client.post("/reservations", json={
        "customer_id":      customer_id,
        "table_id":         first_table["id"],
        "party_size":       1,
        "reservation_time": "2025-12-15T18:00:00Z",
    })
    res_id = r_create.get_json()["id"]
    r = client.get(f"/reservations/{res_id}")
    assert r.status_code == 200


def test_get_reservation_has_correct_data(client, customer_id, first_table):
    r_create = client.post("/reservations", json={
        "customer_id":      customer_id,
        "table_id":         first_table["id"],
        "party_size":       1,
        "reservation_time": "2025-12-16T18:00:00Z",
    })
    res_id = r_create.get_json()["id"]
    data = client.get(f"/reservations/{res_id}").get_json()
    assert data["id"]          == res_id
    assert data["customer_id"] == customer_id
    assert data["table_id"]    == first_table["id"]
    assert data["status"]      == "active"


def test_get_reservation_not_found_returns_404(client):
    r = client.get("/reservations/9999")
    assert r.status_code == 404
    assert "error" in r.get_json()
