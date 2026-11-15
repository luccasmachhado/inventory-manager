import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv

# Carrega as variáveis de ambiente (busca o .env na raiz do projeto)
load_dotenv()

# Caminho para o arquivo JSON de credenciais do Firebase Service Account
CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")

# Inicializa o Firebase Admin SDK apenas se ainda não foi inicializado
if not firebase_admin._apps:
    if os.path.exists(CREDENTIALS_PATH):
        cred = credentials.Certificate(CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
    else:
        # Modo de desenvolvimento/fallback usando credenciais padrão se configuradas no ambiente
        firebase_admin.initialize_app()

# Instância global do Firestore para ser reutilizada
db = firestore.client()

def get_db():
    """Dependency do FastAPI para injetar o cliente do Firestore nas rotas."""
    return db