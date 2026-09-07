Product 004 – Restaurant OpenAPI + SQLite Interface Harness

1. Overview

This project implements a reusable development and testing Harness for OpenAPI-first HTTP interfaces backed by SQLite.

The canonical Restaurant backend is used to prove that the Harness can:

Validate the OpenAPI contract before the application starts

Create and reset a clean SQLite database

Seed predictable test data

Run a Flask HTTP API

Validate API requests and responses against the OpenAPI contract

Test business rules through HTTP requests

Run the complete workflow with one command

Be reused for additional OpenAPI endpoints

Note: No frontend is included because the SOW focuses on the HTTP interface, SQLite backend, and reusable testing Harness.

2. Prerequisites

Python 3.10+

Git

Bash / Git Bash on Windows

Check Python:

python --version

3. Clone the Repository

GitHub Repository:
https://github.com/thota-rojasree-19/lotus-task2

git clone https://github.com/thota-rojasree-19/lotus-task2.git
cd lotus-task2

4. Install Dependencies

pip install -r requirements.txt

5. Database Setup & Reset

The project uses SQLite.

The database file is:

restaurant.db

The database is disposable and is recreated from:

schema.sql
seed.sql

To reset the database manually:

python harness/reset_db.py

The reset process removes the existing database and recreates the required schema and seed data.

6. Start the API Server

Run:

python src/app.py

The Flask API starts locally at:

http://127.0.0.1:5000

Keep the server running while manually testing the API.

7. Run the Complete Test Pipeline

The recommended command is:

bash run-tests.sh

The pipeline runs in this order:

1. Validate openapi.yaml
2. Reset the SQLite database
3. Run contract checks
4. Run pytest HTTP tests

A successful run ends with:

All steps passed.

8. Run Individual Test Steps

Validate OpenAPI

python harness/validate_openapi.py

Reset Database

python harness/reset_db.py

Run Contract Checks

python harness/contract.py

Run Pytest

pytest -q

9. Quick API Workflow

The following workflow demonstrates the main Restaurant use case.

Step 1 – Get Menu

curl http://127.0.0.1:5000/menu

Choose a menu item ID from the response.

Example:

menu_item_id = 1

Step 2 – Create Customer

curl -X POST http://127.0.0.1:5000/customers   -H "Content-Type: application/json"   -d '{"name":"Alice","email":"alice@example.com"}'

Save the returned customer ID.

Example:

customer_id = 3

Step 3 – Get Dining Tables

curl http://127.0.0.1:5000/tables

Choose a table with at least 2 seats.

Example:

table_id = 2

Step 4 – Create Reservation

curl -X POST http://127.0.0.1:5000/reservations   -H "Content-Type: application/json"   -d '{"customer_id":3,"table_id":2,"reservation_time":"2026-09-10T19:00:00","party_size":2}'

The reservation should be created successfully if:

The table exists

The table has enough seats

There is no conflicting active reservation

Step 5 – Create Order

curl -X POST http://127.0.0.1:5000/orders   -H "Content-Type: application/json"   -d '{"customer_id":3,"items":[{"menu_item_id":1,"quantity":2}]}'

The backend calculates the price from SQLite.

The client does not supply or control the price.

Save the returned order ID.

Example:

order_id = 1

Step 6 – Get Order

curl http://127.0.0.1:5000/orders/1

Verify:

Customer

Items

Quantity

Unit price

Line total

Server-calculated order total

Current status

Step 7 – Update Order Status

Valid transitions are:

NEW → PREPARING
PREPARING → READY
READY → COMPLETED

There is also:

NEW → CANCELLED

NEW → PREPARING

curl -X PATCH http://127.0.0.1:5000/orders/1/status   -H "Content-Type: application/json"   -d '{"status":"PREPARING"}'

PREPARING → READY

curl -X PATCH http://127.0.0.1:5000/orders/1/status   -H "Content-Type: application/json"   -d '{"status":"READY"}'

READY → COMPLETED

curl -X PATCH http://127.0.0.1:5000/orders/1/status   -H "Content-Type: application/json"   -d '{"status":"COMPLETED"}'

Invalid state transitions are rejected.

Step 8 – Get Customer Orders

curl http://127.0.0.1:5000/customers/3/orders

This returns the customer's order history.

10. API Endpoints

Operation ID

Method

Endpoint

listMenu

GET

/menu

getMenuItem

GET

/menu/{id}

createCustomer

POST

/customers

listDiningTables

GET

/tables

createReservation

POST

/reservations

getReservation

GET

/reservations/{id}

createOrder

POST

/orders

getOrder

GET

/orders/{id}

updateOrderStatus

PATCH

/orders/{id}/status

listCustomerOrders

GET

/customers/{id}/orders

openapi.yaml is the contract and source of truth for these endpoints.

11. Business Rules

Menu Pricing

Menu prices are stored in SQLite.

The client cannot provide or override the price when creating an order.

The backend always reads the current price from the database.

Order Total

The server calculates:

line_total = quantity × database menu price

and:

total = sum(all line totals)

Unavailable Items

Unavailable menu items cannot be ordered.

Reservation Party Size

The reservation must satisfy:

party_size > 0

and:

party_size <= table seats

Reservation Conflict

The same table cannot have two active reservations at the same reservation time.

Order Status

Allowed statuses:

NEW
PREPARING
READY
COMPLETED
CANCELLED

Valid transitions:

NEW → PREPARING
NEW → CANCELLED
PREPARING → READY
READY → COMPLETED

All other transitions are rejected.

Historical Order Prices

When an order is created, the current menu price is copied into:

order_items.unit_price_cents

Therefore, if the menu price changes later, historical orders keep their original unit price and total.

12. Order Status State Machine

                 ┌─────────────┐
                 │     NEW     │
                 └──────┬──────┘
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       ┌───────────┐        ┌───────────┐
       │ PREPARING │        │ CANCELLED │
       └─────┬─────┘        └───────────┘
             │
             ▼
       ┌───────────┐
       │   READY   │
       └─────┬─────┘
             │
             ▼
       ┌───────────┐
       │ COMPLETED │
       └───────────┘

13. Project Structure

lotus-task2/
│
├── .gitignore
├── README.md
├── openapi.yaml
├── requirements.txt
├── run-tests.sh
├── schema.sql
├── seed.sql
│
├── src/
│   ├── app.py
│   ├── db.py
│   └── handlers.py
│
├── harness/
│   ├── validate_openapi.py
│   ├── reset_db.py
│   └── contract.py
│
└── tests/
    ├── test_menu.py
    ├── test_orders.py
    └── test_reservations.py

restaurant.db is generated locally and intentionally excluded from Git.

14. Harness Design

The Harness is separated from Restaurant-specific business logic.

OpenAPI Validation

harness/validate_openapi.py

Validates the OpenAPI document before the application test flow starts.

Database Reset

harness/reset_db.py

Creates a clean SQLite database using:

schema.sql
seed.sql

Contract Checks

harness/contract.py

Runs HTTP-level checks against the API and verifies expected contract behavior.

HTTP Tests

tests/

Uses Flask's HTTP test client and pytest rather than calling handler functions directly.

This ensures the tests exercise the actual HTTP interface.

15. Test Coverage

The automated tests cover:

Menu listing

Menu item retrieval

Missing menu items

Customer creation

Dining table listing

Reservation creation

Reservation validation

Reservation conflicts

Order creation

Database-driven pricing

Order totals

Unavailable menu items

Order retrieval

Order status transitions

Invalid status transitions

Customer order history

Historical order prices

OpenAPI request and response contract validation

16. Adding a New Endpoint

To add a new endpoint:

1. Update OpenAPI

Add the endpoint and its schema to:

openapi.yaml

Give the endpoint an operationId.

2. Update the Backend

Implement the endpoint in:

src/handlers.py

and register the route in:

src/app.py

3. Add HTTP Tests

Add tests under:

tests/

Use the Flask HTTP test client.

4. Update Contract Checks

If the new endpoint requires reusable contract validation, update:

harness/contract.py

5. Run the Full Pipeline

bash run-tests.sh

The OpenAPI validation must pass before the remaining tests run.

17. Second-Fresher Dogfood Workflow

A second Fresher should be able to use the repository without source-code coaching.

They should only need:

GitHub repository

README.md

openapi.yaml

Recommended Workflow

git clone https://github.com/thota-rojasree-19/lotus-task2.git
cd lotus-task2
pip install -r requirements.txt
python harness/reset_db.py
python src/app.py

Then they should:

Call GET /menu

Create a customer with POST /customers

Call GET /tables

Select a suitable table

Create a reservation with POST /reservations

Create an order with two menu items using POST /orders

Verify the server-calculated total using GET /orders/{id}

Move the order through:

NEW → PREPARING

PREPARING → READY

READY → COMPLETED

Verify customer history using GET /customers/{id}/orders

Run:

bash run-tests.sh

No Restaurant source-code changes should be necessary for this workflow.

18. Key Design Decisions

OpenAPI-First

The OpenAPI document defines the HTTP contract and is validated before the application test flow.

SQLite

SQLite is used because it is lightweight, disposable, and suitable for deterministic local testing.

Integer Prices

Prices are stored as integer cents to avoid floating-point money calculations.

Server-Side Pricing

Order prices and totals are calculated from database values rather than trusted from client input.

Historical Pricing

The order item stores the unit price at order creation time so historical orders remain correct after menu price changes.

Explicit State Machine

Order status transitions are represented explicitly so invalid transitions can be rejected predictably.

HTTP-Level Testing

Tests use the HTTP interface instead of directly invoking business logic, making the tests closer to real API usage.

Disposable Database

The database can be reset at any time, making local and automated test runs predictable.

19. Run Everything

For a clean complete run:

bash run-tests.sh

This performs:

OpenAPI validation
        ↓
Database reset
        ↓
Contract checks
        ↓
Pytest
        ↓
PASS / FAIL result

20. Repository

🔗 GitHub:
https://github.com/thota-rojasree-19/lotus-task2
