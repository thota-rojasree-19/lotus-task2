# Product 004 – Restaurant OpenAPI + SQLite Interface Harness

## 1. Overview

This project is a reusable development and testing Harness for OpenAPI-first HTTP interfaces backed by SQLite, using a canonical Restaurant backend as the implementation. 

Key features include:
- **OpenAPI contract validation**: Ensures the API contract is the ultimate source of truth.
- **SQLite database reset and seed**: Provides reproducible environments.
- **Flask HTTP API**: A lightweight backend implementing the operations.
- **HTTP-level contract testing**: End-to-end tests to guarantee compliance.
- **Business-rule testing**: Verifies logic like pricing and state transitions.
- **One-command test execution**: A single script to run the entire pipeline.
- **Reusability**: Designed so that the harness can test other endpoints in the future.
- **No frontend**: UI is explicitly outside the scope of this project.

## 2. Prerequisites

Ensure you have the following installed on your system:
- Python 3.10+
- Git
- Bash / Git Bash on Windows

Verify your Python version:
```bash
python --version
```

## 3. Clone the Repository

Clone the project from GitHub and navigate into the directory:

```bash
git clone https://github.com/thota-rojasree-19/lotus-task2
cd lotus-task2
```
[https://github.com/thota-rojasree-19/lotus-task2](https://github.com/thota-rojasree-19/lotus-task2)

## 4. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## 5. Database Setup & Reset

The project uses **SQLite**. The database file (`restaurant.db`) is disposable and generated locally during tests. It is created from `schema.sql` (defining tables) and seeded with test data from `seed.sql`.

To reset the database manually to a clean state:
```bash
python harness/reset_db.py
```

## 6. Start the API Server

Run the Flask application:

```bash
python src/app.py
```

The local API will be available at:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

## 7. Run the Complete Test Pipeline

To run the entire suite of checks and tests, run:

```bash
bash run-tests.sh
```

This script executes the following in order:
1. **OpenAPI validation**: Syntactically checks the `openapi.yaml` contract.
2. **Database reset**: Cleans and seeds `restaurant.db`.
3. **Contract checks**: Runs end-to-end HTTP tests.
4. **Pytest**: Runs all unit and integration tests.

Expected successful result will conclude with:
```text
========================================================
  All steps passed.
========================================================
```

## 8. Run Individual Test Steps

You can also run any step of the pipeline individually:

**OpenAPI validation**
```bash
python harness/validate_openapi.py
```

**Database reset**
```bash
python harness/reset_db.py
```

**Contract checks**
```bash
python harness/contract.py
```

**Pytest** (Ensure you have reset the DB first!)
```bash
python -m pytest tests/ -v --tb=short
```

## 9. Quick API Workflow

This canonical workflow demonstrates how a customer might interact with the API based on `openapi.yaml`. 
*Note: Use the actual IDs returned by earlier requests for subsequent endpoints.*

**1. List the menu**
```bash
curl -X GET http://127.0.0.1:5000/menu
```

**2. Create a customer**
```bash
curl -X POST http://127.0.0.1:5000/customers \
     -H "Content-Type: application/json" \
     -d '{"name": "Alice", "email": "alice@example.com", "phone": "555-1234"}'
```
*(Assume returned ID is `1`)*

**3. Check available dining tables**
```bash
curl -X GET http://127.0.0.1:5000/tables
```
*(Assume table ID `2` with 4 seats is available)*

**4. Create a reservation**
```bash
curl -X POST http://127.0.0.1:5000/reservations \
     -H "Content-Type: application/json" \
     -d '{"customer_id": 1, "dining_table_id": 2, "party_size": 2, "reservation_time": "2026-10-15T19:00:00Z"}'
```
*(Assume reservation ID is `1`)*

**5. Create an order**
```bash
curl -X POST http://127.0.0.1:5000/orders \
     -H "Content-Type: application/json" \
     -d '{
           "customer_id": 1,
           "dining_table_id": 2,
           "reservation_id": 1,
           "items": [
             {"menu_item_id": 1, "quantity": 2},
             {"menu_item_id": 3, "quantity": 1}
           ]
         }'
```
*(Assume order ID is `1`)*

**6. Get order details**
```bash
curl -X GET http://127.0.0.1:5000/orders/1
```

**7. Update order status**
```bash
curl -X PATCH http://127.0.0.1:5000/orders/1/status \
     -H "Content-Type: application/json" \
     -d '{"status": "PREPARING"}'
```

**8. Get customer order history**
```bash
curl -X GET http://127.0.0.1:5000/customers/1/orders
```

**9. Run the test harness to verify your backend**
```bash
bash run-tests.sh
```

## 10. API Endpoints

| operationId | HTTP Method | Path |
|---|---|---|
| listMenu | GET | `/menu` |
| getMenuItem | GET | `/menu/{id}` |
| createCustomer | POST | `/customers` |
| listDiningTables | GET | `/tables` |
| createReservation | POST | `/reservations` |
| getReservation | GET | `/reservations/{id}` |
| createOrder | POST | `/orders` |
| getOrder | GET | `/orders/{id}` |
| updateOrderStatus | PATCH | `/orders/{id}/status` |
| listCustomerOrders | GET | `/customers/{id}/orders` |

## 11. Business Rules

- **Menu price** comes from SQLite; the client cannot control or spoof prices.
- **Order total** is always calculated server-side.
- **Line total** = `quantity × database menu price`.
- **Unavailable menu items** cannot be ordered.
- **Party Size**: `party_size > 0` and must not exceed the specified table's capacity.
- **Double Booking**: The same table cannot have two active reservations at the exact same reservation time.
- **Allowed order statuses**: `NEW`, `PREPARING`, `READY`, `COMPLETED`, `CANCELLED`.
- **Valid status transitions**:
  - `NEW` → `PREPARING`
  - `NEW` → `CANCELLED`
  - `PREPARING` → `READY`
  - `READY` → `COMPLETED`
- **Historical Pricing**: Historical `order_items` preserve their original unit price even if menu prices change later.

## 12. Order Status State Machine

```text
      NEW 
     /   \
CANCELLED  PREPARING
             |
           READY
             |
          COMPLETED
```

## 13. Project Structure

```text
.
├── .git/
├── .gitignore               # Ignores restaurant.db and python caches
├── README.md                # This file
├── harness/                 # Core testing utilities
│   ├── contract.py
│   ├── reset_db.py
│   └── validate_openapi.py
├── openapi.yaml             # Source of truth API contract
├── requirements.txt         # Dependencies
├── run-tests.sh             # Master test runner
├── schema.sql               # SQLite database DDL
├── seed.sql                 # Baseline test data
├── src/                     # Application source code
│   ├── app.py
│   ├── db.py
│   └── handlers.py
└── tests/                   # Pytest suite
    ├── test_menu.py
    ├── test_orders.py
    └── test_reservations.py
```
*(Note: `restaurant.db` is generated locally and intentionally ignored by Git)*

## 14. Harness Design

- **`harness/validate_openapi.py`**: Ensures `openapi.yaml` is structurally valid and complete before any code runs against it.
- **`harness/reset_db.py`**: Drops and recreates the SQLite database to maintain a deterministic testing environment.
- **`harness/contract.py`**: Validates the application responses (headers, status codes, schemas) purely via HTTP against the OpenAPI specification.
- **`tests/`**: Contains fine-grained business logic testing.
- **Design Philosophy**: The harness emphasizes end-to-end HTTP testing over isolated function mocking to guarantee the real API behavior matches the contract exactly.

## 15. Test Coverage

Tests enforce:
- **Menu**: Visibility, correct payload shapes.
- **Customers**: Creation constraints, duplicate email rejection.
- **Tables**: Listing correctly.
- **Reservations**: Schema constraints, table sizes, conflicting bookings.
- **Orders**: Valid payload rejection, missing item 404s, backend price calculation, state machine transition validity.
- **Pricing**: Integer cents math and preservation.
- **Totals**: Line totals and final totals.
- **Unavailable items**: Rejection of inactive menu items.
- **Status transitions**: Enforcing valid paths (e.g. `NEW` to `PREPARING`, no skipping).
- **Customer order history**: Endpoint functionality.
- **Historical pricing**: Ensuring past orders reflect past prices.
- **OpenAPI contract validation**: Strict input/output schema checks.

## 16. Adding a New Endpoint

To extend the API, follow these steps:
1. Update `openapi.yaml` with the new path, schemas, and `operationId`.
2. Add the backend route and handler in `src/app.py` and `src/handlers.py`.
3. Add appropriate HTTP-level business tests to the `tests/` directory.
4. Update reusable contract checks in `harness/contract.py` if needed.
5. Run `bash run-tests.sh` to ensure everything passes.

## 17. Second-Fresher Dogfood Workflow

Another fresher should be able to run this without looking at the source code, using only the provided `README.md` and `openapi.yaml`.

1. **Clone** the repository.
2. **Install dependencies** (`pip install -r requirements.txt`).
3. **Reset database** (`python harness/reset_db.py`).
4. **Start API** (`python src/app.py`).
5. **Follow the canonical Restaurant API workflow** using the exact HTTP endpoints (listed in section 9).
6. **Run the complete test pipeline** (`bash run-tests.sh`).

## 18. Key Design Decisions

- **OpenAPI-first approach**: The contract dictates the behavior; the backend obeys it.
- **SQLite**: Zero-configuration, single-file database perfect for isolation and disposability.
- **Integer cents for prices**: Used everywhere (`price_cents`, `total_cents`) to avoid floating-point math errors.
- **Server-side pricing**: Prices are never trusted from the client body.
- **Historical pricing**: `order_items` copies `unit_price_cents` to persist data safely.
- **Explicit order state machine**: Status transitions are strictly enforced to prevent logical errors (like skipping `PREPARING`).
- **HTTP-level testing**: Validates the true contract.
- **Disposable database**: Recreated via `schema.sql` + `seed.sql` on every run for a clean slate.

## 19. Run Everything

To validate the entire harness and backend implementation:

```bash
bash run-tests.sh
```

**Pipeline Flow:**
```text
OpenAPI validation
        ↓
  Database reset
        ↓
  Contract checks
        ↓
      Pytest
        ↓
   PASS / FAIL
```

## 20. Repository

[https://github.com/thota-rojasree-19/lotus-task2](https://github.com/thota-rojasree-19/lotus-task2)

## 21. Product 005: Generic OpenAPI-to-MCP Gateway

The Product 005 module introduces a generic Model Context Protocol (MCP) gateway that automatically exposes the Product 004 REST API endpoints as MCP tools by reading the existing `openapi.yaml`.

### Prerequisites
- Python 3.13
- `fastmcp==4.0.3`
- `httpx`
- `pyyaml`
- `pytest`
- `pytest-asyncio`

### Architecture
The MCP Gateway uses FastMCP to dynamically parse `openapi.yaml` and expose 10 operations as MCP tools over a streamable-HTTP transport. The gateway translates tool calls to REST HTTP requests, passing them to the running Flask backend.

### Environment Variables
- `OPENAPI_FILE` (default: `./openapi.yaml`)
- `API_BASE_URL` (default: `http://127.0.0.1:5000`)
- `MCP_HOST` (default: `127.0.0.1`)
- `MCP_PORT` (default: `8000`)

### How to Run

1. **Start the Product 004 Backend**
```bash
python harness/reset_db.py
export FLASK_APP=src.app:app
flask run --port=5000
```

2. **Start the MCP Gateway**
```bash
./run-mcp.sh
```

### Endpoints
- **MCP Streamable Transport URL:** `http://127.0.0.1:8000/mcp`
- **Swagger UI:** `http://127.0.0.1:8000/docs`

### Discovering and Calling Tools
Tools are discovered via the standard MCP protocol (`list_tools`). The tool names match the `operationIds` exactly (e.g., `listMenu`, `createCustomer`). 

To call tools via an MCP client:
1. Connect to the `http://127.0.0.1:8000/mcp` SSE endpoint.
2. Send `call_tool` with the tool name and flattened input schema parameters.

### Testing
Run the full acceptance flow:
```bash
./run-tests-mcp.sh
```
Or use the provided python wrapper (if bash is unavailable):
```cmd
python run-tests-mcp.py
```

### Cross-Fresher Configuration
To test the gateway with another Fresher's passing API implementation, you can change the environment variables:
```bash
export OPENAPI_FILE=/path/to/other/openapi.yaml
export API_BASE_URL=http://other-api-host:5000
./run-mcp.sh
```
