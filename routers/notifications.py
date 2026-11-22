from fastapi import APIRouter, Depends, HTTPException
from config.firebase_config import get_db
from services.auth_service import get_current_user
from services.telegram_service import (
    check_and_notify_expiring_items,
    send_telegram_message,
)

router = APIRouter()


@router.post("/check-expirations")
async def trigger_expiration_check():
    """Dispara manualmente a varredura de produtos que vencem em até 48h."""
    result = await check_and_notify_expiring_items()
    return {"status": "success", "details": result}


@router.post("/test-message")
async def send_test_notification(current_user: dict = Depends(get_current_user)):
    """Envia uma mensagem de teste para o Telegram do usuário autenticado."""
    uid = current_user["uid"]
    db = get_db()
    user_doc = db.collection("users").document(uid).get()
    user_data = user_doc.to_dict() if user_doc.exists else None

    if not user_data or not user_data.get("telegram_chat_id"):
        raise HTTPException(
            status_code=400,
            detail=(
                "Nenhum telegram_chat_id vinculado a este usuário. "
                "Use PATCH /api/auth/telegram primeiro."
            ),
        )

    chat_id = user_data["telegram_chat_id"]
    sent = await send_telegram_message(
        chat_id,
        "✅ *Conexão confirmada!* Você receberá alertas aqui quando seus alimentos estiverem a 48h de vencer.",
    )

    if not sent:
        raise HTTPException(
            status_code=500,
            detail="Falha ao enviar mensagem pelo bot do Telegram.",
        )

    return {"status": "success", "message": "Mensagem de teste enviada ao Telegram!"}