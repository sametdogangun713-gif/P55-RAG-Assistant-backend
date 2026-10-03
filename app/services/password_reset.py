"""Parola sifirlama is kurallari (Hafta 14). HTTP bilmez, e-posta gondermez (o is mailer.py'nin).

Akis: 1) kullanici e-postasini yazar -> 6 haneli kod uretilir, ozeti saklanir, kod e-postayla gider
      2) kullanici kodu ve yeni parolayi yazar -> kod dogruysa parola degisir, kod silinir.
Guvenlik kararlari:
  - Yanit e-postanin kayitli olup olmadigini SOYLEMEZ (kullanici numaralandirma onlemi).
  - Kod duz metin saklanmaz: HMAC-SHA256(SECRET_KEY, kod). 6 haneli kodun duz SHA256'si 1 milyon denemeyle
    cozulurdu; HMAC'te SECRET_KEY bilinmeden cozulemez.
  - Kod 15 dk gecerli, en fazla 5 yanlis deneme, tek kullanimlik.
"""
import hashlib
import hmac
import secrets
import time

from app.core import config, security
from app.db import password_resets, users
from app.services import auth


class InvalidResetCodeError(Exception):
    pass


def _hash_code(code: str) -> str:
    return hmac.new(config.SECRET_KEY.encode("utf-8"), code.encode("utf-8"), hashlib.sha256).hexdigest()


def request_reset(conn, email: str, now=None):
    """Kayitli e-posta icin kod uretir ve (e-posta, kod) doner; aksi halde None.

    None donmesi cagirana "bir sey gonderme" demektir; kullaniciya yine ayni genel mesaj gosterilir.
    """
    now = int(time.time() if now is None else now)
    email = auth.normalize_email(email)
    user = users.get_user_by_email(conn, email)
    if not user:
        return None
    last = password_resets.get_latest(conn, user["id"])
    if last and now - last["created_at"] < config.RESET_RESEND_SECONDS:
        return None                                  # cok sik istek: yeni kod uretme, oncekini kullansin
    code = f"{secrets.randbelow(1_000_000):06d}"     # secrets: tahmin edilemez rastgelelik (random modulu degil)
    password_resets.replace_code(conn, user["id"], _hash_code(code), now + config.RESET_CODE_MINUTES * 60, now)
    return user["email"], code


def reset_password(conn, email: str, code: str, new_password: str, now=None) -> None:
    """Kod dogruysa parolayi degistirir. Her turlu hatada ayni genel mesaj (hangi adimin tuttugu sizmasin)."""
    now = int(time.time() if now is None else now)
    auth.validate_password(new_password)             # zayif parolada kodu harcamadan once uyar
    generic = InvalidResetCodeError("Kod hatalı veya süresi dolmuş. Yeni kod isteyebilirsin")
    user = users.get_user_by_email(conn, auth.normalize_email(email))
    row = password_resets.get_latest(conn, user["id"]) if user else None
    if not row or now > row["expires_at"] or row["attempts"] >= config.RESET_MAX_ATTEMPTS:
        raise generic
    if not hmac.compare_digest(_hash_code((code or "").strip()), row["code_hash"]):   # sabit zamanli karsilastirma
        password_resets.add_attempt(conn, row["id"])
        raise generic
    users.update_password_hash(conn, user["id"], security.hash_password(new_password))
    password_resets.delete_for_user(conn, user["id"])  # tek kullanimlik
    auth.clear_failed_attempts(user["email"])        # yeni parolayla hemen giris yapabilsin
