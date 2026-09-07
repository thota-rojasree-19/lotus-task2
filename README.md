# Product 004 — Restaurant OpenAPI + SQLite Interface Harness

REST API for a restaurant management system backed by SQLite.
Implements the 10 operations defined in `openapi.yaml` using Flask.

## Prerequisites

- Python 3.10 or later

## Setup

```bash
pip install -r requirements.txt
```

## Running the API server

```bash
python src/app.py
```

Server starts at `http://localhost:5000`.

## Full test pipeline

```bash
bash run-tests.sh
```

Steps executed in order:
1. `python harness/validate_openapi.py` — validate the OpenAPI contract first
2. `python harness/reset_db.py` — reset the database to a clean baseline
3. `python harness/contract.py` — end-to-end contract checks
4. `pytest tests/ -v --tb=short` — full pytest suite

## Running individual steps

```bash
# Validate the OpenAPI spec
python harness/validate_openapi.py

# Reset the database
python harness/reset_db.py

# Run the contract harness only
python harness/contract.py

# Run pytest only (requires DB to be seeded first)
pytest tests/ -v
```

## Project structure

```
openapi.yaml              Contract / source of truth (OpenAPI 3.0.3)
schema.sql                Database DDL — 7 SOW-specified tables
seed.sql                  Baseline test data

src/
  app.py                  Flask application and route registration
  db.py                   SQLite connection helpers (transaction, query_one, query_all)
  handlers.py             One function per operationId

harness/
  validate_openapi.py     Validates openapi.yaml structure and operationId coverage
  reset_db.py             Drops and recreates restaurant.db from schema + seed
  contract.py             End-to-end contract tests via Flask test client

tests/
  test_menu.py            Tests for listMenu, getMenuItem
  test_reservations.py    Tests for createCustomer, listDiningTables,
                          createReservation, getReservation
  test_orders.py          Tests for createOrder, getOrder,
                          updateOrderStatus, listCustomerOrders

requirements.txt
run-tests.sh
README.md
```

## API endpoints

| Method | Path | operationId |
|--------|------|-------------|
| GET | /menu | listMenu |
| GET | /menu/{id} | getMenuItem |
| POST | /customers | createCustomer |
| GET | /tables | listDiningTables |
| POST | /reservations | createReservation |
| GET | /reservations/{id} | getReservation |
| POST | /orders | createOrder |
| GET | /orders/{id} | getOrder |
| PATCH | /orders/{id}/status | updateOrderStatus |
| GET | /customers/{id}/orders | listCustomerOrders |

## Order status state machine

```
NEW ──► PREPARING ──► READY ──► COMPLETED
 │
 └──► CANCELLED
```

COMPLETED and CANCELLED are terminal states — no further transitions are allowed.

## Key design decisions

- **Prices in integer cents** — `price_cents`, `unit_price_cents`, `line_total_cents`,
  `total_cents` are all integers to avoid floating-point rounding errors.
- **Historical price preservation** — `order_items.unit_price_cents` and
  `order_items.line_total_cents` are written at INSERT time from the database and
  never updated, even if the menu item price changes later.
- **Backend-calculated totals** — `line_total_cents = unit_price_cents × quantity`;
  `total_cents = SUM(line_total_cents)`. Neither is accepted from the client.
- **400 vs 422** — 400 for field/schema validation failures; 422 for business-rule
  violations (unavailable menu item, invalid status transition).
- **FK enforcement** — `PRAGMA foreign_keys = ON` is set on every SQLite connection.
- **Validation-first pipeline** — `openapi.yaml` is validated before any application
  code runs, consistent with its role as the source of truth.
