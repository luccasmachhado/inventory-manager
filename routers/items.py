from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from config.firebase_config import get_db
from services.auth_service import get_current_user

router = APIRouter()

# Schema para criação (o usuário não precisa (e não deve) enviar o user_id)
class ItemCreateSchema(BaseModel):
    name: str
    quantity: str
    unit: str
    category: str
    expiration_date: str  

@router.post("/")
def add_item(item: ItemCreateSchema, current_user: dict = Depends(get_current_user)):
    """Salva um novo alimento no Firestore associando automaticamente ao usuário logado."""
    try:
        uid = current_user["uid"]
        db = get_db()
        
        doc_ref = db.collection("items").document()
        item_data = item.model_dump()
        
        # Preenche automaticamente o ID do documento e o ID do usuário autenticado
        item_data["id"] = doc_ref.id
        item_data["user_id"] = uid 
        
        doc_ref.set(item_data)
        
        return {"status": "success", "data": item_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar no Firestore: {str(e)}")

@router.get("/my-items")
def get_my_items(current_user: dict = Depends(get_current_user)):
    """Busca apenas os alimentos cadastrados pelo usuário autenticado (via token JWT)."""
    try:
        uid = current_user["uid"]
        db = get_db()
        
        items_ref = db.collection("items").where("user_id", "==", uid).stream()
        
        items = [doc.to_dict() for doc in items_ref]
        return {"status": "success", "items": items}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar no Firestore: {str(e)}")