"""E-postayla gonderilen 6 haneli tek kullanimlik kodlar: uretme ve dogrulama.

Iki yerde kullanilir: kayitta e-posta dogrulama (purpose='verify') ve parola sifirlama (purpose='reset').
Guvenlik kurallari ikisinde de aynidir, bu yuzden tek yerde yazildi:
  - Kod duz metin saklanmaz: HMAC-SHA256(SECRET_KEY, kod). 6 haneli kodun duz SHA256'si 1 milyon denemeyle
    cozulurdu; HMAC'te SECRET_KEY bilinmeden cozulemez.
  - Sureli (dakika, cagiran belirler), en fazla RESET_MAX_ATTEMPTS yanlis deneme, tek kullanimlik.
  - Ayni kullaniciya RESET_RESEND_SECONDS'tan sik kod uretilmez (posta kutusunu bombalama onlemi).
"""
import hashlib
import hmac
import secrets

from app.core import config
from app.db import email_codes


class InvalidCodeError(Exception):
    pass


GENERIC_ERROR = "Kod hatalı veya süresi dolmuş. Yeni kod isteyebilirsin"


def hash_code(code: str) -> str:
    return hmac.new(config.SECRET_KEY.encode("utf-8"), code.encode("utf-8"), hashlib.sha256).hexdigest()


def issue(conn, user_id: int, purpose: str, minutes: int, now: int):
    """Yeni kod uretip ozetini saklar ve kodu doner. Cok sik istekte None doner (yeni kod uretilmez)."""
    last = email_codes.get_latest(conn, user_id, purpose)
    if last and now - last["created_at"] < config.RESET_RESEND_SECONDS:
        return None
    code = f"{secrets.randbelow(1_000_000):06d}"     # secrets: tahmin edilemez rastgelelik (random modulu degil)
    email_codes.replace_code(conn, user_id, purpose, hash_code(code), now + minutes * 60, now)
    return code


def consume(conn, user_id: int, purpose: str, code: str, now: int) -> None:
    """Kod dogruysa siler (tek kullanimlik), degilse InvalidCodeError. Her hatada AYNI mesaj:
    'kod yok', 'suresi doldu', 'yanlis' ayirt edilmez (hangi adimin tuttugu sizmasin)."""
    row = email_codes.get_latest(conn, user_id, purpose)
    if not row or now > row["expires_at"] or row["attempts"] >= config.RESET_MAX_ATTEMPTS:
        raise InvalidCodeError(GENERIC_ERROR)
    if not hmac.compare_digest(hash_code((code or "").strip()), row["code_hash"]):   # sabit zamanli karsilastirma
        email_codes.add_attempt(conn, row["id"])
        raise InvalidCodeError(GENERIC_ERROR)
    email_codes.delete_for_user(conn, user_id, purpose)
