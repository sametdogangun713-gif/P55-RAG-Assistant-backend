"""Parola sifirlama is kurallari (Hafta 14). HTTP bilmez, e-posta gondermez (o is mailer.py'nin).

Akis: 1) kullanici e-postasini yazar -> 6 haneli kod uretilir, ozeti saklanir, kod e-postayla gider
      2) kullanici kodu ve yeni parolayi yazar -> kod dogruysa parola degisir, kod silinir.
Guvenlik kararlari:
  - Yanit e-postanin kayitli olup olmadigini SOYLEMEZ (kullanici numaralandirma onlemi).
  - Kodun uretimi/saklanmasi/dogrulanmasi email_codes.py'de (HMAC ozeti, 15 dk, 5 yanlis deneme, tek kullanimlik).
"""
import time

from app.core import config, security
from app.db import users
from app.services import auth, email_codes

PURPOSE = "reset"
InvalidResetCodeError = email_codes.InvalidCodeError     # API katmani bu adla yakalar


def request_reset(conn, email: str, now=None):
    """Kayitli e-posta icin kod uretir ve (e-posta, kod) doner; aksi halde None.

    None donmesi cagirana "bir sey gonderme" demektir; kullaniciya yine ayni genel mesaj gosterilir.
    """
    now = int(time.time() if now is None else now)
    user = users.get_user_by_email(conn, auth.normalize_email(email))
    if not user:
        return None
    code = email_codes.issue(conn, user["id"], PURPOSE, config.RESET_CODE_MINUTES, now)
    return (user["email"], code) if code else None   # cok sik istek: yeni kod yok, oncekini kullansin


def reset_password(conn, email: str, code: str, new_password: str, now=None) -> None:
    """Kod dogruysa parolayi degistirir. Her turlu hatada ayni genel mesaj (hangi adimin tuttugu sizmasin)."""
    now = int(time.time() if now is None else now)
    auth.validate_password(new_password)             # zayif parolada kodu harcamadan once uyar
    user = users.get_user_by_email(conn, auth.normalize_email(email))
    if not user:
        raise InvalidResetCodeError(email_codes.GENERIC_ERROR)
    email_codes.consume(conn, user["id"], PURPOSE, code, now)
    users.update_password_hash(conn, user["id"], security.hash_password(new_password))
    # Koda e-postadan ulasabildi: adresin sahibi oldugu kanitlandi, dogrulanmamissa dogrulanmis sayilir.
    users.mark_email_verified(conn, user["id"])
    auth.clear_failed_attempts(user["email"])        # yeni parolayla hemen giris yapabilsin
