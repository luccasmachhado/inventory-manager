import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_receipt_image(image_bytes: bytes, mime_type: str = "image/jpeg"):
    if not image_bytes:
        raise ValueError("A imagem enviada está vazia.")

    safe_mime = mime_type if mime_type in ("image/jpeg", "image/png", "image/webp") else "image/jpeg"

    prompt = (
        "Analise esta imagem de nota fiscal de supermercado. "
        "Retorne estritamente um JSON válido no formato: "
        "{\"store\": \"nome do estabelecimento ou Desconhecido\", \"items\": ["
        "{\"name\": \"nome do produto\", \"quantity\": 1, \"unit\": \"UN\", \"total_value\": 0.0}"
        "]}. "
        "Não inclua marcações markdown extras como ```json, apenas o texto JSON bruto."
    )

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=[
            prompt,
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=safe_mime,
            ),
        ],
    )

    raw = (response.text or "").strip()
    clean_text = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(clean_text)
        if isinstance(parsed, list):
            return {"store": "Desconhecido", "items": parsed}
        if isinstance(parsed, dict):
            return parsed
        return {"store": "Desconhecido", "items": []}
    except json.JSONDecodeError:
        return {"store": "Desconhecido", "items": [], "raw_text": raw}

def _gerar_com_retry(modelo: str, prompt: str, max_tentativas: int = 3, espera_inicial: float = 1.5):
    ultimo_erro = None
    for tentativa in range(max_tentativas):
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            ultimo_erro = e
            msg = str(e)
            is_503 = "503" in msg or "UNAVAILABLE" in msg.upper()
            if not is_503 or tentativa == max_tentativas - 1:
                raise
            time.sleep(espera_inicial * (2 ** tentativa))  # 1.5s, 3.0s
    raise ultimo_erro


def generate_recipe_from_ingredients(ingredients: list[str]):
    ingredients_str = ", ".join(ingredients)
    prompt = (
        f"Com base estritamente nos seguintes ingredientes disponíveis na minha despensa: {ingredients_str}, "
        "crie uma receita prática, gostosa e detalhada (título, tempo de preparo, ingredientes utilizados e passo a passo). "
        "Caso faltem temperos básicos (como sal, óleo ou água), você pode assumir que eles estão disponíveis."
    )

    try:
        return _gerar_com_retry("gemini-3.8-flash", prompt, max_tentativas=3, espera_inicial=1.5)
    except Exception as e:
        msg = str(e)
        if "503" in msg or "UNAVAILABLE" in msg.upper():
            # Fallback caso o modelo principal continue sobrecarregado
            return _gerar_com_retry("gemini-2.5-flash", prompt, max_tentativas=2, espera_inicial=1.0)
        raise