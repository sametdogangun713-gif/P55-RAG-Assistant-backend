"""Ortak bagimliliklar: veritabani baglantisi, mevcut kullanici, yonetici yetkisi."""
from typing import Optional

from fastapi import Depends, Header, HTTPException

from app.core import security
from app.db import database, users
from app.services.llm_client import LLMConfigError, get_llm_client


def get_db():
    """Her istek icin bir baglanti acar, istek bitince kapatir."""
    conn = database.get_connection()
    try:
        yield conn
    finally:
        conn.close()


def get_current_user(authorization: Optional[str] = Header(default=None), conn=Depends(get_db)) -> dict:
    """'Authorization: Bearer <token>' basligini dogrular, kullaniciyi VERITABANINDAN okur.

    Rolu token'dan degil veritabanindan aldigimiz icin rol degisikligi hemen gecerli olur.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Kimlik doğrulaması gerekli",
                            headers={"WWW-Authenticate": "Bearer"})
    token = authorization[7:].strip()
    try:
        payload = security.decode_access_token(token)
        user_id = int(payload["sub"])
    except (security.TokenError, ValueError):
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş oturum",
                            headers={"WWW-Authenticate": "Bearer"})
    user = users.get_user_by_id(conn, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı",
                            headers={"WWW-Authenticate": "Bearer"})
    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Sunucu tarafinda rol kontrolu (yalnizca arayuzde gizlemek YETMEZ)."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için yönetici yetkisi gerekli")
    return user


def get_llm():
    """Her istek icin .env'deki LLM_PROVIDER'a gore bir istemci (Claude ya da Groq).

    Testlerde sahte bir istemciyle degistirilebilir. Saglayici adi yanlissa 500 yerine anlasilir bir 503 doner.
    """
    try:
        return get_llm_client()
    except LLMConfigError as e:
        raise HTTPException(status_code=503, detail=str(e))
