"""
contract.py — End-to-end contract harness for the Restaurant API.

Drives all 10 operationIds through the Flask test client in dependency order,
asserting correct HTTP status codes and response body field presence.

Steps performed automatically:
  1. Resets the database (calls reset_db.reset()).
  2. Exercises all 10 endpoints.
  3. Prints [PASS] or [FAIL] for each check.
  4. Exits 1 if any check fails.

Usage:
  python harness/contract.py
"""
import os
import sys

# Make harness/ and src/ importable
_HARNESS = os.path.dirname(os.path.abspath(__file__))
_BASE    = os.path.abspath(os.path.join(_HARNESS, ".."))

sys.path.insert(0, _HARNESS)
sys.path.insert(0, os.path.join(_BASE, "src"))

import reset_db

# Reset the database before the harness runs
reset_db.reset()
print()

# Import the Flask app (after DB is ready)
import app as flask_app

client = flask_app.app.test_client()

_PASS = 0
_FAIL = 0


def check(label, response, expected_status, required_fields=None):
    """Assert status code and optionally required top-level fields in the JSON body."""
    global _PASS, _FAIL
    data = response.get_json()
    ok   = (response.status_code == expected_status)

    if ok and required_fields:
        if isinstance(data, list):
            # For list responses, check the first element if the list is non-empty
            if data:
                ok = all(f in data[0] for f in required_fields)
        elif isinstance(data, dict):
            ok = all(f in data for f in required_fields)

    if ok:
        _PASS += 1
        print(f"  [PASS] {label}")
    else:
        _FAIL += 1
        print(f"  [FAIL] {label}")
        print(f"         expected status {expected_status}, got {response.status_code}")
        if required_fields and isinstance(data, dict):
            missing = [f for f in required_fields if f not in data]
            if missing:
                print(f"         missing fields: {missing}")

    return ok


# ── Menu ──────────────────────────────────────────────────────────────────────
print("[ listMenu / getMenuItem ]")
r = client.get("/menu")
check("listMenu returns 200", r, 200)
assert isinstance(r.get_json(), list), "listMenu: body must be a list"
print("  [PASS] listMenu returns a list")

r = client.get("/menu/1")
check("getMenuItem returns 200", r, 200,
      required_fields=["id", "name", "price_cents", "available", "category_id"])

r = client.get("/menu/9999")
check("getMenuItem 404 for unknown id", r, 404, required_fields=["error"])

# ── Customers ─────────────────────────────────────────────────────────────────
print()
print("[ createCustomer ]")
r = client.post("/customers", json={"name": "Contract User", "email": "contract@harness.test"})
check("createCustomer returns 201", r, 201,
      required_fields=["id", "name", "email", "created_at"])
customer_id = r.get_json().get("id")

r = client.post("/customers", json={"name": "Dup", "email": "contract@harness.test"})
check("createCustomer duplicate email returns 409", r, 409, required_fields=["error"])

r = client.post("/customers", json={"email": "missing@name.test"})
check("createCustomer missing name returns 400", r, 400, required_fields=["error"])

r = client.post("/customers", json={"name": "No Email"})
check("createCustomer missing email returns 400", r, 400, required_fields=["error"])

# ── Dining Tables ─────────────────────────────────────────────────────────────
print()
print("[ listDiningTables ]")
r = client.get("/tables")
check("listDiningTables returns 200", r, 200)
tables = r.get_json()
assert isinstance(tables, list) and len(tables) > 0, "listDiningTables must return non-empty list"
print("  [PASS] listDiningTables returns non-empty list")
table_id    = tables[0]["id"]
table_seats = tables[0]["seats"]

# ── Reservations ──────────────────────────────────────────────────────────────
print()
print("[ createReservation / getReservation ]")
r = client.post("/reservations", json={
    "customer_id":      customer_id,
    "table_id":         table_id,
    "party_size":       1,
    "reservation_time": "2025-12-01T19:00:00Z",
})
check("createReservation returns 201", r, 201,
      required_fields=["id", "customer_id", "table_id", "party_size",
                       "reservation_time", "status", "created_at"])
assert r.get_json().get("status") == "active", "createReservation: status must be 'active'"
print("  [PASS] createReservation status is 'active'")
res_id = r.get_json().get("id")

# Double-booking
r = client.post("/reservations", json={
    "customer_id":      customer_id,
    "table_id":         table_id,
    "party_size":       1,
    "reservation_time": "2025-12-01T19:00:00Z",
})
check("createReservation double-booking returns 409", r, 409, required_fields=["error"])

# party_size exceeds seats
r = client.post("/reservations", json={
    "customer_id":      customer_id,
    "table_id":         table_id,
    "party_size":       table_seats + 1,
    "reservation_time": "2025-12-02T19:00:00Z",
})
check("createReservation party_size > seats returns 400", r, 400, required_fields=["error"])

# party_size = 0
r = client.post("/reservations", json={
    "customer_id":      customer_id,
    "table_id":         table_id,
    "party_size":       0,
    "reservation_time": "2025-12-03T19:00:00Z",
})
check("createReservation party_size=0 returns 400", r, 400, required_fields=["error"])

# Unknown customer
r = client.post("/reservations", json={
    "customer_id":      9999,
    "table_id":         table_id,
    "party_size":       1,
    "reservation_time": "2025-12-10T19:00:00Z",
})
check("createReservation unknown customer returns 404", r, 404, required_fields=["error"])

r = client.get(f"/reservations/{res_id}")
check("getReservation returns 200", r, 200,
      required_fields=["id", "customer_id", "table_id", "party_size",
                       "reservation_time", "status"])
assert r.get_json().get("id") == res_id, "getReservation: id must match"
print("  [PASS] getReservation id matches")

r = client.get("/reservations/9999")
check("getReservation 404 for unknown id", r, 404, required_fields=["error"])

# ── Orders ────────────────────────────────────────────────────────────────────
print()
print("[ createOrder / getOrder ]")
r = client.post("/orders", json={
    "customer_id": customer_id,
    "items": [
        {"menu_item_id": 1, "quantity": 2},   # Garlic Bread: 499 * 2 = 998
        {"menu_item_id": 7, "quantity": 1},   # Still Water:  250 * 1 = 250
    ],
})
check("createOrder returns 201", r, 201,
      required_fields=["id", "customer_id", "status", "items", "total_cents", "created_at"])
data = r.get_json()
assert data.get("status") == "NEW", "createOrder status is NEW"
assert data.get("total_cents") == 1248, "createOrder total_cents correct"
assert len(data.get("items", [])) == 2, "createOrder items non-empty"
print("  [PASS] createOrder status=NEW, total_cents=1248, 2 items")
order_id = data.get("id")

# Verify line item fields
item0 = data["items"][0] if data.get("items") else {}
for field in ["unit_price_cents", "line_total_cents", "menu_item_id", "quantity"]:
    assert field in item0, f"createOrder item missing field: {field}"
print("  [PASS] createOrder item has unit_price_cents, line_total_cents, menu_item_id, quantity")

# Unavailable item (id=5, Mushroom Risotto)
r = client.post("/orders", json={
    "customer_id": customer_id,
    "items": [{"menu_item_id": 5, "quantity": 1}],
})
check("createOrder unavailable item returns 422", r, 422, required_fields=["error"])

# Unknown menu item
r = client.post("/orders", json={
    "customer_id": customer_id,
    "items": [{"menu_item_id": 9999, "quantity": 1}],
})
check("createOrder unknown item returns 404", r, 404, required_fields=["error"])

# Unknown customer
r = client.post("/orders", json={
    "customer_id": 9999,
    "items": [{"menu_item_id": 1, "quantity": 1}],
})
check("createOrder unknown customer returns 404", r, 404, required_fields=["error"])

# Empty items
r = client.post("/orders", json={"customer_id": customer_id, "items": []})
check("createOrder empty items returns 400", r, 400, required_fields=["error"])

r = client.get(f"/orders/{order_id}")
check("getOrder returns 200", r, 200,
      required_fields=["id", "customer_id", "status", "items", "total_cents"])
assert all("line_total_cents" in i for i in r.get_json().get("items", [])), \
    "getOrder: all items must have line_total_cents"
print("  [PASS] getOrder line_total_cents preserved")

r = client.get("/orders/9999")
check("getOrder 404 for unknown id", r, 404, required_fields=["error"])

# ── Order status FSM ──────────────────────────────────────────────────────────
print()
print("[ updateOrderStatus — FSM transitions ]")

def fresh_order():
    """Create a new order and return its id."""
    resp = client.post("/orders", json={
        "customer_id": customer_id,
        "items": [{"menu_item_id": 1, "quantity": 1}],
    })
    return resp.get_json()["id"]

# NEW -> PREPARING
oid = fresh_order()
r = client.patch(f"/orders/{oid}/status", json={"status": "PREPARING"})
check("NEW -> PREPARING returns 200", r, 200)
assert r.get_json().get("status") == "PREPARING", "status should be PREPARING"
print("  [PASS] NEW -> PREPARING status updated")

# PREPARING -> READY
r = client.patch(f"/orders/{oid}/status", json={"status": "READY"})
check("PREPARING -> READY returns 200", r, 200)

# READY -> COMPLETED
r = client.patch(f"/orders/{oid}/status", json={"status": "COMPLETED"})
check("READY -> COMPLETED returns 200", r, 200)

# COMPLETED is terminal
r = client.patch(f"/orders/{oid}/status", json={"status": "CANCELLED"})
check("COMPLETED -> CANCELLED returns 422 (terminal)", r, 422, required_fields=["error"])

# NEW -> CANCELLED
oid2 = fresh_order()
r = client.patch(f"/orders/{oid2}/status", json={"status": "CANCELLED"})
check("NEW -> CANCELLED returns 200", r, 200)

# CANCELLED is terminal
r = client.patch(f"/orders/{oid2}/status", json={"status": "PREPARING"})
check("CANCELLED -> PREPARING returns 422 (terminal)", r, 422, required_fields=["error"])

# Invalid skip (NEW -> COMPLETED)
oid3 = fresh_order()
r = client.patch(f"/orders/{oid3}/status", json={"status": "COMPLETED"})
check("NEW -> COMPLETED returns 422 (invalid skip)", r, 422, required_fields=["error"])

# Invalid status value
r = client.patch(f"/orders/{oid3}/status", json={"status": "SHIPPED"})
check("invalid status value returns 400", r, 400, required_fields=["error"])

# Order not found
r = client.patch("/orders/9999/status", json={"status": "PREPARING"})
check("updateOrderStatus 404 for unknown id", r, 404, required_fields=["error"])

# ── listCustomerOrders ────────────────────────────────────────────────────────
print()
print("[ listCustomerOrders ]")
r = client.get(f"/customers/{customer_id}/orders")
check("listCustomerOrders returns 200", r, 200)
orders = r.get_json()
assert isinstance(orders, list),  "listCustomerOrders must return a list"
assert len(orders) > 0,           "listCustomerOrders must be non-empty"
assert "items" in orders[0],      "listCustomerOrders orders must have items"
print("  [PASS] listCustomerOrders list, non-empty, items present")

r = client.get("/customers/9999/orders")
check("listCustomerOrders 404 for unknown customer", r, 404, required_fields=["error"])

# ── Summary ───────────────────────────────────────────────────────────────────
total = _PASS + _FAIL
print()
print("=" * 48)
print(f"  CONTRACT RESULTS: {_PASS}/{total} checks passed")
print("=" * 48)

if _FAIL:
    sys.exit(1)
