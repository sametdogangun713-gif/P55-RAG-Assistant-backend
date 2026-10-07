"""E-posta gonderimi: kayitta dogrulama kodu, "Sifremi unuttum"da sifirlama kodu (Hafta 14),
API anahtari olusturulunca / yonetici iptal edince hesap sahibine bildirim.
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

log = logging.getLogger("asistan.mailer")


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
    return _message(to, "Belge Tabanlı Soru Asistanı: parola sıfırlama kodu", (
        f"Merhaba,\n\nBelge Tabanlı Soru Asistanı için parola sıfırlama kodun: {code}\n\n"
        f"Kod {config.RESET_CODE_MINUTES} dakika geçerlidir. Bu isteği sen yapmadıysan bu e-postayı yok say; "
        "parolan değişmez.\n"
    ))


def build_verification_message(to: str, code: str) -> EmailMessage:
    return _message(to, "Belge Tabanlı Soru Asistanı: e-posta doğrulama kodu", (
        f"Merhaba,\n\nBelge Tabanlı Soru Asistanı'na kaydını tamamlamak için doğrulama kodun: {code}\n\n"
        f"Kod {config.VERIFY_CODE_MINUTES} dakika geçerlidir. Bu kaydı sen yapmadıysan bu e-postayı yok say; "
        "kod girilmeden hesap kullanılamaz.\n"
    ))


def _token_lines(token: dict) -> str:
    return (f"  Anahtar adı : {token['name']}\n"
            f"  Anahtar     : {token['prefix']}… (yalnızca ilk 12 karakter)\n"
            f"  Oluşturma   : {token['created_at']} (UTC)\n"
            f"  Bitiş       : {token['expires_at']} (UTC)\n")


def build_token_created_message(to: str, token: dict) -> EmailMessage:
    """Anahtarin KENDISI e-postaya yazilmaz (e-posta kutusu sizarsa anahtar da sizmasin): token = public_info."""
    return _message(to, "Belge Tabanlı Soru Asistanı: yeni API anahtarı oluşturuldu", (
        "Merhaba,\n\nBelge Tabanlı Soru Asistanı hesabında yeni bir API anahtarı oluşturuldu:\n\n" + _token_lines(token) +
        "\nBunu sen yaptıysan bir şey yapmana gerek yok.\n"
        "Sen yapmadıysan: hemen giriş yap, Hesabım > API anahtarları bölümünden bu anahtarı sil ve parolanı değiştir.\n"
    ))


def build_token_revoked_message(to: str, token: dict) -> EmailMessage:
    return _message(to, "Belge Tabanlı Soru Asistanı: API anahtarın yönetici tarafından iptal edildi", (
        "Merhaba,\n\nBelge Tabanlı Soru Asistanı hesabındaki şu API anahtarı yönetici tarafından iptal edildi:\n\n" + _token_lines(token) +
        "\nBu anahtarı kullanan uygulamalar artık bağlanamaz. Gerekirse Hesabım > API anahtarları bölümünden "
        "yeni bir anahtar oluşturabilirsin.\n"
    ))


def _send(msg: EmailMessage, label: str, to: str, detail: str) -> None:
    """Arka planda (ya da Vercel'de yanittan once) calisir. Hata olursa yalnizca loglanir:
    kullaniciya hata donmek 'bu e-posta kayitli' bilgisini sizdirirdi."""
    if not smtp_configured():
        if config.APP_ENV != "production":
            # ASCII: Windows konsolunun kod sayfasi Turkce harfleri bozabiliyor (olcum: "s?f?rlama" goruldu)
            print(f"[Asistan] {label} (gelistirme modu, SMTP ayari yok): {to} -> {detail}", flush=True)
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


def send_token_created(to: str, token: dict) -> None:
    _send(build_token_created_message(to, token), "Yeni API anahtari bildirimi", to, token["prefix"])


def send_token_revoked(to: str, token: dict) -> None:
    _send(build_token_revoked_message(to, token), "API anahtari iptal bildirimi", to, token["prefix"])
