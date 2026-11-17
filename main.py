from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from routers import auth, notifications, receipts, recipes, test_firebase, items
from services.telegram_service import check_and_notify_expiring_items

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicia a verificação automática a cada 6 horas
    scheduler.add_job(check_and_notify_expiring_items, "interval", hours=6)
    scheduler.start()
    yield
    scheduler.shutdown()

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
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticação"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notificações"])
app.include_router(receipts.router, prefix="/api/receipts", tags=["Notas Fiscais"])
app.include_router(recipes.router, prefix="/api/recipes", tags=["Receitas"])
app.include_router(items.router, prefix="/api/items", tags=["Itens"])
app.include_router(test_firebase.router)

@app.get("/", tags=["Health Check"])
def health_check():
    return {"status": "online", "message": "API da Despensa Inteligente rodando com sucesso!"}