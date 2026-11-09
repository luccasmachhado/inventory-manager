from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from config.firebase_config import get_db

router = APIRouter()

class ItemSchema(BaseModel):
    name: str
    quantity: str
    unit: str
    category: str
    expiration_date: str  # Formato DD/MM/AAAA
    user_id: str

@router.post("/")
def add_item(item: ItemSchema):
    """Salva um novo alimento no Firestore na coleção 'items'."""
    try:
        db = get_db()
        doc_ref = db.collection("items").document()
        item_data = item.model_dump()
        item_data["id"] = doc_ref.id
        doc_ref.set(item_data)
        
        return {"status": "success", "data": item_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar no Firestore: {str(e)}")

@router.get("/user/{user_id}")
def get_user_items(user_id: str):
    """Busca todos os alimentos cadastrados por um usuário específico."""
    try:
        db = get_db()
        items_ref = db.collection("items").where("user_id", "==", user_id).stream()
        
        items = [doc.to_dict() for doc in items_ref]
        return {"status": "success", "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar no Firestore: {str(e)}")