import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv

<<<<<<< HEAD
# Carrega as variáveis de ambiente (busca o .env na raiz do projeto)
=======
>>>>>>> 3c147fc8fab9eae0d101df6e5feaad3b08ca7dcf
load_dotenv()

# Caminho para o arquivo JSON de credenciais do Firebase Service Account
CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")

<<<<<<< HEAD
# Inicializa o Firebase Admin SDK apenas se ainda não foi inicializado
=======
>>>>>>> 3c147fc8fab9eae0d101df6e5feaad3b08ca7dcf
if not firebase_admin._apps:
    if os.path.exists(CREDENTIALS_PATH):
        cred = credentials.Certificate(CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
    else:
<<<<<<< HEAD
        # Modo de desenvolvimento/fallback usando credenciais padrão se configuradas no ambiente
        firebase_admin.initialize_app()

# Instância global do Firestore para ser reutilizada
db = firestore.client()

def get_db():
    """Dependency do FastAPI para injetar o cliente do Firestore nas rotas."""
=======
        # Modo de desenvolvimento/fallback usando credenciais padrão se configuradas
        firebase_admin.initialize_app()

db = firestore.client()

def get_db():
>>>>>>> 3c147fc8fab9eae0d101df6e5feaad3b08ca7dcf
    return db