import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_receipt_image(image_bytes: bytes):
    prompt = (
        "Analise esta imagem de nota fiscal de supermercado. "
        "Retorne estritamente um array JSON válido contendo objetos com as chaves: "
        "'name' (nome do produto) e 'quantity' (quantidade estimada ou numérica). "
        "Não inclua marcações markdown extras como ```json, apenas o texto JSON bruto."
    )
    
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=[
            prompt,
            types.Part.from_bytes(
                data=image_bytes,
                mime_type='image/jpeg',
            ),
        ],
    )
    
    # Limpa eventuais marcações markdown e converte para objeto Python
    clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        return {"raw_text": response.text}

def generate_recipe_from_ingredients(ingredients: list[str]):
    ingredients_str = ", ".join(ingredients)
    prompt = (
        f"Com base estritamente nos seguintes ingredientes disponíveis na minha despensa: {ingredients_str}, "
        "crie uma receita prática, gostosa e detalhada (título, tempo de preparo, ingredientes utilizados e passo a passo). "
        "Caso faltem temperos básicos (como sal, óleo ou água), você pode assumir que eles estão disponíveis."
    )
    
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt,
    )
    return response.text