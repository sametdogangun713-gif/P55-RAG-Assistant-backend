"""Kayit / giris is kurallari. HTTP bilmez; hatalari kendi istisnalariyla bildirir."""
import re
import time

from app.core import config, security
from app.db import users

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Basarisiz giris sayaci (bellekte): {e-posta: [deneme_sayisi, ilk_deneme_zamani]}
_failed = {}
MAX_TRACKED_EMAILS = 5000      # sayac tablosu sinirsiz buyumesin (cok sayida rastgele e-postayla bellek doldurma)


class ValidationError(Exception):
    pass


class DuplicateUserError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AccountLockedError(Exception):
    pass


def reset_failed_attempts():
    _failed.clear()


def clear_failed_attempts(email: str):
    """Hafta 14: parola sifirlaninca o e-postanin kilidi kalkar."""
    _failed.pop(normalize_email(email), None)


def _purge_failed():
    """Tablo sinira ulasirsa once suresi dolanlari, gerekirse en eski kayitlari siler."""
    if len(_failed) <= MAX_TRACKED_EMAILS:
        return
    now = time.time()
    for k in [k for k, (_, first) in _failed.items() if now - first > config.LOCKOUT_SECONDS]:
        del _failed[k]
    if len(_failed) > MAX_TRACKED_EMAILS:
        for k, _ in sorted(_failed.items(), key=lambda kv: kv[1][1])[: len(_failed) - MAX_TRACKED_EMAILS]:
            del _failed[k]


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def validate_password(password: str):
    if not isinstance(password, str) or len(password) < config.MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Parola en az {config.MIN_PASSWORD_LENGTH} karakter olmalı")
    if not (re.search(r"[A-Za-z]", password) and re.search(r"\d", password)):
        raise ValidationError("Parola en az bir harf ve bir rakam içermeli")


def register_user(conn, email: str, password: str, role: str = "user") -> dict:
    email = normalize_email(email)
    if not _EMAIL_RE.match(email) or len(email) > 254:
        raise ValidationError("Geçerli bir e-posta adresi girin")
    validate_password(password)
    try:
        return users.create_user(conn, email, security.hash_password(password), role)
    except users.DuplicateEmailError as e:
        raise DuplicateUserError("Bu e-posta zaten kayıtlı") from e


def _check_lock(email: str):
    entry = _failed.get(email)
    if not entry:
        return
    count, first = entry
    if time.time() - first > config.LOCKOUT_SECONDS:
        _failed.pop(email, None)
        return
    if count >= config.MAX_FAILED_LOGINS:
        raise AccountLockedError("Çok fazla başarısız deneme. Biraz sonra tekrar deneyin")


def login(conn, email: str, password: str) -> dict:
    """Basarili ise {'access_token', 'user'} doner.

    Hata mesaji bilerek GENEL: 'e-posta yok' ile 'parola yanlis' ayirt edilmez (kullanici numaralandirmayi onler).
    """
    email = normalize_email(email)
    _check_lock(email)
    user = users.get_user_by_email(conn, email)
    # Kullanici yoksa bile bir hash hesapla: yanit suresi farki bilgi sizdirmasin
    stored = user["password_hash"] if user else _DUMMY_HASH
    ok = security.verify_password(password or "", stored)
    if not user or not ok:
        entry = _failed.setdefault(email, [0, time.time()])
        entry[0] += 1
        _purge_failed()
        raise InvalidCredentialsError("E-posta veya parola hatalı")
    _failed.pop(email, None)
    token = security.create_access_token(user["id"], user["role"])
    return {"access_token": token, "user": user}


_DUMMY_HASH = security.hash_password("sahte-parola-1")


def public_user(user: dict) -> dict:
    """API'ye donerken password_hash gibi alanlari cikar."""
    return {"id": user["id"], "email": user["email"], "role": user["role"], "created_at": user["created_at"]}
