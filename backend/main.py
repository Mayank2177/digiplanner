from fastapi import FastAPI
from pydantic import BaseModel
from database import init_db, insert_receipt
from ocr_engine import extract_data

app = FastAPI()

class Payload(BaseModel):
    device_id: str
    target_image: str

@app.on_event("startup")
def startup():
    init_db()

@app.post("/upload")
def upload(payload: Payload):
    image_name = payload.target_image

    # Step 1: OCR simulation
    extracted = extract_data(image_name)

    # Step 2: Insert into DB
    success = insert_receipt({
        "device_id": payload.device_id,
        "image_name": image_name,
        "merchant": extracted["merchant"],
        "amount": extracted["amount"],
        "date": extracted["date"]
    })

    if not success:
        return {"status": "duplicate"}

    return {"status": "success"}
