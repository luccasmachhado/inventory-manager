import json
import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv

load_dotenv()

CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")
CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON")

_db = None


def init_firebase():
    """Inicializa o Firebase Admin SDK apenas uma vez."""
    if not firebase_admin._apps:
        if CREDENTIALS_JSON:
            cred_dict = json.loads(CREDENTIALS_JSON)
            if isinstance(cred_dict.get("private_key"), str):
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        elif os.path.exists(CREDENTIALS_PATH):
            cred = credentials.Certificate(CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
        else:
            firebase_admin.initialize_app()


def get_db():
    """Dependency do FastAPI para injetar o cliente do Firestore nas rotas."""
    global _db
    init_firebase()
    if _db is None:
        _db = firestore.client()
    return _db