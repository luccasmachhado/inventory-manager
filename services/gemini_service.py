import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Inicializa o cliente oficial da nova SDK do Gemini
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_receipt_image(image_bytes: bytes):
    """
    Opção B: Usa o Gemini 2.5/1.5 Flash via google-genai para extrair itens de uma foto de nota fiscal.
    """
    prompt = (
        "Analise esta imagem de nota fiscal de supermercado. "
        "Retorne estritamente um array JSON válido contendo objetos com as chaves: "
        "'name' (nome do produto) e 'quantity' (quantidade estimada ou numérica). "
        "Não inclua marcações markdown extras como ```json, apenas o texto JSON bruto."
    )
    
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=[
            prompt,
            types.Part.from_bytes(
                data=image_bytes,
                mime_type='image/jpeg',
            ),
        ],
    )
    return response.text

def generate_recipe_from_ingredients(ingredients: list[str]):
    """
    Gera uma receita prática baseada nos ingredientes próximos ao vencimento.
    """
    ingredients_str = ", ".join(ingredients)
    prompt = (
        f"Com base estritamente nos seguintes ingredientes disponíveis na minha despensa: {ingredients_str}, "
        "crie uma receita prática, gostosa e detalhada (título, tempo de preparo, ingredientes utilizados e passo a passo). "
        "Caso faltem temperos básicos (como sal, óleo ou água), você pode assumir que eles estão disponíveis."
    )
    
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt,
    )
    return response.text