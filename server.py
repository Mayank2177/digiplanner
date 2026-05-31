# server.py — Edge AI Receipt Processor
# Run: python server.py
# Then in another terminal: lt --port 8000

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import hashlib
import os
from datetime import datetime

app = FastAPI(title="Edge AI Receipt Processor")

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
            merchant_name TEXT,
            total_amount REAL,
            transaction_date TEXT,
            ocr_text TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()
    print("Database initialized")

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

def simulate_ocr(image_name):
    """
    Simulated OCR — replace with pytesseract later
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
    
    # Simulate OCR / AI Processing
    print("Running OCR simulation...")
    extracted = simulate_ocr(payload.target_image)
    
    # Save to database
    cursor.execute("""
        INSERT INTO receipts 
        (device_id, image_name, image_hash, merchant_name, total_amount, transaction_date, ocr_text, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payload.device_id,
        payload.target_image,
        image_hash,
        extracted["merchant_name"],
        extracted["total_amount"],
        extracted["transaction_date"],
        extracted["ocr_text"],
        "success"
    ))
    receipt_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"SAVED to DB | ID: {receipt_id} | Merchant: {extracted['merchant_name']} | Amount: ${extracted['total_amount']}")
    print(f"{'='*50}\n")
    
    return {
        "status": "success",
        "message": "Receipt processed and stored",
        "receipt_id": receipt_id,
        "duplicate": False,
        "merchant": extracted["merchant_name"],
        "amount": extracted["total_amount"]
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

@app.get("/health")
async def health_check():
    return {"status": "online", "server": "Edge AI Processor"}

# ── Run Server ──
if __name__ == "__main__":
    import uvicorn
    print("="*50)
    print("Edge AI Receipt Processor Server")
    print(f"Database: {os.path.abspath(DB_PATH)}")
    print(f"Image Folder: {os.path.abspath(IMAGE_FOLDER)}")
    print("="*50)
    print("Starting server on http://0.0.0.0:8000")
    print("Run 'lt --port 8000' in another terminal to expose")
    print("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8000)