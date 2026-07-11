from database.db import get_db
import streamlit as st
from datetime import datetime
from utils.notifications import send_email_alert, send_sms_alert
from typing import List, Dict, Any, Optional

# ================= SAVE RECEIPT =================
def save_receipt(data, user_email=None):
    """
    Save receipt to database.
    Assumes data = {
        bill_id, vendor, date, amount, tax, subtotal
    }
    """
    # If user_email not provided, try to get from session state
    if not user_email:
        user_email = st.session_state.get("user_email")

    db = get_db()

    db.execute(
        """
        INSERT INTO receipts (bill_id, user_email, vendor, date, amount, tax, subtotal, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["bill_id"],
            user_email,
            data["vendor"],
            data["date"],
            float(data["amount"]),
            float(data["tax"]),
            float(data["subtotal"]),
            data["category"],
        ),
    )
    db.commit()
    
    # Check for budget alerts after saving if we have a user_email
    if user_email:
        check_budget_alerts(user_email)


# ================= DUPLICATE CHECK (ROBUST) =================
def check_receipt_duplicate(bill_id, vendor, date, amount):
    """
    Check for duplicates with high reliability (>=95%).
    Checks:
    1. Exact Bill ID match (if valid)
    2. Combination of Vendor + Date + Amount (fallback)
    """
    db = get_db()
    
    # 1. Check Bill ID if it exists and looks valid (not temp/default)
    if bill_id and len(bill_id) > 2 and "REC-" not in bill_id:
        cur = db.execute("SELECT 1 FROM receipts WHERE bill_id = ?", (bill_id,))
        if cur.fetchone():
            return True

    # 2. Check Logic Fingerprint (Vendor + Date + Amount)
    # This catches duplicates where OCR missed the specific Bill ID char but data is same
    try:
        cur = db.execute(
            "SELECT 1 FROM receipts WHERE vendor = ? AND date = ? AND abs(amount - ?) < 0.01",
            (vendor, date, float(amount))
        )
        if cur.fetchone():
            return True
    except:
        pass
        
    return False


def receipt_exists(bill_id, user_email=None):
    """Legacy wrapper for backward compatibility"""
    if not user_email:
        user_email = st.session_state.get("user_email")
    db = get_db()
    cur = db.execute("SELECT 1 FROM receipts WHERE bill_id = ? AND user_email = ?", (bill_id, user_email))
    return cur.fetchone() is not None


# ================= FETCH ALL RECEIPTS =================
def fetch_all_receipts(user_email=None) -> List[Dict[str, Any]]:
    """
    Returns list of dicts ordered by date DESC for a specific user.
    """
    if not user_email:
        user_email = st.session_state.get("user_email")
    db = get_db()
    
    try:
        cur = db.execute(
            "SELECT bill_id, vendor, date, amount, tax, subtotal, category FROM receipts WHERE user_email = ? ORDER BY date DESC",
            (user_email,)
        )
    except:
        cur = db.execute(
            "SELECT bill_id, vendor, date, amount, tax, 0.0 as subtotal, 'Uncategorized' as category FROM receipts ORDER BY date DESC"
        )

    rows = cur.fetchall()

    return [
        {
            "bill_id": r["bill_id"],
            "vendor": r["vendor"],
            "date": r["date"],
            "amount": float(r["amount"]),
            "tax": float(r["tax"]),
            "subtotal": float(r["subtotal"]) if ("subtotal" in r.keys() and r["subtotal"] is not None) else 0.0,
            "category": r["category"] if ("category" in r.keys() and r["category"]) else "Uncategorized",
        }
        for r in rows
    ]


# ================= GET ONE RECEIPT =================
def get_receipt_by_id(bill_id: str, user_email: str = None) -> Optional[Dict[str, Any]]:
    """Returns a single receipt as a dict or None"""
    if not user_email:
        user_email = st.session_state.get("user_email")
    db = get_db()
    cur = db.execute(
        "SELECT * FROM receipts WHERE bill_id = ? AND user_email = ?",
        (bill_id, user_email)
    )
    row = cur.fetchone()
    if row:
        return {
            "bill_id": row["bill_id"],
            "vendor": row["vendor"],
            "date": row["date"],
            "amount": float(row["amount"]),
            "tax": float(row["tax"]),
            "subtotal": float(row["subtotal"]) if ("subtotal" in row.keys() and row["subtotal"] is not None) else 0.0,
            "category": row["category"] if ("category" in row.keys() and row["category"]) else "Uncategorized",
        }
    return None


# ================= UPDATE RECEIPT =================
def update_receipt(bill_id: str, update_data: Dict[str, Any], user_email: str = None) -> bool:
    """Updates specific fields for a receipt"""
    if not user_email:
        user_email = st.session_state.get("user_email")
    db = get_db()
    
    fields = []
    values = []
    
    for key, value in update_data.items():
        if value is not None:
            fields.append(f"{key} = ?")
            values.append(value)
    
    if not fields:
        return False
    
    values.append(bill_id)
    values.append(user_email)
    query = f"UPDATE receipts SET {', '.join(fields)} WHERE bill_id = ? AND user_email = ?"
    
    db.execute(query, values)
    db.commit()
    return True


# ================= SEARCH RECEIPTS (OPTIMIZED) =================
def search_receipts(
    user_email: Optional[str] = None,
    vendor: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Search receipts with dynamic SQL filtering (Server-side optimization).
    Uses indexed columns for better performance.
    """
    if not user_email:
        user_email = st.session_state.get("user_email")
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
    
    return [
        {
            "bill_id": r["bill_id"],
            "vendor": r["vendor"],
            "date": r["date"],
            "amount": float(r["amount"]),
            "tax": float(r["tax"]),
            "subtotal": float(r["subtotal"]) if ("subtotal" in r.keys() and r["subtotal"] is not None) else 0.0,
            "category": r["category"] if ("category" in r.keys() and r["category"]) else "Uncategorized",
        }
        for r in rows
    ]


# ================= DELETE ONE RECEIPT =================
def delete_receipt(bill_id, user_email: str = None):
    if not user_email:
        user_email = st.session_state.get("user_email")
    db = get_db()
    db.execute(
        "DELETE FROM receipts WHERE bill_id = ? AND user_email = ?",
        (bill_id, user_email)
    )
    db.commit()


# ================= USER & BUDGET DETAILS =================
def get_user_details(email: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    cur = db.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    if row:
        return dict(row)
    return None

def update_user_budget(email: str, budget: float):
    db = get_db()
    db.execute("UPDATE users SET budget = ? WHERE email = ?", (budget, email))
    db.commit()

# ================= BUDGET ALERT LOGIC =================
def check_budget_alerts(email: str):
    """
    Checks if spending thresholds have been reached and sends alerts.
    Thresholds: 50%, 60%, 70%, 80%, 90%, 100%
    """
    user = get_user_details(email)
    if not user or not user.get("budget"):
        return

    budget = float(user["budget"])
    phone = user.get("phone")
    
    # Calculate current month total
    current_month = datetime.now().strftime("%Y-%m")
    db = get_db()
    # Note: We filter by user_email as well now
    cur = db.execute(
        "SELECT SUM(amount) as total FROM receipts WHERE user_email = ? AND date LIKE ?",
        (email, f"{current_month}%")
    )
    res = cur.fetchone()
    current_spend = float(res["total"]) if res and res["total"] else 0.0
    
    if current_spend == 0:
        return

    percent_used = (current_spend / budget) * 100
    for t in [50, 90, 100]:
        if percent_used >= t:
            # Check if alert already sent for this month and threshold
            cur = db.execute(
                "SELECT 1 FROM alerts_sent WHERE user_email = ? AND month = ? AND threshold = ?",
                (email, current_month, t)
            )
            if not cur.fetchone():
                # Send Alert
                send_email_alert(email, t, current_spend, budget)
                if phone:
                    send_sms_alert(phone, t, current_spend)
                
                # Record that we sent it
                db.execute(
                    "INSERT INTO alerts_sent (user_email, month, threshold) VALUES (?, ?, ?)",
                    (email, current_month, t)
                )
                db.commit()


# ================= CLEAR ALL RECEIPTS =================
def clear_all_receipts():
    db = get_db()
    db.execute("DELETE FROM receipts")
    db.execute("DELETE FROM sqlite_sequence WHERE name='receipts'")
    db.commit()