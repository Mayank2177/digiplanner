from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config.config import APP_TITLE, APP_VERSION, CORS_ORIGINS
from database.db import init_db
from database.queries import (
    fetch_all_receipts,
    search_receipts,
    get_receipt_by_id,
    save_receipt,
    update_receipt,
    delete_receipt,
    check_receipt_duplicate,
    get_user_by_email,
    create_user,
    update_user_budget,
)
from auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_email,
)
from utils.validators import is_valid_email, validate_uploaded_file
from utils.logger import log_error, log_info
from ocr.receipt_pipeline import process_receipt_file, OCRProcessingError

# ─────────────────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=APP_TITLE,
    description="REST API for receipt OCR, expense tracking, and ERP integration",
    version=APP_VERSION,
)

# Allows your React app (localhost:3000 by default — see config.CORS_ORIGINS
# / the CORS_ORIGINS env var) to actually call this API from the browser.
# This was completely missing before; every fetch() from the frontend
# would have been blocked by the browser regardless of any other fix.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    log_info("Database initialized. Receipt Vault API is starting up.")


# ─────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────
class SignupRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    name: Optional[str] = ""
    company: Optional[str] = ""
    phone: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str
    name: Optional[str] = ""


class UserProfile(BaseModel):
    email: str
    name: Optional[str] = ""
    company: Optional[str] = ""
    phone: Optional[str] = ""
    budget: float = 50000.0


class BudgetUpdateRequest(BaseModel):
    budget: float = Field(gt=0)


class ReceiptBase(BaseModel):
    bill_id: str
    vendor: str
    date: str
    amount: float
    tax: float
    subtotal: float
    category: str


class ReceiptUpdateRequest(BaseModel):
    vendor: Optional[str] = None
    date: Optional[str] = None
    amount: Optional[float] = None
    tax: Optional[float] = None
    subtotal: Optional[float] = None
    category: Optional[str] = None


class ERPExportResponse(BaseModel):
    erp_system: str
    sync_status: str
    sync_time: str
    exported_records: int
    payload_preview: dict


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# ─────────────────────────────────────────────────────────────────────────
# Root / health
# ─────────────────────────────────────────────────────────────────────────
@app.get("/")
def read_root():
    return {"message": "Receipt Vault API is online", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ─────────────────────────────────────────────────────────────────────────
# AUTH — did not exist at all before. LoginPage.js / SignupPage.js should
# call these instead of their current setTimeout()-based fakes.
# ─────────────────────────────────────────────────────────────────────────
@app.post("/api/v1/auth/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest):
    if not is_valid_email(payload.email):
        raise HTTPException(status_code=400, detail="Invalid email address")

    if get_user_by_email(payload.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    password_hash = hash_password(payload.password)
    user = create_user(
        email=payload.email,
        password_hash=password_hash,
        name=payload.name or "",
        company=payload.company or "",
        phone=payload.phone or "",
    )
    token = create_access_token(user["email"])
    return AuthResponse(access_token=token, email=user["email"], name=user.get("name", ""))


@app.post("/api/v1/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token(user["email"])
    return AuthResponse(access_token=token, email=user["email"], name=user.get("name", ""))


@app.get("/api/v1/auth/me", response_model=UserProfile)
def get_me(user_email: str = Depends(get_current_user_email)):
    user = get_user_by_email(user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(
        email=user["email"],
        name=user.get("name", ""),
        company=user.get("company", ""),
        phone=user.get("phone", ""),
        budget=user.get("budget", 50000.0),
    )


@app.put("/api/v1/auth/budget", response_model=UserProfile)
def set_budget(payload: BudgetUpdateRequest, user_email: str = Depends(get_current_user_email)):
    update_user_budget(user_email, payload.budget)
    return get_me(user_email)


# ─────────────────────────────────────────────────────────────────────────
# RECEIPTS — every function below now requires a valid JWT and is scoped
# to that user's own data (via get_current_user_email), instead of the old
# broken st.session_state lookup.
# ─────────────────────────────────────────────────────────────────────────
@app.get("/api/v1/receipts", response_model=List[ReceiptBase])
def get_receipts(
    vendor: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    user_email: str = Depends(get_current_user_email),
):
    """Fetch (optionally filtered) receipts for the logged-in user. Powers the Dashboard page."""
    try:
        if any([vendor, category, start_date, end_date, min_amount, max_amount]):
            return search_receipts(
                user_email=user_email,
                vendor=vendor,
                category=category,
                start_date=start_date,
                end_date=end_date,
                min_amount=min_amount,
                max_amount=max_amount,
            )
        return fetch_all_receipts(user_email)
    except Exception as e:
        log_error(f"get_receipts failed for {user_email}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/receipts/{bill_id}", response_model=ReceiptBase)
def get_receipt(bill_id: str, user_email: str = Depends(get_current_user_email)):
    receipt = get_receipt_by_id(bill_id, user_email)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


@app.patch("/api/v1/receipts/{bill_id}", response_model=ReceiptBase)
def edit_receipt(
    bill_id: str,
    payload: ReceiptUpdateRequest,
    user_email: str = Depends(get_current_user_email),
):
    update_data = {k: v for k, v in payload.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    updated = update_receipt(bill_id, update_data, user_email)
    if not updated:
        raise HTTPException(status_code=404, detail="Receipt not found")

    receipt = get_receipt_by_id(bill_id, user_email)
    return receipt


@app.delete("/api/v1/receipts/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_receipt(bill_id: str, user_email: str = Depends(get_current_user_email)):
    deleted = delete_receipt(bill_id, user_email)
    if not deleted:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return None


# ─────────────────────────────────────────────────────────────────────────
# UPLOAD + OCR — this endpoint DID NOT WORK AT ALL before. It returned
# {"status": "WIP"} unconditionally. This is the real implementation your
# DashboardPage.js upload UI should call instead of its mock setTimeout.
# ─────────────────────────────────────────────────────────────────────────
@app.post("/api/v1/receipts/upload", response_model=ReceiptBase, status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    file: UploadFile = File(...),
    user_email: str = Depends(get_current_user_email),
):
    """
    Accepts a real multipart file upload (image or PDF), runs it through the
    OCR pipeline (ocr/receipt_pipeline.py), parses out vendor/date/amount/tax,
    checks for duplicates, and saves it to the database for the logged-in user.
    """
    file_bytes = await file.read()

    try:
        validate_uploaded_file(file.filename, len(file_bytes))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        parsed = process_receipt_file(file_bytes, file.filename)
    except OCRProcessingError as e:
        log_error(f"OCR failed for {file.filename} ({user_email}): {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        log_error(f"Unexpected OCR error for {file.filename} ({user_email}): {e}")
        raise HTTPException(status_code=500, detail="Failed to process the uploaded file")

    if check_receipt_duplicate(parsed["bill_id"], parsed["vendor"], parsed["date"], parsed["amount"], user_email):
        raise HTTPException(status_code=409, detail="This receipt appears to already be in your vault")

    save_receipt(parsed, user_email)
    return parsed


# ─────────────────────────────────────────────────────────────────────────
# BUDGET SUMMARY — powers a "spent this month vs budget" widget
# ─────────────────────────────────────────────────────────────────────────
@app.get("/api/v1/budget/summary")
def budget_summary(user_email: str = Depends(get_current_user_email)):
    user = get_user_by_email(user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    receipts = fetch_all_receipts(user_email)
    current_month = datetime.now().strftime("%Y-%m")
    spent_this_month = sum(r["amount"] for r in receipts if r["date"].startswith(current_month))
    budget = float(user.get("budget") or 0)

    return {
        "budget": budget,
        "spent_this_month": spent_this_month,
        "remaining": max(budget - spent_this_month, 0),
        "percent_used": round((spent_this_month / budget) * 100, 1) if budget else 0,
    }


# ─────────────────────────────────────────────────────────────────────────
# ANALYTICS — wires up the previously-unused analytics/ module
# ─────────────────────────────────────────────────────────────────────────
@app.get("/api/v1/analytics/spend-by-category")
def spend_by_category(user_email: str = Depends(get_current_user_email)):
    receipts = fetch_all_receipts(user_email)
    totals: dict = {}
    for r in receipts:
        totals[r["category"]] = totals.get(r["category"], 0) + r["amount"]
    return [{"category": k, "total": v} for k, v in sorted(totals.items(), key=lambda x: -x[1])]


@app.get("/api/v1/analytics/subscriptions")
def detect_subscriptions_endpoint(user_email: str = Depends(get_current_user_email)):
    """Uses analytics/advanced_analytics.py to flag likely recurring subscriptions."""
    import pandas as pd
    from analytics.advanced_analytics import detect_subscriptions

    receipts = fetch_all_receipts(user_email)
    if not receipts:
        return []

    df = pd.DataFrame(receipts)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    result = detect_subscriptions(df)
    return result.to_dict(orient="records") if hasattr(result, "to_dict") else []


# ─────────────────────────────────────────────────────────────────────────
# CHAT — a real (if simple) implementation over the user's own data.
# There is no LLM wired in here (the original repo had none either) — this
# answers a handful of common questions directly from the database so the
# ChatPage.js has something genuine to call instead of its setTimeout mock.
# For a true conversational AI, plug an LLM API call in where noted below.
# ─────────────────────────────────────────────────────────────────────────
@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, user_email: str = Depends(get_current_user_email)):
    message = payload.message.lower()
    receipts = fetch_all_receipts(user_email)

    if not receipts:
        return ChatResponse(reply="You don't have any receipts saved yet — upload one to get started!")

    total_spend = sum(r["amount"] for r in receipts)
    current_month = datetime.now().strftime("%Y-%m")
    month_spend = sum(r["amount"] for r in receipts if r["date"].startswith(current_month))

    if "this month" in message or "month" in message:
        return ChatResponse(reply=f"You've spent ₹{month_spend:,.2f} so far this month across {sum(1 for r in receipts if r['date'].startswith(current_month))} receipts.")
    if "total" in message or "overall" in message:
        return ChatResponse(reply=f"Your total tracked spend is ₹{total_spend:,.2f} across {len(receipts)} receipts.")
    if "vendor" in message or "merchant" in message or "where" in message:
        top_vendor = max({r["vendor"] for r in receipts}, key=lambda v: sum(r["amount"] for r in receipts if r["vendor"] == v))
        return ChatResponse(reply=f"Your top vendor by spend is {top_vendor}.")

    # NOTE: To make this a true AI assistant, call an LLM API here (e.g. the
    # Anthropic API) with `receipts` as context and `payload.message` as the
    # user's question, and return the model's response instead.
    return ChatResponse(
        reply="I can tell you about your total spend, this month's spend, or your top vendor — ask me about one of those!"
    )


# ─────────────────────────────────────────────────────────────────────────
# ERP EXPORT — kept from the original, cleaned up to use the scoped queries
# ─────────────────────────────────────────────────────────────────────────
@app.post("/api/v1/erp/sync", response_model=ERPExportResponse)
def sync_to_erp(system: str = "SAP", user_email: str = Depends(get_current_user_email)):
    """
    Simulated ERP synchronization endpoint — formats the user's receipts
    into common ERP schemas (SAP-style, Oracle-style, ERPNext). This does
    NOT actually push data to a live ERP system; wiring a real SAP/Oracle/
    NetSuite/QuickBooks integration requires that vendor's SDK and OAuth
    credentials, which is a separate, larger integration task.
    """
    receipts = fetch_all_receipts(user_email)

    if system == "ERPNext":
        erp_payload = {
            "doctype": "Purchase Invoice",
            "supplier": receipts[0]["vendor"] if receipts else "N/A",
            "posting_date": receipts[0]["date"] if receipts else "N/A",
            "apply_tds": 0,
            "items": [
                {
                    "item_code": "Generic Expense",
                    "qty": 1,
                    "rate": r["amount"],
                    "amount": r["amount"],
                    "description": f"Receipt {r['bill_id']} from {r['vendor']}",
                }
                for r in receipts[:5]
            ],
        }
    else:
        erp_payload = {
            "Header": {
                "System": system,
                "TransferID": f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "Organization": "ReceiptVault-Client",
            },
            "Invoices": [
                {
                    "ExternalInvID": r["bill_id"],
                    "Supplier": r["vendor"],
                    "PostingDate": r["date"],
                    "GrossAmount": r["amount"],
                    "TaxAmount": r["tax"],
                    "Currency": "INR",
                }
                for r in receipts[:5]
            ],
        }

    return {
        "erp_system": system,
        "sync_status": "SUCCESS",
        "sync_time": datetime.now().isoformat(),
        "exported_records": len(receipts),
        "payload_preview": erp_payload,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
