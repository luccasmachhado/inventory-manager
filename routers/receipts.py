from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from services.scraper_service import scrape_nfce_items
from services.gemini_service import analyze_receipt_image

router = APIRouter()

class QRCodeRequest(BaseModel):
    url: str

@router.post("/scrape-qrcode")
def process_qrcode(payload: QRCodeRequest):
    """Abordagem A: Processa a leitura do QR Code da NFC-e via Web Scraping."""
    try:
        data = scrape_nfce_items(payload.url)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ocr-image")
async def process_ocr_image(file: UploadFile = File(...)):
    """Abordagem B (Fallback): Processa imagem da nota fiscal via Gemini OCR."""
    try:
        image_bytes = await file.read()
        result_json = analyze_receipt_image(image_bytes)
        return {"source": "gemini_ocr", "raw_result": result_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))