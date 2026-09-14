"""
queries.py — Data access layer for receipts, users, and budget alerts.

CRITICAL FIX applied here:
  The old version of this file did `import streamlit as st` and pulled
  `user_email` from `st.session_state` whenever the caller didn't pass one
  explicitly. That works ONLY inside a running Streamlit script. Called from
  FastAPI (main.py), `st.session_state` does not exist and every one of
  these functions would raise a RuntimeError the moment it was hit.

  Streamlit has been removed entirely. Every function that needs to know
  "which user" now takes `user_email` as a required parameter. In the API,
  that value comes from the authenticated JWT (see auth/security.py),
  never from a global/session variable.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from database.db import get_db
from utils.notifications import send_email_alert, send_sms_alert
from utils.logger import log_error


# ================= SAVE RECEIPT =================
def save_receipt(data: Dict[str, Any], user_email: str) -> None:
    """
    Save a receipt to the database for a specific user.
    Expected keys in `data`: bill_id, vendor, date, amount, tax, subtotal,
    category (optional), raw_text (optional).
    """
    if not user_email:
        raise ValueError("user_email is required")

    db = get_db()
    db.execute(
        """
        INSERT INTO receipts (bill_id, user_email, vendor, date, amount, tax, subtotal, category, raw_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["bill_id"],
            user_email,
            data["vendor"],
            data["date"],
            float(data["amount"]),
            float(data.get("tax") or 0.0),
            float(data.get("subtotal") or 0.0),
            data.get("category") or "Uncategorized",
            data.get("raw_text"),
        ),
    )
    db.commit()
    db.close()

    # Fire budget-threshold alerts (never let a notification failure break the save)
    try:
        check_budget_alerts(user_email)
    except Exception as e:
        log_error(f"Budget alert check failed for {user_email}: {e}")


# ================= DUPLICATE CHECK (ROBUST) =================
def check_receipt_duplicate(bill_id: str, vendor: str, date: str, amount: float, user_email: str) -> bool:
    """
    Check for duplicates with high reliability.
    1. Exact Bill ID match (if it looks like a real, non-generated ID)
    2. Vendor + Date + Amount fingerprint (fallback for OCR misses on bill_id)
    """
    db = get_db()

    if bill_id and len(bill_id) > 2 and "REC-" not in bill_id:
        cur = db.execute(
            "SELECT 1 FROM receipts WHERE bill_id = ? AND user_email = ?",
            (bill_id, user_email),
        )
        if cur.fetchone():
            db.close()
            return True

    try:
        cur = db.execute(
            "SELECT 1 FROM receipts WHERE vendor = ? AND date = ? AND abs(amount - ?) < 0.01 AND user_email = ?",
            (vendor, date, float(amount), user_email),
        )
        if cur.fetchone():
            db.close()
            return True
    except Exception:
        pass

    db.close()
    return False


def receipt_exists(bill_id: str, user_email: str) -> bool:
    db = get_db()
    cur = db.execute(
        "SELECT 1 FROM receipts WHERE bill_id = ? AND user_email = ?",
        (bill_id, user_email),
    )
    row = cur.fetchone()
    db.close()
    return row is not None


# ================= FETCH ALL RECEIPTS =================
def fetch_all_receipts(user_email: str) -> List[Dict[str, Any]]:
    """Returns list of dicts for a specific user, ordered by date DESC."""
    if not user_email:
        raise ValueError("user_email is required")

    db = get_db()
    cur = db.execute(
        "SELECT bill_id, vendor, date, amount, tax, subtotal, category FROM receipts "
        "WHERE user_email = ? ORDER BY date DESC",
        (user_email,),
    )
    rows = cur.fetchall()
    db.close()

    return [_row_to_dict(r) for r in rows]


# ================= GET ONE RECEIPT =================
def get_receipt_by_id(bill_id: str, user_email: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    cur = db.execute(
        "SELECT * FROM receipts WHERE bill_id = ? AND user_email = ?",
        (bill_id, user_email),
    )
    row = cur.fetchone()
    db.close()
    return _row_to_dict(row) if row else None


# ================= UPDATE RECEIPT =================
def update_receipt(bill_id: str, update_data: Dict[str, Any], user_email: str) -> bool:
    """Updates specific fields for a receipt belonging to user_email."""
    db = get_db()

    allowed_fields = {"vendor", "date", "amount", "tax", "subtotal", "category"}
    fields, values = [], []

    for key, value in update_data.items():
        if key in allowed_fields and value is not None:
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        db.close()
        return False

    values.extend([bill_id, user_email])
    query = f"UPDATE receipts SET {', '.join(fields)} WHERE bill_id = ? AND user_email = ?"

    db.execute(query, values)
    db.commit()
    updated = db.total_changes > 0
    db.close()
    return updated


# ================= SEARCH RECEIPTS =================
def search_receipts(
    user_email: str,
    vendor: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Search receipts with dynamic SQL filtering, scoped to one user."""
    if not user_email:
        raise ValueError("user_email is required")

    db = get_db()

    query = "SELECT * FROM receipts WHERE user_email = ?"
    params: List[Any] = [user_email]

    if vendor:
        query += " AND vendor LIKE ?"
        params.append(f"%{vendor}%")
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if min_amount is not None:
        query += " AND amount >= ?"
        params.append(min_amount)
    if max_amount is not None:
        query += " AND amount <= ?"
        params.append(max_amount)

    query += " ORDER BY date DESC"

    cur = db.execute(query, params)
    rows = cur.fetchall()
    db.close()

    return [_row_to_dict(r) for r in rows]


# ================= DELETE ONE RECEIPT =================
def delete_receipt(bill_id: str, user_email: str) -> bool:
    db = get_db()
    db.execute(
        "DELETE FROM receipts WHERE bill_id = ? AND user_email = ?",
        (bill_id, user_email),
    )
    db.commit()
    deleted = db.total_changes > 0
    db.close()
    return deleted


# ================= CLEAR ALL RECEIPTS (for one user) =================
def clear_all_receipts(user_email: str) -> None:
    db = get_db()
    db.execute("DELETE FROM receipts WHERE user_email = ?", (user_email,))
    db.commit()
    db.close()


# ================= USERS =================
def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    cur = db.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    db.close()
    return dict(row) if row else None


def create_user(email: str, password_hash: str, name: str = "", company: str = "",
                 phone: str = "", auth_method: str = "email") -> Dict[str, Any]:
    db = get_db()
    db.execute(
        """
        INSERT INTO users (email, password_hash, name, company, phone, auth_method)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (email, password_hash, name, company, phone, auth_method),
    )
    db.commit()
    db.close()
    return get_user_by_email(email)


def update_user_budget(email: str, budget: float) -> None:
    db = get_db()
    db.execute("UPDATE users SET budget = ? WHERE email = ?", (budget, email))
    db.commit()
    db.close()


# ================= BUDGET ALERT LOGIC =================
def check_budget_alerts(email: str) -> None:
    """
    Checks if the user's monthly spend has crossed 50 / 90 / 100% of their
    budget and sends an alert email (once per threshold per month).
    """
    user = get_user_by_email(email)
    if not user or not user.get("budget"):
        return

    budget = float(user["budget"])
    phone = user.get("phone")

    current_month = datetime.now().strftime("%Y-%m")
    db = get_db()
    cur = db.execute(
        "SELECT SUM(amount) as total FROM receipts WHERE user_email = ? AND date LIKE ?",
        (email, f"{current_month}%"),
    )
    res = cur.fetchone()
    current_spend = float(res["total"]) if res and res["total"] else 0.0

    if current_spend == 0:
        db.close()
        return

    percent_used = (current_spend / budget) * 100
    for threshold in (50, 90, 100):
        if percent_used >= threshold:
            cur = db.execute(
                "SELECT 1 FROM alerts_sent WHERE user_email = ? AND month = ? AND threshold = ?",
                (email, current_month, threshold),
            )
            if not cur.fetchone():
                send_email_alert(email, threshold, current_spend, budget)
                if phone:
                    send_sms_alert(phone, threshold, current_spend)

                db.execute(
                    "INSERT INTO alerts_sent (user_email, month, threshold) VALUES (?, ?, ?)",
                    (email, current_month, threshold),
                )
                db.commit()

    db.close()


# ================= HELPERS =================
def _row_to_dict(r) -> Dict[str, Any]:
    keys = r.keys()
    return {
        "bill_id": r["bill_id"],
        "vendor": r["vendor"],
        "date": r["date"],
        "amount": float(r["amount"]),
        "tax": float(r["tax"]) if ("tax" in keys and r["tax"] is not None) else 0.0,
        "subtotal": float(r["subtotal"]) if ("subtotal" in keys and r["subtotal"] is not None) else 0.0,
        "category": r["category"] if ("category" in keys and r["category"]) else "Uncategorized",
    }
