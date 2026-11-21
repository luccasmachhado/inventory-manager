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


# Schema para atualização (campos opcionais permitem atualizar parcialmente ou por completo)
class ItemUpdateSchema(BaseModel):
    name: Optional[str] = None
    quantity: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    expiration_date: Optional[str] = None


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


@router.put("/{item_id}")
def update_item(
    item_id: str,
    item: ItemUpdateSchema,
    current_user: dict = Depends(get_current_user),
):
    """Atualiza um alimento existente pertencente ao usuário autenticado."""
    try:
        uid = current_user["uid"]
        db = get_db()

        doc_ref = db.collection("items").document(item_id)
        doc = doc_ref.get()

        # 1. Verifica se o documento existe
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Item não encontrado.")

        existing_data = doc.to_dict()

        # 2. Garante que o item pertence ao usuário logado
        if existing_data.get("user_id") != uid:
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para alterar este item.",
            )

        # 3. Extrai apenas os campos enviados na requisição
        update_data = item.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="Nenhum campo válido foi enviado para atualização.",
            )

        # 4. Atualiza no Firestore e retorna o registro atualizado
        doc_ref.update(update_data)
        updated_doc = doc_ref.get().to_dict()

        return {"status": "success", "data": updated_doc}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar no Firestore: {str(e)}")


@router.delete("/{item_id}")
def delete_item(
    item_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Remove um alimento existente pertencente ao usuário autenticado."""
    try:
        uid = current_user["uid"]
        db = get_db()

        doc_ref = db.collection("items").document(item_id)
        doc = doc_ref.get()

        # 1. Verifica se o documento existe
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Item não encontrado.")

        existing_data = doc.to_dict()

        # 2. Garante que o item pertence ao usuário logado
        if existing_data.get("user_id") != uid:
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para excluir este item.",
            )

        # 3. Exclui o documento no Firestore
        doc_ref.delete()

        return {"status": "success", "message": "Item removido com sucesso.", "id": item_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir no Firestore: {str(e)}")