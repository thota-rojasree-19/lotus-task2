"""
reset_db.py — Drop and recreate the SQLite database from schema.sql + seed.sql.

Idempotent: safe to run multiple times. Deletes the existing DB file before
recreating it, guaranteeing a clean baseline for every test run.

Exit codes:
  0 — success
  1 — error

Usage:
  python harness/reset_db.py
"""
import os
import sqlite3
import sys

_BASE   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.environ.get("DB_PATH", os.path.join(_BASE, "restaurant.db"))
SCHEMA  = os.path.join(_BASE, "schema.sql")
SEED    = os.path.join(_BASE, "seed.sql")


def reset():
    # Remove stale database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        with open(SCHEMA, encoding="utf-8") as f:
            conn.executescript(f.read())
        print("Schema applied.")

        with open(SEED, encoding="utf-8") as f:
            conn.executescript(f.read())
        print("Seed data applied.")

        conn.close()
    except Exception as exc:
        conn.close()
        print(f"ERROR: {exc}")
        sys.exit(1)

    print(f"Database ready: {DB_PATH}")


if __name__ == "__main__":
    reset()
