# Edge AI Receipt Processor - Wokwi Integration

## Overview
This server connects your **Wokwi ESP32/PicoW simulator** to the **DONUT CORD-v2 AI extraction pipeline**, enabling real-time receipt processing from IoT devices.

## Architecture
```
Wokwi Simulator (main.py)
    ↓ HTTPS
Cloudflare/Pipedream
    ↓ HTTPS  
Edge Server (server.py on localhost:8080)
    ↓
DONUT CORD-v2 AI Model
    ↓
SQLite Database (analytics_ledger.db)
```

## Features
- ✅ **Real DONUT AI Extraction** (replaced mock OCR)
- ✅ **Line Items Support** - Extracts individual items from receipts
- ✅ **Multi-currency** - Supports USD, INR, etc.
- ✅ **Duplicate Detection** - MD5 hash-based deduplication
- ✅ **Financial Validation** - Subtotal + Tax = Total checks
- ✅ **RESTful API** - Easy integration with any device

## Setup

### 1. Install Dependencies
```bash
cd backend
pip install fastapi uvicorn pillow transformers torch
```

### 2. Prepare Receipt Images
Place receipt images in `./receipts/` folder:
```bash
mkdir -p backend/server/receipts
cp your-receipts/*.jpg backend/server/receipts/
```

### 3. Start Server
```bash
cd backend/server
python server.py
```

Server will start on `http://0.0.0.0:8080`

### 4. Expose via Localtunnel (for Wokwi)
In another terminal:
```bash
npm install -g localtunnel
lt --port 8080
```

You'll get a public URL like: `https://abc123.loca.lt`

### 5. Update Wokwi main.py
Edit `main.py` line 15:
```python
SERVER_URL = "https://your-localtunnel-url.loca.lt"  # Replace with your URL
```

### 6. Run Wokwi Simulator
1. Open https://wokwi.com
2. Upload `main.py` and `diagram.json`
3. Click "Start Simulation"
4. Press the button (Pin 15) to capture receipt

## API Endpoints

### POST /upload
**Simulate Wokwi device uploading a receipt**

Request:
```json
{
  "device_id": "PicoW_Node_01",
  "target_image": "1020-receipt.jpg"
}
```

Response:
```json
{
  "status": "success",
  "receipt_id": 1,
  "merchant": "Dona Mercedes Restaurant",
  "amount": 24.47,
  "tax": 2.22,
  "currency": "USD",
  "line_items_count": 4
}
```

### GET /receipts
**Get all processed receipts**

Response:
```json
[
  {
    "id": 1,
    "device_id": "PicoW_Node_01",
    "merchant_name": "Dona Mercedes Restaurant",
    "total_amount": 24.47,
    "tax": 2.22,
    "subtotal": 22.25,
    "currency": "USD",
    "processed_at": "2026-09-23T15:45:00"
  }
]
```

### GET /receipts/{receipt_id}/line-items
**Get line items for a specific receipt**

Response:
```json
{
  "receipt_id": 1,
  "line_items": [
    {"item_name": "Putusa Queso", "quantity": 1, "total_price": 6.75},
    {"item_name": "Platanos Orden", "quantity": 1, "total_price": 7.75},
    {"item_name": "Diet coke", "quantity": 1, "total_price": 1.50},
    {"item_name": "Quesadilla salvadorena", "quantity": 2, "total_price": 4.00}
  ]
}
```

### GET /health
**Check server status**

Response:
```json
{
  "status": "online",
  "server": "Edge AI Processor (DONUT Powered)",
  "model": "DONUT CORD-v2"
}
```

## Testing

### Test Server Locally
```bash
cd backend/server
python test_server.py
```

This will:
1. Check server health
2. Copy test receipt to receipts folder
3. Simulate Wokwi upload
4. Verify DONUT extraction
5. Fetch line items

### Expected Output
```
✅ Server online: Edge AI Processor (DONUT Powered)
✅ Upload successful!
   Merchant: Dona Mercedes Restaurant
   Amount: $24.47
   Line Items: 4
✅ Retrieved 4 line items:
   • Putusa Queso: $6.75
   • Platanos Orden: $7.75
   • Diet coke: $1.50
   • Quesadilla salvadorena x2: $4.00
```

## Database Schema

### receipts table
- `id` - Primary key
- `device_id` - Wokwi device identifier
- `image_name` - Receipt filename
- `image_hash` - MD5 hash for deduplication
- `bill_id` - Receipt number from OCR
- `merchant_name` - Vendor name
- `total_amount` - Total amount
- `tax` - Tax amount
- `subtotal` - Subtotal
- `currency` - Currency code (USD, INR, etc.)
- `transaction_date` - Transaction date
- `category` - Auto-categorized (Food & Dining, Travel, etc.)
- `processed_at` - Timestamp

### line_items table
- `id` - Primary key
- `receipt_id` - Foreign key to receipts
- `item_name` - Item description
- `quantity` - Item quantity
- `unit_price` - Price per unit
- `total_price` - Line item total

## Troubleshooting

### Server won't start
- Check if port 8080 is available: `netstat -an | findstr 8080`
- Make sure you're in the correct directory: `cd backend/server`

### DONUT extraction fails
- Verify images are in `./receipts/` folder
- Check image format (JPG, PNG supported)
- Review logs for specific errors

### Wokwi can't connect
- Ensure localtunnel is running: `lt --port 8080`
- Update `SERVER_URL` in `main.py` with the correct tunnel URL
- Check Wokwi console for connection errors

### Duplicate receipts
- Server uses MD5 hash deduplication
- Same image will return: `{"status": "duplicate"}`
- To reprocess, delete from database or use different image

## Performance
- First request: ~8-10 seconds (model loading)
- Subsequent requests: ~2-3 seconds
- Model preloaded on server startup for faster processing

## Production Deployment

For production, consider:
1. Use proper tunnel service (ngrok Pro, Cloudflare Tunnel)
2. Add authentication (API keys)
3. Use PostgreSQL instead of SQLite
4. Add rate limiting
5. Enable HTTPS
6. Add monitoring/logging
7. Deploy on cloud (AWS, Azure, GCP)

## Credits
- **DONUT Model**: naver-clova-ix/donut-base-finetuned-cord-v2
- **Framework**: FastAPI + Uvicorn
- **Hardware**: Wokwi ESP32/PicoW Simulator
