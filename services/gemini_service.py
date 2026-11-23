import os
import json
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELO_PRINCIPAL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
MODELO_FALLBACK = os.getenv("GEMINI_FALLBACK_MODEL", "").strip()


def _is_erro_503(exc: Exception) -> bool:
    msg = str(exc)
    return "503" in msg or "UNAVAILABLE" in msg.upper()


def _gerar_com_retry(
    modelo: str,
    contents,
    max_tentativas: int = 4,
    espera_inicial: float = 1.5,
):
    ultimo_erro = None
    for tentativa in range(max_tentativas):
        try:
            return client.models.generate_content(
                model=modelo,
                contents=contents,
            )
        except Exception as e:
            ultimo_erro = e
            if not _is_erro_503(e) or tentativa == max_tentativas - 1:
                raise
            time.sleep(espera_inicial * (2 ** tentativa))  # 1.5s, 3.0s, 6.0s
    raise ultimo_erro


def _chamar_com_fallback(contents):
    try:
        return _gerar_com_retry(
            MODELO_PRINCIPAL,
            contents,
            max_tentativas=4,
            espera_inicial=1.5,
        )
    except Exception as e:
        if _is_erro_503(e) and MODELO_FALLBACK:
            return _gerar_com_retry(
                MODELO_FALLBACK,
                contents,
                max_tentativas=2,
                espera_inicial=1.5,
            )
        raise


def analyze_receipt_image(image_bytes: bytes, mime_type: str = "image/jpeg"):
    if not image_bytes:
        raise ValueError("A imagem enviada está vazia.")

    safe_mime = (
        mime_type
        if mime_type in ("image/jpeg", "image/png", "image/webp")
        else "image/jpeg"
    )

    prompt = (
        "Analise esta imagem de nota fiscal de supermercado. "
        "Retorne estritamente um JSON válido no formato: "
        '{"store": "nome do estabelecimento ou Desconhecido", "items": ['
        '{"name": "nome do produto", "quantity": 1, "unit": "UN", "total_value": 0.0}'
        "]}. "
        "Não inclua marcações markdown extras como ```json, apenas o texto JSON bruto."
    )

    contents = [
        prompt,
        types.Part.from_bytes(
            data=image_bytes,
            mime_type=safe_mime,
        ),
    ]

    response = _chamar_com_fallback(contents)

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


def generate_recipe_from_ingredients(ingredients: list[str]):
    ingredients_str = ", ".join(ingredients)
    prompt = (
        f"Com base estritamente nos seguintes ingredientes disponíveis na minha despensa: {ingredients_str}, "
        "crie uma receita prática, gostosa e detalhada (título, tempo de preparo, ingredientes utilizados e passo a passo). "
        "Caso faltem temperos básicos (como sal, óleo ou água), você pode assumir que eles estão disponíveis."
    )

    response = _chamar_com_fallback(prompt)
    return response.text