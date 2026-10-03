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


class EmailNotVerifiedError(Exception):
    """Parola dogru ama e-posta henuz dogrulanmadi."""


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


def validate_name(full_name: str) -> str:
    """Ad soyadi temizler (bas/son ve fazla bosluklar) ve dogrular; temiz hali doner."""
    name = " ".join((full_name or "").split()) if isinstance(full_name, str) else ""
    if not (config.MIN_NAME_LENGTH <= len(name) <= config.MAX_NAME_LENGTH):
        raise ValidationError(f"Ad soyad {config.MIN_NAME_LENGTH}-{config.MAX_NAME_LENGTH} karakter olmalı")
    if not re.search(r"[^\W\d_]", name):           # en az bir harf (Turkce harfler dahil); "123" ad degildir
        raise ValidationError("Ad soyad en az bir harf içermeli")
    if any(not c.isprintable() for c in name):       # gorunmez/denetim karakterleri arayuzde sorun cikarir
        raise ValidationError("Ad soyad geçersiz karakter içeriyor")
    return name


def validate_email(email: str) -> str:
    email = normalize_email(email)
    if not _EMAIL_RE.match(email) or len(email) > 254:
        raise ValidationError("Geçerli bir e-posta adresi girin")
    return email


def register_user(conn, email: str, password: str, role: str = "user",
                  full_name: str = "", verified: bool = True) -> dict:
    """Hesabi dogrudan olusturur (yonetici betigi, testler). Kayit ekrani sign_up() kullanir."""
    email = validate_email(email)
    validate_password(password)
    try:
        return users.create_user(conn, email, security.hash_password(password), role,
                                 full_name=full_name, verified=verified)
    except users.DuplicateEmailError as e:
        raise DuplicateUserError("Bu e-posta zaten kayıtlı") from e


def sign_up(conn, full_name: str, email: str, password: str) -> dict:
    """Kayit ekrani: ad soyad + e-posta + parola. E-posta dogrulamasi aciksa hesap DOGRULANMAMIS acilir.

    Ayni e-postayla dogrulanmamis bir hesap varsa (kod hic girilmemis) ad ve parola yenilenir: adresin sahibi
    henuz kanitlanmadigi icin o hesap kimseye ait sayilmaz. Boylece yanlislikla baskasinin adresini yazan biri,
    gercek sahibinin kayit olmasini engelleyemez. Dogrulanmis hesap varsa "zaten kayitli".
    """
    name = validate_name(full_name)
    email = validate_email(email)
    validate_password(password)
    verified = not config.REQUIRE_EMAIL_VERIFICATION
    existing = users.get_user_by_email(conn, email)
    if existing and not existing["email_verified_at"]:
        users.update_unverified_signup(conn, existing["id"], name, security.hash_password(password))
        return users.get_user_by_id(conn, existing["id"])
    if existing:
        raise DuplicateUserError("Bu e-posta zaten kayıtlı")
    return register_user(conn, email, password, full_name=name, verified=verified)


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
    # Dogrulama kontrolu parola DOGRUYSA yapilir: yanlis parolayla "dogrulanmamis" bilgisi sizmaz.
    if config.REQUIRE_EMAIL_VERIFICATION and not user["email_verified_at"]:
        raise EmailNotVerifiedError("E-posta adresin henüz doğrulanmadı. E-postana gelen 6 haneli kodu gir "
                                    "ya da yeni kod iste")
    return {"access_token": issue_token(user), "user": user}


def issue_token(user: dict) -> str:
    """Giris ve e-posta dogrulama sonrasi verilen oturum anahtari (JWT)."""
    return security.create_access_token(user["id"], user["role"])


_DUMMY_HASH = security.hash_password("sahte-parola-1")


def public_user(user: dict) -> dict:
    """API'ye donerken password_hash gibi alanlari cikar."""
    return {"id": user["id"], "full_name": user.get("full_name") or "", "email": user["email"], "role": user["role"],
            "email_verified": bool(user.get("email_verified_at")), "created_at": user["created_at"]}
