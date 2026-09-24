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
    
    # Preload DONUT model on startup to avoid first-request delay
    try:
        log_info("Preloading DONUT model...")
        from ocr.donut_engine import get_processor
        get_processor()
        log_info("✅ DONUT model preloaded and ready!")
    except Exception as e:
        log_error(f"⚠️ DONUT preload failed: {e}")
        log_info("Model will load on first receipt upload instead.")


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
    currency: str = "USD"


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


@app.get("/api/v1/receipts/{bill_id}/line-items")
def get_receipt_line_items(bill_id: str, user_email: str = Depends(get_current_user_email)):
    """Fetch line items for a specific receipt."""
    from database.db import get_db
    
    db = get_db()
    cursor = db.execute(
        """
        SELECT item_name, quantity, unit_price, total_price
        FROM line_items
        WHERE bill_id = ? AND user_email = ?
        ORDER BY id
        """,
        (bill_id, user_email),
    )
    
    items = []
    for row in cursor.fetchall():
        items.append({
            "name": row["item_name"],
            "quantity": row["quantity"],
            "unit_price": row["unit_price"],
            "total_price": row["total_price"],
        })
    
    db.close()
    return {"bill_id": bill_id, "line_items": items}


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
# UPLOAD + OCR — Single and Batch Upload Support
# ─────────────────────────────────────────────────────────────────────────
@app.post("/api/v1/receipts/upload", response_model=ReceiptBase, status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    file: UploadFile = File(...),
    user_email: str = Depends(get_current_user_email),
):
    """
    Accepts a single file upload (image or PDF), runs it through the
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


class BatchUploadResult(BaseModel):
    total_files: int
    successful: int
    failed: int
    duplicates: int
    results: List[dict]


@app.post("/api/v1/receipts/upload/batch", response_model=BatchUploadResult)
async def upload_multiple_receipts(
    files: List[UploadFile] = File(...),
    user_email: str = Depends(get_current_user_email),
):
    """
    Accepts multiple file uploads (images or PDFs) and processes them in batch.
    Returns detailed results for each file including success/failure status.
    
    - Processes all files even if some fail
    - Skips duplicates without failing the entire batch
    - Returns comprehensive results for UI feedback
    """
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Limit batch size to prevent resource exhaustion
    MAX_BATCH_SIZE = 20
    if len(files) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"Too many files. Maximum {MAX_BATCH_SIZE} files per batch"
        )
    
    results = []
    successful_count = 0
    failed_count = 0
    duplicate_count = 0
    
    log_info(f"Batch upload started: {len(files)} files for user {user_email}")
    
    for idx, file in enumerate(files):
        file_result = {
            "filename": file.filename,
            "status": "processing",
            "message": "",
            "receipt_data": None
        }
        
        try:
            # Read file
            file_bytes = await file.read()
            
            # Validate file
            try:
                validate_uploaded_file(file.filename, len(file_bytes))
            except ValueError as e:
                file_result["status"] = "failed"
                file_result["message"] = f"Validation error: {str(e)}"
                failed_count += 1
                results.append(file_result)
                continue
            
            # Process with OCR
            try:
                parsed = process_receipt_file(file_bytes, file.filename)
            except OCRProcessingError as e:
                file_result["status"] = "failed"
                file_result["message"] = f"OCR error: {str(e)}"
                failed_count += 1
                log_error(f"OCR failed for {file.filename} in batch ({user_email}): {e}")
                results.append(file_result)
                continue
            except Exception as e:
                file_result["status"] = "failed"
                file_result["message"] = f"Processing error: {str(e)}"
                failed_count += 1
                log_error(f"Unexpected error for {file.filename} in batch ({user_email}): {e}")
                results.append(file_result)
                continue
            
            # Check for duplicates
            if check_receipt_duplicate(
                parsed["bill_id"], 
                parsed["vendor"], 
                parsed["date"], 
                parsed["amount"], 
                user_email
            ):
                file_result["status"] = "duplicate"
                file_result["message"] = "Receipt already exists in your vault"
                file_result["receipt_data"] = parsed
                duplicate_count += 1
                results.append(file_result)
                continue
            
            # Save to database
            save_receipt(parsed, user_email)
            file_result["status"] = "success"
            file_result["message"] = "Receipt processed and saved successfully"
            file_result["receipt_data"] = parsed
            successful_count += 1
            results.append(file_result)
            
        except Exception as e:
            # Catch any unexpected errors
            file_result["status"] = "failed"
            file_result["message"] = f"Unexpected error: {str(e)}"
            failed_count += 1
            log_error(f"Critical error processing {file.filename} in batch: {e}")
            results.append(file_result)
    
    log_info(
        f"Batch upload completed for {user_email}: "
        f"{successful_count} success, {failed_count} failed, {duplicate_count} duplicates"
    )
    
    return BatchUploadResult(
        total_files=len(files),
        successful=successful_count,
        failed=failed_count,
        duplicates=duplicate_count,
        results=results
    )


# ─────────────────────────────────────────────────────────────────────────
# BUDGET SUMMARY — powers a "spent this month vs budget" widget
# ─────────────────────────────────────────────────────────────────────────
@app.get("/api/v1/budget/summary")
def budget_summary(user_email: str = Depends(get_current_user_email)):
    """Enhanced budget summary with burn rate analysis from advanced_analytics."""
    from analytics.advanced_analytics import calculate_burn_rate
    
    user = get_user_by_email(user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    receipts = fetch_all_receipts(user_email)
    current_month = datetime.now().strftime("%Y-%m")
    spent_this_month = sum(r["amount"] for r in receipts if r["date"].startswith(current_month))
    budget = float(user.get("budget") or 0)
    
    # Calculate burn rate for detailed insights
    days_passed = datetime.now().day
    burn_rate_data = calculate_burn_rate(spent_this_month, budget, days_passed) if budget > 0 else None

    response = {
        "budget": budget,
        "spent_this_month": spent_this_month,
        "remaining": max(budget - spent_this_month, 0),
        "percent_used": round((spent_this_month / budget) * 100, 1) if budget else 0,
    }
    
    # Add burn rate insights if available
    if burn_rate_data:
        response["burn_rate"] = burn_rate_data
    
    return response


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


@app.get("/api/v1/analytics/forecast")
def forecast_spending(user_email: str = Depends(get_current_user_email)):
    """
    Predicts next month spending using multiple forecasting methods.
    Returns simple average, polynomial regression predictions, and burn rate analysis.
    """
    import pandas as pd
    from analytics.forecasting import predict_next_month_spending, predict_spending_polynomial
    from analytics.advanced_analytics import calculate_burn_rate

    receipts = fetch_all_receipts(user_email)
    if not receipts:
        return {
            "simple_forecast": 0,
            "daily_average": 0,
            "polynomial_forecast": [],
            "burn_rate": None,
            "message": "No receipt data available for forecasting"
        }

    df = pd.DataFrame(receipts)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    # Simple moving average forecast
    predicted_spend, daily_avg = predict_next_month_spending(df)

    # Polynomial regression forecast
    poly_forecast = predict_spending_polynomial(df, degree=2)
    poly_data = []
    if poly_forecast is not None and not poly_forecast.empty:
        poly_data = poly_forecast.to_dict(orient="records")
        # Convert datetime to string for JSON serialization
        for item in poly_data:
            if "date" in item:
                item["date"] = item["date"].strftime("%Y-%m-%d")

    # Burn rate analysis
    user = get_user_by_email(user_email)
    monthly_budget = float(user.get("budget", 0)) if user else 0
    current_month = datetime.now().strftime("%Y-%m")
    current_month_receipts = [r for r in receipts if r["date"].startswith(current_month)]
    current_spend = sum(r["amount"] for r in current_month_receipts)
    days_passed = datetime.now().day
    
    burn_rate = calculate_burn_rate(current_spend, monthly_budget, days_passed)

    return {
        "simple_forecast": round(predicted_spend, 2),
        "daily_average": round(daily_avg, 2),
        "polynomial_forecast": poly_data[:10] if poly_data else [],  # First 10 days
        "burn_rate": burn_rate,
        "forecast_summary": {
            "method": "Moving Average + Polynomial Regression",
            "confidence": "Medium" if len(receipts) > 10 else "Low",
            "data_points": len(receipts)
        }
    }


@app.get("/api/v1/analytics/trends")
def spending_trends(window_days: int = 7, user_email: str = Depends(get_current_user_email)):
    """
    Calculates moving averages and spending trends over time.
    Useful for visualizing spending patterns in charts.
    """
    import pandas as pd
    from analytics.forecasting import calculate_moving_averages

    receipts = fetch_all_receipts(user_email)
    if not receipts:
        return {"daily_spending": [], "moving_average": [], "message": "No data available"}

    df = pd.DataFrame(receipts)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    if df.empty:
        return {"daily_spending": [], "moving_average": [], "message": "No valid dates found"}

    daily_spend, moving_avg = calculate_moving_averages(df, window_days=window_days)

    # Convert to list of dicts for JSON response
    daily_data = [
        {"date": date.strftime("%Y-%m-%d"), "amount": float(amount)}
        for date, amount in daily_spend.items()
    ]

    ma_data = [
        {"date": date.strftime("%Y-%m-%d"), "moving_average": float(avg)}
        for date, avg in moving_avg.items()
        if pd.notna(avg)
    ]

    return {
        "daily_spending": daily_data[-30:],  # Last 30 days
        "moving_average": ma_data[-30:],     # Last 30 days
        "window_days": window_days,
        "total_days": len(daily_data)
    }


@app.get("/api/v1/analytics/search")
def smart_search(q: str, user_email: str = Depends(get_current_user_email)):
    """
    Enhanced search using the analytics search module.
    Searches across vendor names and categories with fuzzy matching.
    """
    import pandas as pd
    from analytics.search import search_receipts as analytics_search

    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")

    receipts = fetch_all_receipts(user_email)
    if not receipts:
        return []

    df = pd.DataFrame(receipts)
    result_df = analytics_search(df, q.strip())

    if result_df.empty:
        return []

    return result_df.to_dict(orient="records")


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
