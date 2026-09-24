# server.py — Edge AI Receipt Processor (with DONUT Integration)
# Run: python server.py
# Then in another terminal: lt --port 8080

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import hashlib
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from ocr.receipt_pipeline import process_receipt_file, OCRProcessingError
from ocr.image_optimizer import optimize_image_for_ocr
from utils.logger import log_info, log_error
from PIL import Image

app = FastAPI(title="Edge AI Receipt Processor - DONUT Powered")

# ── Paths ──
DB_PATH = "analytics_ledger.db"
IMAGE_FOLDER = "./receipts"

# Ensure folders exist
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# ── Database Setup ──
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            image_name TEXT NOT NULL,
            image_hash TEXT UNIQUE NOT NULL,
            bill_id TEXT,
            merchant_name TEXT,
            total_amount REAL,
            tax REAL,
            subtotal REAL,
            currency TEXT DEFAULT 'USD',
            transaction_date TEXT,
            category TEXT,
            ocr_text TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            unit_price REAL DEFAULT 0.0,
            total_price REAL NOT NULL,
            FOREIGN KEY (receipt_id) REFERENCES receipts(id)
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Database initialized with DONUT schema")

# Initialize on startup
init_db()

# ── Pydantic Models ──
class ReceiptPayload(BaseModel):
    device_id: str
    target_image: str

# ── Helper Functions ──
def get_image_hash(image_path):
    """Generate MD5 hash of image file for deduplication"""
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def process_receipt_with_donut(image_path):
    """
    Real DONUT CORD-v2 extraction - replaces mock OCR
    """
    try:
        log_info(f"🔍 Processing receipt with DONUT: {image_path}")
        
        # Read image file
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Use the same pipeline as main backend
        extracted = process_receipt_file(image_bytes, os.path.basename(image_path))
        
        log_info(f"✅ DONUT extracted: {extracted['vendor']} - ${extracted['amount']}")
        
        return {
            "bill_id": extracted.get("bill_id"),
            "merchant_name": extracted.get("vendor", "Unknown"),
            "total_amount": float(extracted.get("amount", 0)),
            "tax": float(extracted.get("tax", 0)),
            "subtotal": float(extracted.get("subtotal", 0)),
            "transaction_date": extracted.get("date"),
            "currency": extracted.get("currency", "USD"),
            "category": extracted.get("category", "Uncategorized"),
            "line_items": extracted.get("line_items", []),
            "ocr_text": f"DONUT CORD-v2 extraction complete"
        }
    except OCRProcessingError as e:
        log_error(f"❌ DONUT processing failed: {e}")
        raise
    except Exception as e:
        log_error(f"❌ Unexpected error in DONUT processing: {e}")
        raise

def simulate_ocr(image_name):
    """
    DEPRECATED - Kept for fallback only
    """
    # Deterministic mock data based on filename
    hash_val = hash(image_name)
    mock_data = {
        "merchant_name": f"Store_{image_name[:4]}",
        "total_amount": round((hash_val % 10000) / 100, 2),
        "transaction_date": datetime.now().strftime("%Y-%m-%d"),
        "ocr_text": f"Simulated OCR for {image_name}"
    }
    return mock_data

# ── API Endpoints ──
@app.post("/upload")
async def upload_receipt(payload: ReceiptPayload):
    print(f"\n{'='*50}")
    print(f"RECEIVED from {payload.device_id}")
    print(f"Image: {payload.target_image}")
    
    image_path = os.path.join(IMAGE_FOLDER, payload.target_image)
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"ERROR: Image not found: {image_path}")
        raise HTTPException(status_code=404, detail="Image file not found on server")
    
    # Generate hash for deduplication
    image_hash = get_image_hash(image_path)
    if not image_hash:
        raise HTTPException(status_code=500, detail="Could not hash image")
    
    # Check for duplicates
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM receipts WHERE image_hash = ?", (image_hash,))
    existing = cursor.fetchone()
    
    if existing:
        conn.close()
        print(f"DUPLICATE detected! ID: {existing[0]}")
        return {
            "status": "duplicate",
            "message": "Receipt already processed",
            "receipt_id": existing[0],
            "duplicate": True
        }
    
    # Process with DONUT AI (real extraction)
    print("🤖 Running DONUT CORD-v2 AI extraction...")
    try:
        extracted = process_receipt_with_donut(image_path)
    except Exception as e:
        log_error(f"DONUT extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"DONUT extraction failed: {str(e)}")
    
    # Save receipt to database
    cursor.execute("""
        INSERT INTO receipts 
        (device_id, image_name, image_hash, bill_id, merchant_name, total_amount, tax, subtotal, 
         currency, transaction_date, category, ocr_text, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payload.device_id,
        payload.target_image,
        image_hash,
        extracted["bill_id"],
        extracted["merchant_name"],
        extracted["total_amount"],
        extracted["tax"],
        extracted["subtotal"],
        extracted["currency"],
        extracted["transaction_date"],
        extracted["category"],
        extracted["ocr_text"],
        "success"
    ))
    receipt_id = cursor.lastrowid
    
    # Save line items
    line_items = extracted.get("line_items", [])
    if line_items:
        for item in line_items:
            cursor.execute("""
                INSERT INTO line_items (receipt_id, item_name, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
            """, (
                receipt_id,
                item.get("name", "Unknown"),
                item.get("quantity", 1),
                item.get("unit_price", 0.0),
                item.get("total_price", 0.0)
            ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ SAVED to DB | ID: {receipt_id} | Merchant: {extracted['merchant_name']} | Amount: ${extracted['total_amount']:.2f}")
    print(f"   Line Items: {len(line_items)} | Tax: ${extracted['tax']:.2f} | Subtotal: ${extracted['subtotal']:.2f}")
    print(f"{'='*50}\n")
    
    return {
        "status": "success",
        "message": "Receipt processed with DONUT AI",
        "receipt_id": receipt_id,
        "duplicate": False,
        "bill_id": extracted["bill_id"],
        "merchant": extracted["merchant_name"],
        "amount": extracted["total_amount"],
        "tax": extracted["tax"],
        "currency": extracted["currency"],
        "line_items_count": len(line_items)
    }

@app.get("/receipts")
async def get_all_receipts():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM receipts ORDER BY processed_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/receipts/{receipt_id}/line-items")
async def get_receipt_line_items(receipt_id: int):
    """Get line items for a specific receipt"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM line_items WHERE receipt_id = ? ORDER BY id", (receipt_id,))
    rows = cursor.fetchall()
    conn.close()
    return {"receipt_id": receipt_id, "line_items": [dict(row) for row in rows]}

@app.get("/health")
async def health_check():
    return {"status": "online", "server": "Edge AI Processor (DONUT Powered)", "model": "DONUT CORD-v2"}

# ── Run Server ──
if __name__ == "__main__":
    import uvicorn
    print("="*50)
    print("🤖 Edge AI Receipt Processor - DONUT CORD-v2")
    print(f"📁 Database: {os.path.abspath(DB_PATH)}")
    print(f"🖼️  Image Folder: {os.path.abspath(IMAGE_FOLDER)}")
    print("="*50)
    print("🚀 Starting server on http://0.0.0.0:8080")
    print("💡 Run 'lt --port 8080' in another terminal to expose via localtunnel")
    print("="*50)
    
    # Preload DONUT model
    print("⏳ Preloading DONUT model (first request will be fast)...")
    try:
        from ocr.donut_engine import get_donut_processor
        get_donut_processor()
        print("✅ DONUT model loaded!")
    except Exception as e:
        print(f"⚠️  Could not preload DONUT: {e}")
    
    print("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8080)