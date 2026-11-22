from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from typing import Optional
from services.scraper_service import scrape_nfce_items
from services.gemini_service import analyze_receipt_image
from services.auth_service import get_current_user
from config.firebase_config import get_db
from datetime import datetime

router = APIRouter()

class QRCodeRequest(BaseModel):
    url: str
    # user_id removido daqui, pois pegaremos automaticamente do token JWT

@router.post("/scrape-qrcode")
def process_and_save_qrcode(
    payload: QRCodeRequest, 
    current_user: dict = Depends(get_current_user)
):
    """Processa o QR Code da NFC-e via Scraper e salva os itens automaticamente para o usuário logado."""
    try:
        uid = current_user["uid"]
        
        # 1. Executa o scraping
        data = scrape_nfce_items(payload.url)
        items_list = data.get("items", [])
        
        db = get_db()
        saved_items = []

        # 2. Varre os itens encontrados e salva um a um no Firestore
        for item in items_list:
            doc_ref = db.collection("items").document()
            
            item_data = {
                "id": doc_ref.id,
                "name": item.get("name", "Produto Desconhecido"),
                "quantity": str(item.get("quantity", "1")),
                "unit": item.get("unit", "UN"),
                "category": "", # Categoria padrão para itens de nota
                "expiration_date": "", # O usuário pode preencher depois no app
                "user_id": uid  # <--- Inserido automaticamente do token JWT
            }
            
            doc_ref.set(item_data)
            saved_items.append(item_data)

        return {
            "status": "success",
            "source": "scraper",
            "store": data.get("store", "Desconhecido"),
            "saved_count": len(saved_items),
            "items": saved_items
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ocr-image")
async def process_and_save_ocr_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Processa imagem da nota fiscal via Gemini OCR e salva os itens automaticamente para o usuário logado."""
    try:
        uid = current_user["uid"]
        image_bytes = await file.read()
        print("DEBUG OCR -> filename:", file.filename, "content_type:", file.content_type, "len:", len(image_bytes), "head:", image_bytes[:10])

        if not image_bytes:
            raise HTTPException(status_code=400, detail="Arquivo de imagem vazio.")

        result_json = analyze_receipt_image(
            image_bytes=image_bytes,
            mime_type=file.content_type or "image/jpeg",
        )

        raw_items = (
            result_json.get("items", [])
            if isinstance(result_json, dict)
            else result_json
        )
        items_list = [i for i in raw_items if isinstance(i, dict)] if isinstance(raw_items, list) else []

        db = get_db()
        saved_items = []

        for item in items_list:
            doc_ref = db.collection("items").document()

            item_data = {
                "id": doc_ref.id,
                "name": str(item.get("name") or "Produto Desconhecido").strip(),
                "quantity": str(item.get("quantity") or "1"),
                "unit": str(item.get("unit") or "UN"),
                "category": "",
                "expiration_date": "",
                "user_id": uid,
            }

            doc_ref.set(item_data)
            saved_items.append(item_data)

        store_name = (
            result_json.get("store", "Desconhecido")
            if isinstance(result_json, dict)
            else "Desconhecido"
        )

        return {
            "status": "success",
            "source": "gemini_ocr",
            "store": store_name,
            "saved_count": len(saved_items),
            "items": saved_items,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))