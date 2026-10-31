from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.gemini_service import generate_recipe_from_ingredients

router = APIRouter()

class RecipeRequest(BaseModel):
    ingredients: List[str]

@router.post("/generate")
def create_recipe(payload: RecipeRequest):
    """Gera receita utilizando os ingredientes em alerta vermelho."""
    if not payload.ingredients:
        raise HTTPException(status_code=400, detail="A lista de ingredientes não pode estar vazia.")
    
    try:
        recipe_text = generate_recipe_from_ingredients(payload.ingredients)
        return {"recipe": recipe_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))