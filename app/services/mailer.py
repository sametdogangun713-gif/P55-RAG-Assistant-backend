"""E-posta gonderimi: kayitta dogrulama kodu, "Sifremi unuttum"da sifirlama kodu (Hafta 14).
Standart kutuphane smtplib kullanilir; ek paket yok.

SMTP ayari (.env) yoksa:
  - gelistirmede (APP_ENV=development) kod sunucunun konsol penceresine yazilir: yalnizca sunucuyu
    calistiran kisi gorur, tarayiciya/HTTP yanitina asla girmez;
  - uretimde (APP_ENV=production) kod hicbir yere yazilmaz; kayit ve sifirlama kapali sayilir (can_deliver False).
"""
import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core import config

log = logging.getLogger("p55.mailer")


def smtp_configured() -> bool:
    return bool(config.SMTP_HOST and config.SMTP_USER and config.SMTP_PASSWORD)


def can_deliver() -> bool:
    """Kod (dogrulama ya da sifirlama) kullaniciya ulastirilabilir mi?"""
    return smtp_configured() or config.APP_ENV != "production"


def _message(to: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.SMTP_FROM or config.SMTP_USER
    msg["To"] = to
    msg.set_content(body)
    return msg


def build_reset_message(to: str, code: str) -> EmailMessage:
    return _message(to, "P55 parola sıfırlama kodu", (
        f"Merhaba,\n\nP55 Belge Soru-Cevap Asistanı için parola sıfırlama kodun: {code}\n\n"
        f"Kod {config.RESET_CODE_MINUTES} dakika geçerlidir. Bu isteği sen yapmadıysan bu e-postayı yok say; "
        "parolan değişmez.\n"
    ))


def build_verification_message(to: str, code: str) -> EmailMessage:
    return _message(to, "P55 e-posta doğrulama kodu", (
        f"Merhaba,\n\nP55 Belge Soru-Cevap Asistanı'na kaydını tamamlamak için doğrulama kodun: {code}\n\n"
        f"Kod {config.VERIFY_CODE_MINUTES} dakika geçerlidir. Bu kaydı sen yapmadıysan bu e-postayı yok say; "
        "kod girilmeden hesap kullanılamaz.\n"
    ))


def _send(msg: EmailMessage, label: str, to: str, code: str) -> None:
    """Arka planda (ya da Vercel'de yanittan once) calisir. Hata olursa yalnizca loglanir:
    kullaniciya hata donmek 'bu e-posta kayitli' bilgisini sizdirirdi."""
    if not smtp_configured():
        if config.APP_ENV != "production":
            # ASCII: Windows konsolunun kod sayfasi Turkce harfleri bozabiliyor (olcum: "s?f?rlama" goruldu)
            print(f"[P55] {label} (gelistirme modu, SMTP ayari yok): {to} -> {code}", flush=True)
        return
    try:
        if config.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=20, context=ssl.create_default_context()) as s:
                s.login(config.SMTP_USER, config.SMTP_PASSWORD)
                s.send_message(msg)
        else:
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as s:
                s.starttls(context=ssl.create_default_context())     # parola sifreli baglantidan gitsin
                s.login(config.SMTP_USER, config.SMTP_PASSWORD)
                s.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        log.error("%s e-postası gönderilemedi (%s): %s", label, type(e).__name__, e)


def send_reset_code(to: str, code: str) -> None:
    _send(build_reset_message(to, code), "Parola sifirlama kodu", to, code)


def send_verification_code(to: str, code: str) -> None:
    _send(build_verification_message(to, code), "E-posta dogrulama kodu", to, code)
