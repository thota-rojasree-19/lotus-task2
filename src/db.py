"""
db.py — SQLite connection and query helpers.

All connections enable PRAGMA foreign_keys = ON.
DB_PATH is resolved from the DB_PATH environment variable, or defaults to
restaurant.db in the project root (one level above this file's directory).
"""
import contextlib
import os
import sqlite3

# Resolve the database path once at import time.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.environ.get("DB_PATH", os.path.join(_ROOT, "restaurant.db"))


@contextlib.contextmanager
def transaction():
    """Yield a sqlite3.Connection inside an atomic transaction.

    - Commits automatically on success.
    - Rolls back and re-raises on any exception.
    - Always closes the connection.
    - Enables PRAGMA foreign_keys = ON for every connection.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_one(sql, params=()):
    """Return the first matching row as a dict, or None if no rows found."""
    with transaction() as conn:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None


def query_all(sql, params=()):
    """Return all matching rows as a list of dicts."""
    with transaction() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
