from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from services.scraper_service import scrape_nfce_items
from services.gemini_service import analyze_receipt_image
from services.auth_service import get_current_user
from services.telegram_service import check_and_notify_single_item
from config.firebase_config import get_db
import base64

router = APIRouter()


class QRCodeRequest(BaseModel):
    url: str


@router.post("/scrape-qrcode")
def process_and_save_qrcode(
    payload: QRCodeRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Processa o QR Code da NFC-e via Scraper e salva os itens automaticamente para o usuário logado."""
    try:
        uid = current_user["uid"]

        data = scrape_nfce_items(payload.url)
        items_list = data.get("items", [])

        db = get_db()
        saved_items = []

        for item in items_list:
            doc_ref = db.collection("items").document()
            exp_date = str(item.get("expiration_date") or "").strip()

            item_data = {
                "id": doc_ref.id,
                "name": item.get("name", "Produto Desconhecido"),
                "quantity": str(item.get("quantity", "1")),
                "unit": item.get("unit", "UN"),
                "category": str(item.get("category") or ""),
                "expiration_date": exp_date,
                "notified_48h": False,
                "user_id": uid,
            }

            doc_ref.set(item_data)
            saved_items.append(item_data)

            if exp_date:
                background_tasks.add_task(
                    check_and_notify_single_item, doc_ref.id, item_data
                )

        return {
            "status": "success",
            "source": "scraper",
            "store": data.get("store", "Desconhecido"),
            "saved_count": len(saved_items),
            "items": saved_items,
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
    background_tasks: BackgroundTasks,
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
            exp_date = str(item.get("expiration_date") or "").strip()

            item_data = {
                "id": doc_ref.id,
                "name": str(item.get("name") or "Produto Desconhecido").strip(),
                "quantity": str(item.get("quantity") or "1"),
                "unit": str(item.get("unit") or "UN"),
                "category": str(item.get("category") or ""),
                "expiration_date": exp_date,
                "notified_48h": False,
                "user_id": uid,
            }

            doc_ref.set(item_data)
            saved_items.append(item_data)

            if exp_date:
                background_tasks.add_task(
                    check_and_notify_single_item, doc_ref.id, item_data
                )

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
        msg = str(e)
        if "503" in msg or "UNAVAILABLE" in msg.upper():
            raise HTTPException(
                status_code=503,
                detail="O serviço de IA está com alta demanda no momento. Tente novamente em instantes.",
            )
        raise HTTPException(status_code=500, detail=msg)