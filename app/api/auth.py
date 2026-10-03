from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db
from app.core import config
from app.services import auth as auth_service
from app.services import mailer, password_reset

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: str
    password: str


class ForgotRequest(BaseModel):
    email: str


class ResetRequest(BaseModel):
    email: str
    code: str
    new_password: str


@router.post("/register", status_code=201)
def register(body: Credentials, conn=Depends(get_db)):
    try:
        user = auth_service.register_user(conn, body.email, body.password)
    except auth_service.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except auth_service.DuplicateUserError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return auth_service.public_user(user)


@router.post("/login")
def login(body: Credentials, conn=Depends(get_db)):
    try:
        result = auth_service.login(conn, body.email, body.password)
    except auth_service.AccountLockedError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except auth_service.InvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e), headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": result["access_token"], "token_type": "bearer",
            "user": auth_service.public_user(result["user"])}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return auth_service.public_user(user)


# --- Hafta 14: parola sifirlama ---
RESET_SENT_MESSAGE = "Bu e-posta kayıtlıysa sıfırlama kodu gönderildi. Gelen kutunu (ve gereksiz klasörünü) kontrol et."


@router.post("/forgot-password")
def forgot_password(body: ForgotRequest, background: BackgroundTasks, conn=Depends(get_db)):
    """Kayitli olsun olmasin AYNI yaniti doner. E-posta arka planda gider: kayitli e-postada yanit
    gecikseydi, sure farkindan hesabin varligi anlasilirdi.

    Istisna (SEND_EMAIL_INLINE, Vercel'de varsayilan): islev yanittan sonra durdurulabildigi icin e-posta
    yanittan ONCE gonderilir. Bedeli: kayitli e-postada yanit biraz gecikir (bilinen sinir, docs'ta yazili).
    """
    if not mailer.can_deliver():
        raise HTTPException(status_code=503, detail="Parola sıfırlama e-postası ayarlanmamış. Yöneticine başvur")
    result = password_reset.request_reset(conn, body.email)
    if result and config.SEND_EMAIL_INLINE:
        mailer.send_reset_code(*result)
    elif result:
        background.add_task(mailer.send_reset_code, *result)
    return {"detail": RESET_SENT_MESSAGE}


@router.post("/reset-password")
def reset_password(body: ResetRequest, conn=Depends(get_db)):
    try:
        password_reset.reset_password(conn, body.email, body.code, body.new_password)
    except auth_service.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except password_reset.InvalidResetCodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"detail": "Parolan değiştirildi. Yeni parolanla giriş yapabilirsin."}
