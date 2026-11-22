from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config.firebase_config import init_firebase
from routers import auth, notifications, receipts, recipes, test_firebase, items
from services.telegram_service import check_and_notify_expiring_items

TIMEZONE_LOCAL = ZoneInfo("America/Fortaleza")
scheduler = AsyncIOScheduler(timezone=TIMEZONE_LOCAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa o Firebase Admin SDK na subida da API
    init_firebase()

    # Varredura completa de todo o estoque todos os dias às 00:00 (America/Fortaleza)
    if not scheduler.running:
        scheduler.add_job(
            check_and_notify_expiring_items,
            trigger=CronTrigger(hour=0, minute=0, timezone=TIMEZONE_LOCAL),
            id="daily_midnight_expiration_check",
            replace_existing=True,
        )
        scheduler.start()

    yield

    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(
    title="Despensa Inteligente API",
    description="Backend para gerenciamento de estoque doméstico, leitura de notas fiscais e geração de receitas com IA.",
    version="1.0.0",
    lifespan=lifespan,
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