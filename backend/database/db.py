import sqlite3
from pathlib import Path

# ================= DATABASE FILE =================
DB_PATH = Path("receipts.db")


# ================= GET DB CONNECTION =================
def get_db():
    """
    Returns a SQLite connection with row_factory enabled
    so rows behave like dictionaries.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ================= INITIALIZE DATABASE =================
def init_db():
    """
    Creates receipts table if it does not exist.
    Call this once at app startup.
    """
    db = get_db()

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS receipts (
            bill_id TEXT PRIMARY KEY,
            user_email TEXT,
            vendor TEXT NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            tax REAL NOT NULL,
            subtotal REAL DEFAULT 0.0,
            category TEXT DEFAULT 'Uncategorized'
        )
        """
    )
    
    # --- Optimization: Add Indexes for Search ---
    db.execute("CREATE INDEX IF NOT EXISTS idx_vendor ON receipts(vendor)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_date ON receipts(date)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_category ON receipts(category)")

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT,
            name TEXT,
            phone TEXT,
            budget REAL DEFAULT 50000.0,
            auth_method TEXT DEFAULT 'email'
        )
        """
    )

    # Migration: Add subtotal column if it doesn't exist
    try:
        db.execute("ALTER TABLE receipts ADD COLUMN subtotal REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass

    # Migration: Add category column if it doesn't exist
    try:
        db.execute("ALTER TABLE receipts ADD COLUMN category TEXT DEFAULT 'Uncategorized'")
    except sqlite3.OperationalError:
        pass

    # Migration: Add user_email column if it doesn't exist
    try:
        db.execute("ALTER TABLE receipts ADD COLUMN user_email TEXT")
    except sqlite3.OperationalError:
        pass

    # Migration: Add budget column to users if it doesn't exist
    try:
        db.execute("ALTER TABLE users ADD COLUMN budget REAL DEFAULT 50000.0")
    except sqlite3.OperationalError:
        pass

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