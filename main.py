from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import receipts, recipes, test_firebase

app = FastAPI(
    title="Despensa Inteligente API",
    description="Backend para gerenciamento de estoque doméstico, leitura de notas fiscais e geração de receitas com IA.",
    version="1.0.0"
)

# Configuração de CORS para permitir requisições do App React Native / Expo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restringe para domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro das rotas
app.include_router(receipts.router, prefix="/api/receipts", tags=["Notas Fiscais"])
app.include_router(recipes.router, prefix="/api/recipes", tags=["Receitas"])
app.include_router(test_firebase.router)

@app.get("/", tags=["Health Check"])
def health_check():
    return {"status": "online", "message": "API da Despensa Inteligente rodando com sucesso!"}