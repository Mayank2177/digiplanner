"""
db.py — SQLite connection + schema management.

This REPLACES the old `db.py` + `database(2).py` duplicate.
Fix applied: DB_PATH now comes from config.py (so every module in the app
writes to the SAME database file) instead of a second, disconnected
"receipts.db" created relative to whatever folder the process happened to
be launched from.
"""

import sqlite3
from config.config import DB_PATH


def get_db() -> sqlite3.Connection:
    """
    Returns a SQLite connection with row_factory enabled
    so rows behave like dictionaries.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """
    Creates all required tables if they do not exist.
    Safe to call multiple times (e.g. on every app startup).
    """
    db = get_db()

    # ── users ────────────────────────────────────────────────────────────
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            name TEXT,
            company TEXT,
            phone TEXT,
            budget REAL DEFAULT 50000.0,
            auth_method TEXT DEFAULT 'email',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # ── receipts ─────────────────────────────────────────────────────────
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS receipts (
            bill_id TEXT NOT NULL,
            user_email TEXT NOT NULL,
            vendor TEXT NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            tax REAL DEFAULT 0.0,
            subtotal REAL DEFAULT 0.0,
            category TEXT DEFAULT 'Uncategorized',
            currency TEXT DEFAULT 'USD',
            raw_text TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (bill_id, user_email),
            FOREIGN KEY (user_email) REFERENCES users(email) ON DELETE CASCADE
        )
        """
    )
    
    # Add currency column if it doesn't exist (migration for existing databases)
    try:
        db.execute("ALTER TABLE receipts ADD COLUMN currency TEXT DEFAULT 'USD'")
        db.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass

    db.execute("CREATE INDEX IF NOT EXISTS idx_vendor ON receipts(vendor)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_date ON receipts(date)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_category ON receipts(category)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_user_email ON receipts(user_email)")

    # ── line_items (individual items on each receipt) ───────────────────
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id TEXT NOT NULL,
            user_email TEXT NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            unit_price REAL DEFAULT 0.0,
            total_price REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bill_id, user_email) REFERENCES receipts(bill_id, user_email) ON DELETE CASCADE
        )
        """
    )
    
    db.execute("CREATE INDEX IF NOT EXISTS idx_line_items_receipt ON line_items(bill_id, user_email)")

    # ── alerts_sent (tracks which budget-threshold emails were already sent) ─
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts_sent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            month TEXT NOT NULL,
            threshold INTEGER NOT NULL,
            UNIQUE(user_email, month, threshold)
        )
        """
    )

    db.commit()
    db.close()
