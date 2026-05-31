import sqlite3

DB_NAME = "analytics_ledger.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        image_name TEXT UNIQUE,
        merchant TEXT,
        amount REAL,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()


def insert_receipt(data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
        INSERT INTO receipts (device_id, image_name, merchant, amount, date)
        VALUES (?, ?, ?, ?, ?)
        """, (
            data["device_id"],
            data["image_name"],
            data["merchant"],
            data["amount"],
            data["date"]
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()