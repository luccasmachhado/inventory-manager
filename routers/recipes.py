from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from services.gemini_service import generate_recipe_from_ingredients
from services.auth_service import get_current_user
from config.firebase_config import get_db
from datetime import datetime

router = APIRouter()

class RecipeRequest(BaseModel):
    ingredients: List[str]

@router.post("/generate")
def create_recipe(
    payload: RecipeRequest, 
    current_user: dict = Depends(get_current_user)
):
    """Gera receita utilizando os ingredientes e salva no Firestore para o usuário logado."""
    if not payload.ingredients:
        raise HTTPException(status_code=400, detail="A lista de ingredientes não pode estar vazia.")
    
    try:
        uid = current_user["uid"]
        
        # 1. Gera a receita via serviço do Gemini
        recipe_text = generate_recipe_from_ingredients(payload.ingredients)
        
        # 2. Salva a receita no Firestore associada ao usuário
        db = get_db()
        doc_ref = db.collection("recipes").document()
        
        recipe_data = {
            "id": doc_ref.id,
            "user_id": uid,
            "ingredients": payload.ingredients,
            "recipe": recipe_text,
            "created_at": datetime.utcnow().isoformat()
        }
        
        doc_ref.set(recipe_data)
        
        return {
            "status": "success",
            "data": recipe_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-recipes")
def get_my_recipes(current_user: dict = Depends(get_current_user)):
    """Busca as receitas geradas e salvas pelo usuário autenticado."""
    try:
        uid = current_user["uid"]
        db = get_db()

        recipes_ref = db.collection("recipes").where("user_id", "==", uid).stream()
        recipes = [doc.to_dict() for doc in recipes_ref]

        # Ordena pelas mais recentes se existir created_at
        recipes.sort(key=lambda r: r.get("created_at", ""), reverse=True)

        return {"status": "success", "recipes": recipes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar receitas: {str(e)}")