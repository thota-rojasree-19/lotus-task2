"""
test_orders.py — pytest tests for:
  createOrder       POST /orders
  getOrder          GET  /orders/{id}
  updateOrderStatus PATCH /orders/{id}/status
  listCustomerOrders GET  /customers/{id}/orders

Assumes the database has been seeded by run-tests.sh before pytest runs.
Uses a distinct customer email to avoid UNIQUE conflicts with other test modules.

Seed data reference (from seed.sql):
  menu item id=1  Garlic Bread       price_cents=499  available=1
  menu item id=5  Mushroom Risotto   price_cents=1350 available=0  (unavailable)
  menu item id=7  Still Water        price_cents=250  available=1
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from app import app as flask_app
import db  # src/ is on sys.path; used to mutate DB state in the preservation test

_UNAVAILABLE_ITEM_ID = 5   # Mushroom Risotto, available=0 in seed data


@pytest.fixture(scope="module")
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture(scope="module")
def customer_id(client):
    r = client.post("/customers", json={
        "name":  "Orders Tester",
        "email": "orders_tester@example.test",
    })
    assert r.status_code == 201
    return r.get_json()["id"]


@pytest.fixture(scope="module")
def base_order_id(client, customer_id):
    """A reference order with two items used by getOrder / listCustomerOrders tests."""
    r = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [
            {"menu_item_id": 1, "quantity": 2},  # 499 * 2 = 998
            {"menu_item_id": 7, "quantity": 1},  # 250 * 1 = 250
        ],
    })
    assert r.status_code == 201
    return r.get_json()["id"]


def _fresh_order(client, customer_id, menu_item_id=1, quantity=1):
    """Helper — create a new single-item order and return its id."""
    r = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [{"menu_item_id": menu_item_id, "quantity": quantity}],
    })
    assert r.status_code == 201
    return r.get_json()["id"]


# ── createOrder ───────────────────────────────────────────────────────────────

def test_create_order_returns_201(client, customer_id):
    r = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [{"menu_item_id": 1, "quantity": 1}],
    })
    assert r.status_code == 201


def test_create_order_initial_status_is_new(client, customer_id):
    r = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [{"menu_item_id": 1, "quantity": 1}],
    })
    assert r.get_json()["status"] == "NEW"


def test_create_order_has_required_fields(client, customer_id):
    r = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [{"menu_item_id": 1, "quantity": 1}],
    })
    data = r.get_json()
    for field in ["id", "customer_id", "status", "items", "total_cents", "created_at"]:
        assert field in data


def test_create_order_total_cents_calculated_by_backend(client, customer_id):
    # Garlic Bread (id=1): price_cents=499, quantity=2 -> total=998
    r = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [{"menu_item_id": 1, "quantity": 2}],
    })
    assert r.get_json()["total_cents"] == 998


def test_create_order_total_cents_multiline(client, customer_id):
    # id=1: 499*2=998, id=7: 250*1=250 -> total=1248
    r = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [
            {"menu_item_id": 1, "quantity": 2},
            {"menu_item_id": 7, "quantity": 1},
        ],
    })
    assert r.get_json()["total_cents"] == 1248


def test_create_order_items_have_unit_price_cents(client, customer_id):
    r = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [{"menu_item_id": 1, "quantity": 1}],
    })
    item = r.get_json()["items"][0]
    assert "unit_price_cents" in item
    assert isinstance(item["unit_price_cents"], int)
    assert item["unit_price_cents"] == 499   # Garlic Bread seed price


def test_create_order_items_have_line_total_cents(client, customer_id):
    r = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [{"menu_item_id": 1, "quantity": 3}],
    })
    item = r.get_json()["items"][0]
    assert "line_total_cents" in item
    assert item["line_total_cents"] == 499 * 3


def test_create_order_items_have_sow_fields(client, customer_id):
    r = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [{"menu_item_id": 1, "quantity": 1}],
    })
    item = r.get_json()["items"][0]
    for field in ["id", "order_id", "menu_item_id", "quantity",
                  "unit_price_cents", "line_total_cents"]:
        assert field in item


def test_create_order_unavailable_item_returns_422(client, customer_id):
    r = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [{"menu_item_id": _UNAVAILABLE_ITEM_ID, "quantity": 1}],
    })
    assert r.status_code == 422
    assert "error" in r.get_json()


def test_create_order_unknown_item_returns_404(client, customer_id):
    r = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [{"menu_item_id": 9999, "quantity": 1}],
    })
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_create_order_unknown_customer_returns_404(client):
    r = client.post("/orders", json={
        "customer_id": 9999,
        "items": [{"menu_item_id": 1, "quantity": 1}],
    })
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_create_order_empty_items_returns_400(client, customer_id):
    r = client.post("/orders", json={"customer_id": customer_id, "items": []})
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_create_order_missing_customer_id_returns_400(client):
    r = client.post("/orders", json={"items": [{"menu_item_id": 1, "quantity": 1}]})
    assert r.status_code == 400
    assert "error" in r.get_json()


# ── getOrder ──────────────────────────────────────────────────────────────────

def test_get_order_returns_200(client, base_order_id):
    assert client.get(f"/orders/{base_order_id}").status_code == 200


def test_get_order_has_required_fields(client, base_order_id):
    data = client.get(f"/orders/{base_order_id}").get_json()
    for field in ["id", "customer_id", "status", "items", "total_cents", "created_at"]:
        assert field in data


def test_get_order_items_preserve_unit_price_cents(client, base_order_id):
    data = client.get(f"/orders/{base_order_id}").get_json()
    for item in data["items"]:
        assert "unit_price_cents" in item
        assert isinstance(item["unit_price_cents"], int)


def test_get_order_items_have_line_total_cents(client, base_order_id):
    data = client.get(f"/orders/{base_order_id}").get_json()
    for item in data["items"]:
        assert "line_total_cents" in item
        assert item["line_total_cents"] == item["unit_price_cents"] * item["quantity"]


def test_get_order_not_found_returns_404(client):
    r = client.get("/orders/9999")
    assert r.status_code == 404
    assert "error" in r.get_json()


# ── updateOrderStatus — state machine ────────────────────────────────────────

def test_update_status_new_to_preparing(client, customer_id):
    oid = _fresh_order(client, customer_id)
    r = client.patch(f"/orders/{oid}/status", json={"status": "PREPARING"})
    assert r.status_code == 200
    assert r.get_json()["status"] == "PREPARING"


def test_update_status_new_to_cancelled(client, customer_id):
    oid = _fresh_order(client, customer_id)
    r = client.patch(f"/orders/{oid}/status", json={"status": "CANCELLED"})
    assert r.status_code == 200
    assert r.get_json()["status"] == "CANCELLED"


def test_update_status_preparing_to_ready(client, customer_id):
    oid = _fresh_order(client, customer_id)
    client.patch(f"/orders/{oid}/status", json={"status": "PREPARING"})
    r = client.patch(f"/orders/{oid}/status", json={"status": "READY"})
    assert r.status_code == 200
    assert r.get_json()["status"] == "READY"


def test_update_status_ready_to_completed(client, customer_id):
    oid = _fresh_order(client, customer_id)
    client.patch(f"/orders/{oid}/status", json={"status": "PREPARING"})
    client.patch(f"/orders/{oid}/status", json={"status": "READY"})
    r = client.patch(f"/orders/{oid}/status", json={"status": "COMPLETED"})
    assert r.status_code == 200
    assert r.get_json()["status"] == "COMPLETED"


def test_update_status_invalid_skip_new_to_completed_returns_422(client, customer_id):
    oid = _fresh_order(client, customer_id)
    r = client.patch(f"/orders/{oid}/status", json={"status": "COMPLETED"})
    assert r.status_code == 422
    assert "error" in r.get_json()


def test_update_status_completed_is_terminal(client, customer_id):
    oid = _fresh_order(client, customer_id)
    client.patch(f"/orders/{oid}/status", json={"status": "PREPARING"})
    client.patch(f"/orders/{oid}/status", json={"status": "READY"})
    client.patch(f"/orders/{oid}/status", json={"status": "COMPLETED"})
    r = client.patch(f"/orders/{oid}/status", json={"status": "CANCELLED"})
    assert r.status_code == 422
    assert "error" in r.get_json()


def test_update_status_cancelled_is_terminal(client, customer_id):
    oid = _fresh_order(client, customer_id)
    client.patch(f"/orders/{oid}/status", json={"status": "CANCELLED"})
    r = client.patch(f"/orders/{oid}/status", json={"status": "PREPARING"})
    assert r.status_code == 422
    assert "error" in r.get_json()


def test_update_status_invalid_value_returns_400(client, customer_id):
    oid = _fresh_order(client, customer_id)
    r = client.patch(f"/orders/{oid}/status", json={"status": "SHIPPED"})
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_update_status_not_found_returns_404(client):
    r = client.patch("/orders/9999/status", json={"status": "PREPARING"})
    assert r.status_code == 404
    assert "error" in r.get_json()


# ── listCustomerOrders ────────────────────────────────────────────────────────

def test_list_customer_orders_returns_200(client, customer_id):
    assert client.get(f"/customers/{customer_id}/orders").status_code == 200


def test_list_customer_orders_returns_list(client, customer_id):
    assert isinstance(client.get(f"/customers/{customer_id}/orders").get_json(), list)


def test_list_customer_orders_is_non_empty(client, customer_id):
    data = client.get(f"/customers/{customer_id}/orders").get_json()
    assert len(data) > 0


def test_list_customer_orders_items_have_required_fields(client, customer_id):
    orders = client.get(f"/customers/{customer_id}/orders").get_json()
    for order in orders:
        assert "id"          in order
        assert "customer_id" in order
        assert "status"      in order
        assert "total_cents" in order
        assert "items"       in order


def test_list_customer_orders_line_items_have_sow_fields(client, customer_id):
    orders = client.get(f"/customers/{customer_id}/orders").get_json()
    for order in orders:
        for item in order["items"]:
            for field in ["id", "order_id", "menu_item_id", "quantity",
                          "unit_price_cents", "line_total_cents"]:
                assert field in item


def test_list_customer_orders_unknown_customer_returns_404(client):
    r = client.get("/customers/9999/orders")
    assert r.status_code == 404
    assert "error" in r.get_json()


# ── Historical price preservation (SOW requirement) ───────────────────────────

def test_historical_unit_price_preserved_after_menu_price_change(client, customer_id):
    """SOW requirement: order_items.unit_price_cents and line_total_cents must
    retain the values they had at order creation time, even if the menu item's
    current price_cents is changed afterwards.

    Flow:
      1. Create an order.  Record original unit_price_cents / line_total_cents.
      2. Directly UPDATE menu_items.price_cents in the test database.
      3. Verify the menu item now reports the new price via GET /menu/{id}.
      4. GET the existing order via the HTTP API.
      5. Assert the stored unit_price_cents and line_total_cents are unchanged.
      6. Assert orders.total_cents is unchanged.
      7. Restore the original price so subsequent tests are not affected.
    """
    ITEM_ID = 1          # Garlic Bread, price_cents=499 in seed data
    QUANTITY = 2
    ORIGINAL_PRICE = 499

    # Step 1 — Create a fresh order and capture the stored prices
    r = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [{"menu_item_id": ITEM_ID, "quantity": QUANTITY}],
    })
    assert r.status_code == 201
    created = r.get_json()
    order_id             = created["id"]
    original_unit_price  = created["items"][0]["unit_price_cents"]
    original_line_total  = created["items"][0]["line_total_cents"]
    original_total_cents = created["total_cents"]

    assert original_unit_price == ORIGINAL_PRICE,          "seed price mismatch"
    assert original_line_total == ORIGINAL_PRICE * QUANTITY, "line_total seed mismatch"

    # Step 2 — Mutate the menu item price directly in the DB (simulates a
    #           price change that happens after the order was placed)
    new_price = ORIGINAL_PRICE + 200  # 699 cents
    with db.transaction() as conn:
        conn.execute(
            "UPDATE menu_items SET price_cents = ? WHERE id = ?",
            (new_price, ITEM_ID),
        )

    try:
        # Step 3 — Confirm the menu item now advertises the new price
        r_menu = client.get(f"/menu/{ITEM_ID}")
        assert r_menu.status_code == 200
        assert r_menu.get_json()["price_cents"] == new_price, \
            "menu item should reflect the updated price"

        # Step 4 — GET the existing order through the HTTP API
        r_order = client.get(f"/orders/{order_id}")
        assert r_order.status_code == 200
        order = r_order.get_json()

        # Step 5 — The stored unit_price_cents must equal the ORIGINAL value
        item = order["items"][0]
        assert item["unit_price_cents"] == original_unit_price, (
            f"Historical unit_price_cents must be preserved: "
            f"expected {original_unit_price}, got {item['unit_price_cents']}"
        )
        assert item["line_total_cents"] == original_line_total, (
            f"Historical line_total_cents must be preserved: "
            f"expected {original_line_total}, got {item['line_total_cents']}"
        )

        # Step 6 — The order total must be unchanged
        assert order["total_cents"] == original_total_cents, (
            f"orders.total_cents must be preserved: "
            f"expected {original_total_cents}, got {order['total_cents']}"
        )

    finally:
        # Step 7 — Restore original price regardless of test outcome
        with db.transaction() as conn:
            conn.execute(
                "UPDATE menu_items SET price_cents = ? WHERE id = ?",
                (ORIGINAL_PRICE, ITEM_ID),
            )
