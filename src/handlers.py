"""
handlers.py — One handler function per operationId defined in openapi.yaml.

Each function returns a (body, http_status_code) tuple.
app.py wraps the result in jsonify() before returning it to the client.

Business rules applied here:
- Prices always read from the DB; never trusted from the client.
- line_total_cents = unit_price_cents * quantity (calculated at INSERT time).
- total_cents = SUM(line_total_cents) across all order_items.
- Historical unit_price_cents and line_total_cents are never updated.
- Order status transitions follow the SOW state machine.
- party_size must be >= 1 and must not exceed the table's seat count.
- The same table cannot have two active reservations at the same reservation_time.
"""
import sqlite3

from flask import request

import db


# ── Internal helpers ──────────────────────────────────────────────────────────

def _err(msg, code):
    """Return a uniform error response tuple."""
    return {"error": msg}, code


def _fetch_order(conn, order_id):
    """Return a full order dict including its line items from an open connection."""
    row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:
        return None
    order = dict(row)
    items = conn.execute(
        "SELECT * FROM order_items WHERE order_id = ?", (order_id,)
    ).fetchall()
    order["items"] = [dict(i) for i in items]
    return order


# ── Menu ──────────────────────────────────────────────────────────────────────

def list_menu():
    """operationId: listMenu — GET /menu"""
    rows = db.query_all(
        """
        SELECT mi.id,
               mi.category_id,
               mc.name  AS category_name,
               mi.name,
               mi.description,
               mi.price_cents,
               mi.available
        FROM   menu_items     mi
        JOIN   menu_categories mc ON mc.id = mi.category_id
        ORDER  BY mi.id
        """
    )
    for r in rows:
        r["available"] = bool(r["available"])
    return rows, 200


def get_menu_item(item_id):
    """operationId: getMenuItem — GET /menu/{id}"""
    row = db.query_one(
        """
        SELECT mi.id,
               mi.category_id,
               mc.name  AS category_name,
               mi.name,
               mi.description,
               mi.price_cents,
               mi.available
        FROM   menu_items     mi
        JOIN   menu_categories mc ON mc.id = mi.category_id
        WHERE  mi.id = ?
        """,
        (item_id,),
    )
    if row is None:
        return _err("Menu item not found", 404)
    row["available"] = bool(row["available"])
    return row, 200


# ── Customers ─────────────────────────────────────────────────────────────────

def create_customer():
    """operationId: createCustomer — POST /customers"""
    body = request.get_json(silent=True) or {}

    name  = (body.get("name")  or "").strip()
    email = (body.get("email") or "").strip()
    phone = body.get("phone")

    if not name:
        return _err("name is required", 400)
    if not email:
        return _err("email is required", 400)

    try:
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO customers (name, email, phone) VALUES (?, ?, ?)",
                (name, email, phone),
            )
            row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            row = conn.execute(
                "SELECT * FROM customers WHERE id = ?", (row_id,)
            ).fetchone()
            customer = dict(row)
    except sqlite3.IntegrityError:
        return _err("A customer with this email already exists", 409)

    return customer, 201


# ── Dining Tables ─────────────────────────────────────────────────────────────

def list_dining_tables():
    """operationId: listDiningTables — GET /tables"""
    rows = db.query_all("SELECT * FROM dining_tables ORDER BY id")
    return rows, 200


# ── Reservations ──────────────────────────────────────────────────────────────

def create_reservation():
    """operationId: createReservation — POST /reservations"""
    body = request.get_json(silent=True) or {}

    customer_id      = body.get("customer_id")
    table_id         = body.get("table_id")
    party_size       = body.get("party_size")
    reservation_time = body.get("reservation_time")

    # Required fields
    if any(v is None for v in [customer_id, table_id, party_size, reservation_time]):
        return _err(
            "customer_id, table_id, party_size, and reservation_time are required", 400
        )

    # party_size type and minimum
    if not isinstance(party_size, int) or party_size < 1:
        return _err("party_size must be an integer >= 1", 400)

    # Customer must exist
    if db.query_one("SELECT id FROM customers WHERE id = ?", (customer_id,)) is None:
        return _err("Customer not found", 404)

    # Table must exist
    table = db.query_one("SELECT * FROM dining_tables WHERE id = ?", (table_id,))
    if table is None:
        return _err("Dining table not found", 404)

    # party_size must not exceed table seat count
    if party_size > table["seats"]:
        return _err(
            f"party_size ({party_size}) exceeds table seat count ({table['seats']})", 400
        )

    # Double-booking: same table, same time, status = active
    conflict = db.query_one(
        """
        SELECT id FROM reservations
        WHERE  table_id = ? AND reservation_time = ? AND status = 'active'
        """,
        (table_id, reservation_time),
    )
    if conflict:
        return _err("Table already has an active reservation at this time", 409)

    with db.transaction() as conn:
        conn.execute(
            """
            INSERT INTO reservations
                   (customer_id, table_id, party_size, reservation_time)
            VALUES (?, ?, ?, ?)
            """,
            (customer_id, table_id, party_size, reservation_time),
        )
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        row = conn.execute(
            "SELECT * FROM reservations WHERE id = ?", (row_id,)
        ).fetchone()
        reservation = dict(row)

    return reservation, 201


def get_reservation(reservation_id):
    """operationId: getReservation — GET /reservations/{id}"""
    row = db.query_one(
        "SELECT * FROM reservations WHERE id = ?", (reservation_id,)
    )
    if row is None:
        return _err("Reservation not found", 404)
    return row, 200


# ── Orders ────────────────────────────────────────────────────────────────────

def create_order():
    """operationId: createOrder — POST /orders

    Prices are read exclusively from menu_items in the database.
    line_total_cents = unit_price_cents * quantity (computed here, stored in DB).
    total_cents = SUM(line_total_cents) (computed here, stored in orders row).
    The entire INSERT (orders + order_items) is atomic in one transaction.
    """
    body = request.get_json(silent=True) or {}

    customer_id = body.get("customer_id")
    items       = body.get("items")

    if customer_id is None:
        return _err("customer_id is required", 400)
    if not items or not isinstance(items, list):
        return _err("items must be a non-empty array", 400)

    # Customer must exist
    if db.query_one("SELECT id FROM customers WHERE id = ?", (customer_id,)) is None:
        return _err("Customer not found", 404)

    # Validate and resolve each line item against the DB
    resolved = []
    for entry in items:
        mid = entry.get("menu_item_id")
        qty = entry.get("quantity")

        if mid is None or qty is None:
            return _err("Each item requires menu_item_id and quantity", 400)
        if not isinstance(qty, int) or qty < 1:
            return _err("quantity must be an integer >= 1", 400)

        menu_item = db.query_one("SELECT * FROM menu_items WHERE id = ?", (mid,))
        if menu_item is None:
            return _err(f"Menu item {mid} not found", 404)
        if not menu_item["available"]:
            return _err(
                f"Menu item '{menu_item['name']}' (id={mid}) is not available", 422
            )

        unit_price = menu_item["price_cents"]
        resolved.append({
            "menu_item_id":    mid,
            "quantity":        qty,
            "unit_price_cents": unit_price,
            "line_total_cents": unit_price * qty,
        })

    total_cents = sum(r["line_total_cents"] for r in resolved)

    with db.transaction() as conn:
        conn.execute(
            "INSERT INTO orders (customer_id, total_cents) VALUES (?, ?)",
            (customer_id, total_cents),
        )
        order_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        for r in resolved:
            conn.execute(
                """
                INSERT INTO order_items
                       (order_id, menu_item_id, quantity,
                        unit_price_cents, line_total_cents)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    r["menu_item_id"],
                    r["quantity"],
                    r["unit_price_cents"],
                    r["line_total_cents"],
                ),
            )

        order = _fetch_order(conn, order_id)

    return order, 201


def get_order(order_id):
    """operationId: getOrder — GET /orders/{id}"""
    order = db.query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    if order is None:
        return _err("Order not found", 404)
    order["items"] = db.query_all(
        "SELECT * FROM order_items WHERE order_id = ? ORDER BY id", (order_id,)
    )
    return order, 200


# ── Order status state machine ────────────────────────────────────────────────

_ALLOWED_TRANSITIONS = {
    "NEW":       {"PREPARING", "CANCELLED"},
    "PREPARING": {"READY"},
    "READY":     {"COMPLETED"},
    "COMPLETED": set(),   # terminal — no outgoing transitions
    "CANCELLED": set(),   # terminal — no outgoing transitions
}

_VALID_TARGET_STATUSES = {"PREPARING", "READY", "COMPLETED", "CANCELLED"}


def update_order_status(order_id):
    """operationId: updateOrderStatus — PATCH /orders/{id}/status"""
    body = request.get_json(silent=True) or {}
    new_status = body.get("status")

    # 400: status value not in the allowed enum
    if new_status not in _VALID_TARGET_STATUSES:
        return _err(
            f"status must be one of: {', '.join(sorted(_VALID_TARGET_STATUSES))}", 400
        )

    # 404: order does not exist
    order = db.query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    if order is None:
        return _err("Order not found", 404)

    current = order["status"]

    # 422: transition not permitted by the state machine
    if new_status not in _ALLOWED_TRANSITIONS.get(current, set()):
        return _err(
            f"Invalid status transition: {current} -> {new_status}", 422
        )

    with db.transaction() as conn:
        conn.execute(
            "UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id)
        )
        updated = _fetch_order(conn, order_id)

    return updated, 200


def list_customer_orders(customer_id):
    """operationId: listCustomerOrders — GET /customers/{id}/orders"""
    # 404 if customer does not exist
    if db.query_one("SELECT id FROM customers WHERE id = ?", (customer_id,)) is None:
        return _err("Customer not found", 404)

    with db.transaction() as conn:
        orders = conn.execute(
            "SELECT * FROM orders WHERE customer_id = ? ORDER BY id",
            (customer_id,),
        ).fetchall()

        result = []
        for order_row in orders:
            order = dict(order_row)
            items = conn.execute(
                "SELECT * FROM order_items WHERE order_id = ? ORDER BY id",
                (order["id"],),
            ).fetchall()
            order["items"] = [dict(i) for i in items]
            result.append(order)

    # Return empty array [] if customer exists but has no orders (not 404)
    return result, 200
