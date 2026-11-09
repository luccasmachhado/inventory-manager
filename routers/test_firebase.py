from fastapi import APIRouter, Depends, HTTPException
from config.firebase_config import get_db

router = APIRouter(prefix="/test", tags=["Teste Firebase"])

@router.get("/firestore")
def testar_firestore(db = Depends(get_db)):
    try:
        # Tenta criar um documento de teste na coleção "health_check"
        doc_ref = db.collection("health_check").document("conexao")
        doc_ref.set({
            "status": "online",
            "mensagem": "Firebase conectado com sucesso via FastAPI!"
        })

        # Tenta ler o documento que acabou de ser criado
        doc = doc_ref.get()
        if doc.exists:
            return {
                "sucesso": True,
                "dados": doc.to_dict()
            }
        else:
            raise HTTPException(status_code=500, detail="Documento não foi encontrado após a gravação.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar com o Firebase: {str(e)}")