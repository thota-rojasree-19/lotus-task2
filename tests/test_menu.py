"""
test_menu.py — pytest tests for listMenu (GET /menu) and getMenuItem (GET /menu/{id}).

Assumes the database has been seeded by run-tests.sh before pytest runs.
Uses the Flask test client (no running server required).
"""
import os
import sys

# Make src/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from app import app as flask_app


@pytest.fixture(scope="module")
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ── listMenu — GET /menu ──────────────────────────────────────────────────────

def test_list_menu_returns_200(client):
    r = client.get("/menu")
    assert r.status_code == 200


def test_list_menu_returns_list(client):
    r = client.get("/menu")
    assert isinstance(r.get_json(), list)


def test_list_menu_is_non_empty(client):
    r = client.get("/menu")
    assert len(r.get_json()) > 0


def test_list_menu_items_have_required_fields(client):
    r = client.get("/menu")
    for item in r.get_json():
        assert "id"            in item
        assert "category_id"   in item
        assert "category_name" in item
        assert "name"          in item
        assert "price_cents"   in item
        assert "available"     in item


def test_list_menu_price_cents_is_non_negative_integer(client):
    r = client.get("/menu")
    for item in r.get_json():
        assert isinstance(item["price_cents"], int)
        assert item["price_cents"] >= 0


def test_list_menu_available_is_boolean(client):
    r = client.get("/menu")
    for item in r.get_json():
        assert isinstance(item["available"], bool)


# ── getMenuItem — GET /menu/{id} ──────────────────────────────────────────────

def test_get_menu_item_returns_200(client):
    r = client.get("/menu/1")
    assert r.status_code == 200


def test_get_menu_item_has_required_fields(client):
    r = client.get("/menu/1")
    data = r.get_json()
    assert "id"            in data
    assert "category_id"   in data
    assert "category_name" in data
    assert "name"          in data
    assert "price_cents"   in data
    assert "available"     in data
    assert data["id"] == 1


def test_get_menu_item_not_found_returns_404(client):
    r = client.get("/menu/9999")
    assert r.status_code == 404


def test_get_menu_item_not_found_has_error_field(client):
    r = client.get("/menu/9999")
    assert "error" in r.get_json()
