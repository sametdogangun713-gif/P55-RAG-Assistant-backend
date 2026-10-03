from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_db, get_llm, require_admin
from app.api.errors import llm_http_error
from app.db import documents as documents_repo
from app.db import users
from app.services import admin as admin_service
from app.services import auth as auth_service
from app.services import documents as documents_service
from app.services.llm_client import LLMError

router = APIRouter(prefix="/admin", tags=["admin"])


class LLMTestRequest(BaseModel):
    prompt: str = "Merhaba! Tek cümleyle kendini tanıt."


@router.get("/users")
def list_all_users(admin: dict = Depends(require_admin), conn=Depends(get_db)):
    """Yalnizca yonetici: tum kullanicilar (parola hash'i donmez)."""
    return [auth_service.public_user(u) for u in users.list_users(conn)]


@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin: dict = Depends(require_admin), conn=Depends(get_db)):
    """Yalnizca yonetici: kullaniciyi ve tum verisini (dosyalar dahil) siler. Kendi hesabini silemez."""
    try:
        admin_service.delete_user_and_files(conn, admin, user_id)
    except admin_service.UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"deleted": True}


@router.get("/documents")
def list_all_documents(admin: dict = Depends(require_admin), conn=Depends(get_db)):
    """Yalnizca yonetici: tum belgeler (sahibiyle)."""
    return [documents_service.public_document(d) for d in documents_repo.list_documents(conn)]


@router.post("/llm-test")
def llm_test(body: LLMTestRequest, admin: dict = Depends(require_admin), llm=Depends(get_llm)):
    """Yalnizca yonetici: secili LLM saglayicisinin (Claude/Groq) baglantisini dener (hafta 9 demosu)."""
    prompt = body.prompt.strip()[:1000]
    try:
        answer = llm.complete("Kısa ve Türkçe yanıt ver.", [{"role": "user", "content": prompt}], max_tokens=200)
    except LLMError as e:
        raise llm_http_error(e)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"model": llm.model, "answer": answer}
