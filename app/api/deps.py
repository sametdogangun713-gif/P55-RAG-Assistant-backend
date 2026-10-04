"""Ortak bagimliliklar: veritabani baglantisi, mevcut kullanici, yonetici yetkisi, e-posta gonderimi."""
from typing import Optional

from fastapi import BackgroundTasks, Depends, Header, HTTPException

from app.core import config, security
from app.db import database, users
from app.services import api_tokens
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

    Iki tur anahtar kabul edilir: giriste verilen JWT (tarayici) ve "p55_" ile baslayan kisisel API anahtari
    (3. parti uygulama). Hangisiyle gelindigi user["auth_method"]'a yazilir (require_session kullanir).
    Rolu token'dan degil veritabanindan aldigimiz icin rol degisikligi hemen gecerli olur.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Kimlik doğrulaması gerekli",
                            headers={"WWW-Authenticate": "Bearer"})
    token = authorization[7:].strip()
    if api_tokens.looks_like_api_token(token):
        user = api_tokens.authenticate(conn, token)
        if user is None:
            raise HTTPException(status_code=401, detail="API anahtarı geçersiz, silinmiş ya da süresi dolmuş",
                                headers={"WWW-Authenticate": "Bearer"})
        return {**user, "auth_method": "api_token"}
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
    return {**user, "auth_method": "session"}


def require_session(user: dict = Depends(get_current_user)) -> dict:
    """Hesabi yoneten islemler (parola, hesap silme, API anahtari uretme/silme) yalnizca giris oturumuyla yapilir.

    Sizan bir API anahtariyla yeni anahtar uretilip erisim kalici hale getirilmesin ya da hesap ele gecirilmesin.
    """
    if user.get("auth_method") == "api_token":
        raise HTTPException(status_code=403, detail="Bu işlem API anahtarıyla yapılamaz. Arayüzden giriş yaparak dene")
    return user


def require_admin(user: dict = Depends(require_session)) -> dict:
    """Sunucu tarafinda rol kontrolu (yalnizca arayuzde gizlemek YETMEZ).

    Yonetim islemleri (kullanici silme vb.) API anahtariyla yapilamaz: sizan bir yonetici anahtari daha az zarar versin.
    """
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Bu işlem için yönetici yetkisi gerekli")
    return user


def deliver_email(background: BackgroundTasks, send, *args) -> None:
    """E-postayi gonderir. Normalde arka planda (yanit beklemez). Vercel'de (SEND_EMAIL_INLINE) islev yanittan
    sonra durdurulabildigi icin yanittan ONCE gonderilir; bedeli yanitin biraz gecikmesi (docs'ta yazili)."""
    if config.SEND_EMAIL_INLINE:
        send(*args)
    else:
        background.add_task(send, *args)


def get_llm():
    """Her istek icin .env'deki LLM_PROVIDER'a gore bir istemci (Claude ya da Groq).

    Testlerde sahte bir istemciyle degistirilebilir. Saglayici adi yanlissa 500 yerine anlasilir bir 503 doner.
    """
    try:
        return get_llm_client()
    except LLMConfigError as e:
        raise HTTPException(status_code=503, detail=str(e))
