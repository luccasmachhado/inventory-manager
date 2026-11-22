from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from typing import Optional
from services.scraper_service import scrape_nfce_items
from services.gemini_service import analyze_receipt_image
from services.auth_service import get_current_user
from config.firebase_config import get_db
from datetime import datetime
import base64
from pydantic import BaseModel

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

class OcrBase64Request(BaseModel):
    image_base64: str
    mime_type: Optional[str] = "image/jpeg"
    filename: Optional[str] = "nota-fiscal.jpg"


@router.post("/ocr-base64")
def process_and_save_ocr_base64(
    payload: OcrBase64Request,
    current_user: dict = Depends(get_current_user),
):
    """Recebe imagem em base64 via JSON, processa via Gemini OCR e salva os itens no Firestore."""
    try:
        uid = current_user["uid"]

        b64_clean = payload.image_base64.strip()
        if "," in b64_clean and b64_clean.startswith("data:"):
            b64_clean = b64_clean.split(",", 1)[1]

        if not b64_clean:
            raise HTTPException(status_code=400, detail="Imagem base64 vazia.")

        image_bytes = base64.b64decode(b64_clean)
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Falha ao decodificar imagem.")

        result_json = analyze_receipt_image(
            image_bytes=image_bytes,
            mime_type=payload.mime_type or "image/jpeg",
        )

        raw_items = (
            result_json.get("items", [])
            if isinstance(result_json, dict)
            else result_json
        )
        items_list = (
            [i for i in raw_items if isinstance(i, dict)]
            if isinstance(raw_items, list)
            else []
        )

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