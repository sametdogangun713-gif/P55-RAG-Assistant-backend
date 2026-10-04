from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db, require_session
from app.core import config
from app.services import auth as auth_service
from app.services import account, api_tokens, email_codes, email_verification, mailer, password_reset

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str


class EmailRequest(BaseModel):
    email: str


ForgotRequest = EmailRequest


class VerifyRequest(BaseModel):
    email: str
    code: str


class ProfileUpdate(BaseModel):
    full_name: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class AccountDelete(BaseModel):
    password: str


class TokenCreate(BaseModel):
    name: str
    expires_in_days: Optional[int] = None      # None -> varsayilan (90 gun)


class ResetRequest(BaseModel):
    email: str
    code: str
    new_password: str


MAIL_NOT_CONFIGURED = "E-posta gönderimi ayarlanmamış (SMTP). Yöneticine başvur"


def _deliver(background: BackgroundTasks, send, to: str, code: str) -> None:
    """E-postayi gonderir. Normalde arka planda (yanit beklemez). Vercel'de (SEND_EMAIL_INLINE) islev yanittan
    sonra durdurulabildigi icin yanittan ONCE gonderilir; bedeli yanitin biraz gecikmesi (docs'ta yazili)."""
    if config.SEND_EMAIL_INLINE:
        send(to, code)
    else:
        background.add_task(send, to, code)


def _token_response(user: dict) -> dict:
    return {"access_token": auth_service.issue_token(user), "token_type": "bearer",
            "user": auth_service.public_user(user)}


@router.post("/register", status_code=201)
def register(body: RegisterRequest, background: BackgroundTasks, conn=Depends(get_db)):
    """Kayit: ad soyad + e-posta + parola. Dogrulama aciksa hesap dogrulanmamis acilir ve e-postaya kod gider."""
    if config.REQUIRE_EMAIL_VERIFICATION and not mailer.can_deliver():
        raise HTTPException(status_code=503, detail=MAIL_NOT_CONFIGURED)    # kod ulasmayacaksa hesap acma
    try:
        user = auth_service.sign_up(conn, body.full_name, body.email, body.password)
    except auth_service.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except auth_service.DuplicateUserError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if user["email_verified_at"]:
        return {**auth_service.public_user(user), "verification_required": False,
                "detail": "Kayıt tamamlandı, şimdi giriş yapabilirsin."}
    code = email_verification.issue_code(conn, user)
    if code:                                          # None: az once kod gitti, yenisi uretilmedi
        _deliver(background, mailer.send_verification_code, user["email"], code)
    return {**auth_service.public_user(user), "verification_required": True,
            "detail": f"{user['email']} adresine 6 haneli doğrulama kodu gönderildi. "
                      f"Kod {config.VERIFY_CODE_MINUTES} dakika geçerli."}


@router.post("/verify-email")
def verify_email(body: VerifyRequest, conn=Depends(get_db)):
    """Kod dogruysa e-posta dogrulanir ve kullanici dogrudan giris yapmis olur (token doner)."""
    try:
        user = email_verification.verify(conn, body.email, body.code)
    except email_codes.InvalidCodeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _token_response(user)


@router.post("/resend-verification")
def resend_verification(body: EmailRequest, background: BackgroundTasks, conn=Depends(get_db)):
    """Kayitli ve dogrulanmamis e-postaya yeni kod. Yanit her durumda ayni (kayitli olup olmadigi sizmasin)."""
    if not mailer.can_deliver():
        raise HTTPException(status_code=503, detail=MAIL_NOT_CONFIGURED)
    result = email_verification.request_code(conn, body.email)
    if result:
        _deliver(background, mailer.send_verification_code, *result)
    return {"detail": "Bu e-posta kayıtlı ve doğrulanmamışsa yeni kod gönderildi. Gelen kutunu "
                      "(ve gereksiz klasörünü) kontrol et."}


@router.post("/login")
def login(body: Credentials, conn=Depends(get_db)):
    try:
        result = auth_service.login(conn, body.email, body.password)
    except auth_service.AccountLockedError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except auth_service.InvalidCredentialsError as e:
        raise HTTPException(status_code=401, detail=str(e), headers={"WWW-Authenticate": "Bearer"})
    except auth_service.EmailNotVerifiedError as e:
        raise HTTPException(status_code=403, detail=str(e))   # arayuz 403'te "kodu gir" paneline gecer
    return {"access_token": result["access_token"], "token_type": "bearer",
            "user": auth_service.public_user(result["user"])}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return auth_service.public_user(user)


# --- Hesabim: kullanicinin kendi hesabi ---
@router.patch("/me")
def update_me(body: ProfileUpdate, user: dict = Depends(require_session), conn=Depends(get_db)):
    try:
        return auth_service.public_user(account.update_name(conn, user, body.full_name))
    except auth_service.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/change-password")
def change_password(body: PasswordChange, user: dict = Depends(require_session), conn=Depends(get_db)):
    try:
        account.change_password(conn, user, body.current_password, body.new_password)
    except account.WrongPasswordError as e:
        raise HTTPException(status_code=400, detail=str(e))     # 401 degil: oturum gecerli, yalnizca parola yanlis
    except auth_service.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"detail": "Parolan değiştirildi."}


@router.delete("/me")
def delete_me(body: AccountDelete, user: dict = Depends(require_session), conn=Depends(get_db)):
    try:
        account.delete_account(conn, user, body.password)
    except account.WrongPasswordError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except account.LastAdminError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"detail": "Hesabın ve tüm verilerin silindi."}


# --- Kisisel API anahtarlari: 3. parti uygulamalar "Authorization: Bearer p55_..." ile baglanir ---
@router.get("/tokens")
def list_tokens(user: dict = Depends(require_session), conn=Depends(get_db)):
    """Anahtarlarin adi, ilk 12 karakteri ve tarihleri. Anahtarin kendisi bir daha gosterilmez."""
    return api_tokens.list_tokens(conn, user)


@router.post("/tokens", status_code=201)
def create_token(body: TokenCreate, user: dict = Depends(require_session), conn=Depends(get_db)):
    """Yanittaki "token" alani anahtarin TEK gosterimidir: kullanici hemen kopyalamali."""
    try:
        return api_tokens.create_token(conn, user, body.name, body.expires_in_days)
    except api_tokens.TokenValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except api_tokens.TokenLimitError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/tokens/{token_id}")
def delete_token(token_id: int, user: dict = Depends(require_session), conn=Depends(get_db)):
    """Anahtari iptal eder: o anahtarla gelen sonraki istek 401 alir. Baskasinin anahtari 404 (var oldugu sizmaz)."""
    if not api_tokens.revoke_token(conn, user, token_id):
        raise HTTPException(status_code=404, detail="API anahtarı bulunamadı")
    return {"detail": "API anahtarı silindi. Bu anahtarı kullanan uygulamalar artık bağlanamaz."}


# --- Hafta 14: parola sifirlama ---
RESET_SENT_MESSAGE = "Bu e-posta kayıtlıysa sıfırlama kodu gönderildi. Gelen kutunu (ve gereksiz klasörünü) kontrol et."


@router.post("/forgot-password")
def forgot_password(body: ForgotRequest, background: BackgroundTasks, conn=Depends(get_db)):
    """Kayitli olsun olmasin AYNI yaniti doner. E-posta arka planda gider: kayitli e-postada yanit
    gecikseydi, sure farkindan hesabin varligi anlasilirdi (Vercel istisnasi: _deliver)."""
    if not mailer.can_deliver():
        raise HTTPException(status_code=503, detail=MAIL_NOT_CONFIGURED)
    result = password_reset.request_reset(conn, body.email)
    if result:
        _deliver(background, mailer.send_reset_code, *result)
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
