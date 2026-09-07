-- schema.sql
-- DDL for the Restaurant API database.
-- Apply with: python harness/reset_db.py
-- All 7 tables match the SOW specification exactly.

PRAGMA foreign_keys = ON;

-- ── menu_categories ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS menu_categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL
);

-- ── menu_items ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS menu_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL
                    REFERENCES menu_categories(id) ON DELETE RESTRICT,
    name        TEXT    NOT NULL,
    description TEXT,
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
    available   INTEGER NOT NULL DEFAULT 1
                    CHECK (available IN (0, 1))
);

-- ── customers ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    email      TEXT    NOT NULL UNIQUE,
    phone      TEXT,
    created_at TEXT    NOT NULL
                   DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- ── dining_tables ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dining_tables (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    table_number TEXT    NOT NULL UNIQUE,
    seats        INTEGER NOT NULL CHECK (seats >= 1),
    status       TEXT    NOT NULL DEFAULT 'available'
                     CHECK (status IN ('available', 'reserved', 'occupied'))
);

-- ── reservations ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reservations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id      INTEGER NOT NULL
                         REFERENCES customers(id) ON DELETE RESTRICT,
    table_id         INTEGER NOT NULL
                         REFERENCES dining_tables(id) ON DELETE RESTRICT,
    party_size       INTEGER NOT NULL CHECK (party_size >= 1),
    reservation_time TEXT    NOT NULL,
    status           TEXT    NOT NULL DEFAULT 'active'
                         CHECK (status IN ('active', 'cancelled', 'completed')),
    created_at       TEXT    NOT NULL
                         DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- ── orders ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL
                    REFERENCES customers(id) ON DELETE RESTRICT,
    status      TEXT    NOT NULL DEFAULT 'NEW'
                    CHECK (status IN ('NEW', 'PREPARING', 'READY', 'COMPLETED', 'CANCELLED')),
    total_cents INTEGER NOT NULL DEFAULT 0 CHECK (total_cents >= 0),
    created_at  TEXT    NOT NULL
                    DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- ── order_items ───────────────────────────────────────────────────────────────
-- Exactly 7 SOW-specified columns.
-- unit_price_cents and line_total_cents are captured from menu_items at INSERT
-- time and preserved historically; they are never updated.
CREATE TABLE IF NOT EXISTS order_items (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id         INTEGER NOT NULL
                         REFERENCES orders(id) ON DELETE RESTRICT,
    menu_item_id     INTEGER NOT NULL
                         REFERENCES menu_items(id) ON DELETE RESTRICT,
    quantity         INTEGER NOT NULL CHECK (quantity >= 1),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0),
    line_total_cents INTEGER NOT NULL CHECK (line_total_cents >= 0)
);
