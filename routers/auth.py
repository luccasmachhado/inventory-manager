from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import os
from firebase_admin import auth
import httpx
from config.firebase_config import get_db
from services.auth_service import get_current_user

router = APIRouter()


class UserRegisterSchema(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    telegram_chat_id: Optional[str] = None


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class TelegramUpdateSchema(BaseModel):
    telegram_chat_id: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserRegisterSchema):
    """Cria o usuário no Firebase Auth e salva o perfil na coleção 'users' do Firestore."""
    clean_chat_id = (
        user.telegram_chat_id.strip()
        if isinstance(user.telegram_chat_id, str) and user.telegram_chat_id.strip()
        else None
    )

    user_record = None
    try:
        user_record = auth.create_user(
            email=user.email,
            password=user.password,
            display_name=user.name.strip(),
        )

        db = get_db()
        user_data = {
            "uid": user_record.uid,
            "name": user.name.strip(),
            "email": user.email.strip().lower(),
            "telegram_chat_id": clean_chat_id,
        }
        db.collection("users").document(user_record.uid).set(user_data)

        return {"status": "success", "data": user_data}

    except auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Esse e-mail já está cadastrado.")
    except HTTPException:
        raise
    except Exception as e:
        if user_record is not None:
            try:
                auth.delete_user(user_record.uid)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Erro ao cadastrar usuário: {str(e)}")


@router.post("/login")
async def login_user(credentials: UserLoginSchema):
    """Autentica e-mail/senha via Firebase Identity Toolkit e retorna o token JWT e o uid."""
    web_api_key = os.getenv("FIREBASE_WEB_API_KEY")
    if not web_api_key:
        raise HTTPException(
            status_code=500,
            detail="FIREBASE_WEB_API_KEY não configurada no ambiente.",
        )

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={web_api_key}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json={
                "email": credentials.email,
                "password": credentials.password,
                "returnSecureToken": True,
            },
        )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")

    data = response.json()
    uid = data["localId"]

    db = get_db()
    user_doc = db.collection("users").document(uid).get()
    profile = (
        user_doc.to_dict()
        if user_doc.exists
        else {"uid": uid, "email": credentials.email, "telegram_chat_id": None}
    )

    return {
        "status": "success",
        "access_token": data["idToken"],
        "refresh_token": data["refreshToken"],
        "user": profile,
    }


@router.get("/me")
def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Retorna os dados do usuário autenticado pelo token."""
    uid = current_user["uid"]
    db = get_db()
    doc = db.collection("users").document(uid).get()

    if not doc.exists:
        return {
            "status": "success",
            "user": {
                "uid": uid,
                "email": current_user.get("email"),
                "telegram_chat_id": None,
            },
        }

    return {"status": "success", "user": doc.to_dict()}


@router.patch("/telegram")
def link_telegram(
    payload: TelegramUpdateSchema,
    current_user: dict = Depends(get_current_user),
):
    """Vincula ou atualiza o chat_id do Telegram do usuário logado."""
    clean_chat_id = payload.telegram_chat_id.strip()
    if not clean_chat_id:
        raise HTTPException(status_code=400, detail="Informe um telegram_chat_id válido.")

    uid = current_user["uid"]
    db = get_db()
    db.collection("users").document(uid).set(
        {"telegram_chat_id": clean_chat_id},
        merge=True,
    )
    return {
        "status": "success",
        "message": "Telegram vinculado com sucesso!",
        "telegram_chat_id": clean_chat_id,
    }