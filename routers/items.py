from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from config.firebase_config import get_db
from services.auth_service import get_current_user
from services.telegram_service import check_and_notify_single_item

router = APIRouter()


class ItemCreateSchema(BaseModel):
    name: str
    quantity: str
    unit: str
    category: str
    expiration_date: str


class ItemUpdateSchema(BaseModel):
    name: Optional[str] = None
    quantity: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    expiration_date: Optional[str] = None


@router.post("/")
def add_item(
    item: ItemCreateSchema,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Salva um novo alimento no Firestore associando automaticamente ao usuário logado."""
    try:
        uid = current_user["uid"]
        db = get_db()

        doc_ref = db.collection("items").document()
        item_data = item.model_dump()

        item_data["id"] = doc_ref.id
        item_data["user_id"] = uid
        item_data["notified_48h"] = False

        doc_ref.set(item_data)
        background_tasks.add_task(check_and_notify_single_item, doc_ref.id, item_data)

        return {"status": "success", "data": item_data}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao salvar no Firestore: {str(e)}"
        )


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
        raise HTTPException(
            status_code=500, detail=f"Erro ao buscar no Firestore: {str(e)}"
        )


@router.put("/{item_id}")
def update_item(
    item_id: str,
    item: ItemUpdateSchema,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Atualiza um alimento existente pertencente ao usuário autenticado."""
    try:
        uid = current_user["uid"]
        db = get_db()

        doc_ref = db.collection("items").document(item_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Item não encontrado.")

        existing_data = doc.to_dict()

        if existing_data.get("user_id") != uid:
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para alterar este item.",
            )

        update_data = item.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="Nenhum campo válido foi enviado para atualização.",
            )

        if "expiration_date" in update_data:
            update_data["notified_48h"] = False

        doc_ref.update(update_data)
        updated_doc = doc_ref.get().to_dict()

        if "expiration_date" in update_data and updated_doc:
            background_tasks.add_task(check_and_notify_single_item, item_id, updated_doc)

        return {"status": "success", "data": updated_doc}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao atualizar no Firestore: {str(e)}"
        )


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

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Item não encontrado.")

        existing_data = doc.to_dict()

        if existing_data.get("user_id") != uid:
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para excluir este item.",
            )

        doc_ref.delete()

        return {
            "status": "success",
            "message": "Item removido com sucesso.",
            "id": item_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao excluir no Firestore: {str(e)}"
        )