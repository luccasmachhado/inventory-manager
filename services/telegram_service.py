import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import httpx
from dotenv import load_dotenv
from config.firebase_config import get_db

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _escapar_markdown(texto: str) -> str:
    """Escapa caracteres que podem quebrar o parse_mode='Markdown' no Telegram."""
    if not texto:
        return ""
    return str(texto).replace("_", "\\_").replace("*", "\\*").replace("`", "'")


async def send_telegram_message(chat_id: str, text: str) -> bool:
    """Envia uma mensagem de texto via API oficial do Telegram."""
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH, override=True)

    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token or not chat_id:
        print(
            f"DEBUG TELEGRAM -> Caminho .env: {ENV_PATH} | "
            f"Existe? {ENV_PATH.exists()} | Token: {bool(token)} | ChatID: {bool(chat_id)}"
        )
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": str(chat_id).strip(),
        "text": text,
        "parse_mode": "Markdown",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            print(f"ERRO TELEGRAM ({response.status_code}): {response.text}")
        return response.status_code == 200


async def check_and_notify_expiring_items() -> dict:
    """Varre os itens no Firestore e notifica produtos que vencem em até 48 horas (2 dias)."""
    db = get_db()
    today = datetime.now(ZoneInfo("America/Fortaleza")).date()
    items_ref = db.collection("items").stream()

    notified_count = 0
    checked_count = 0
    users_cache = {}

    for doc in items_ref:
        checked_count += 1
        item = doc.to_dict()

        if not item:
            continue

        if item.get("notified_48h") is True:
            continue

        exp_str = item.get("expiration_date")
        user_id = item.get("user_id")

        if not exp_str or not user_id:
            continue

        try:
            exp_date = datetime.strptime(exp_str.strip(), "%d/%m/%Y").date()
        except ValueError:
            continue

        days_left = (exp_date - today).days

        if 0 <= days_left <= 2:
            if user_id not in users_cache:
                user_doc = db.collection("users").document(user_id).get()
                users_cache[user_id] = user_doc.to_dict() if user_doc.exists else None

            user_data = users_cache[user_id]
            chat_id = user_data.get("telegram_chat_id") if user_data else None

            if not chat_id:
                continue

            prazo_texto = (
                "HOJE!" if days_left == 0
                else "AMANHÃ (24h)!" if days_left == 1
                else "em 48 horas!"
            )

            nome_seguro = _escapar_markdown(item.get("name", "Produto"))
            categoria_segura = _escapar_markdown(item.get("category") or "Geral")

            mensagem = (
                f"⚠️ *Alerta de Validade — Despensa Inteligente*\n\n"
                f"O produto *{nome_seguro}* ({item.get('quantity')} {item.get('unit')}) "
                f"vence *{prazo_texto}*\n"
                f"📅 Validade: `{exp_str}`\n"
                f"📂 Categoria: {categoria_segura}"
            )

            sent = await send_telegram_message(chat_id, mensagem)
            if sent:
                db.collection("items").document(doc.id).update({"notified_48h": True})
                notified_count += 1

    return {
        "checked_items": checked_count,
        "notifications_sent": notified_count,
    }


async def check_and_notify_single_item(item_id: str, item: dict) -> bool:
    """Verifica se um item recém-criado ou editado vence em até 48h e notifica imediatamente."""
    if not item or item.get("notified_48h") is True:
        return False

    exp_str = item.get("expiration_date")
    user_id = item.get("user_id")
    if not exp_str or not user_id:
        return False

    try:
        exp_date = datetime.strptime(exp_str.strip(), "%d/%m/%Y").date()
    except ValueError:
        return False

    today = datetime.now(ZoneInfo("America/Fortaleza")).date()
    days_left = (exp_date - today).days

    if not (0 <= days_left <= 2):
        return False

    db = get_db()
    user_doc = db.collection("users").document(user_id).get()
    user_data = user_doc.to_dict() if user_doc.exists else None
    chat_id = user_data.get("telegram_chat_id") if user_data else None

    if not chat_id:
        return False

    prazo_texto = (
        "HOJE!" if days_left == 0
        else "AMANHÃ (24h)!" if days_left == 1
        else "em 48 horas!"
    )

    nome_seguro = _escapar_markdown(item.get("name", "Produto"))
    categoria_segura = _escapar_markdown(item.get("category") or "Geral")

    mensagem = (
        f"⚠️ *Alerta de Validade — Despensa Inteligente*\n\n"
        f"O produto *{nome_seguro}* ({item.get('quantity')} {item.get('unit')}) "
        f"vence *{prazo_texto}*\n"
        f"📅 Validade: `{exp_str}`\n"
        f"📂 Categoria: {categoria_segura}"
    )

    sent = await send_telegram_message(chat_id, mensagem)
    if sent and item_id:
        db.collection("items").document(item_id).update({"notified_48h": True})
    return sent