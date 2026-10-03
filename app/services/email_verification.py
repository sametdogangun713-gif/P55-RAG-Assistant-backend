"""E-posta dogrulama is kurallari. HTTP bilmez, e-posta gondermez (o is mailer.py'nin).

Neden: kayitta yazilan e-posta yanlis (yazim hatasi) ya da baskasinin olabilir. Yanlis adresle acilan hesapta
"Sifremi unuttum" hic calismaz; baskasinin adresiyle acilan hesap ise o kisiye ait gibi gorunur.
Kodu girebilen kisi o posta kutusuna erisebiliyor demektir: adres hem dogru hem de onun.

Akis: kayit -> hesap dogrulanmamis acilir + 6 haneli kod e-postaya gider -> kod girilince email_verified_at
dolar ve kullanici giris yapmis olur. Dogrulanmamis hesap giris yapamaz (auth.login).
"""
import time

from app.core import config
from app.db import users
from app.services import auth, email_codes

PURPOSE = "verify"


def issue_code(conn, user: dict, now=None):
    """Kayittan hemen sonra cagrilir: kod (str) ya da cok sik istekte None."""
    now = int(time.time() if now is None else now)
    return email_codes.issue(conn, user["id"], PURPOSE, config.VERIFY_CODE_MINUTES, now)


def request_code(conn, email: str, now=None):
    """"Kodu yeniden gonder": e-posta kayitli VE dogrulanmamissa (e-posta, kod), aksi halde None.
    Yanit her durumda ayni olur (hangi e-postanin kayitli oldugu sizmasin)."""
    user = users.get_user_by_email(conn, auth.normalize_email(email))
    if not user or user["email_verified_at"]:
        return None
    code = issue_code(conn, user, now)
    return (user["email"], code) if code else None


def verify(conn, email: str, code: str, now=None) -> dict:
    """Kod dogruysa e-postayi dogrulanmis yapar ve guncel kullaniciyi doner; degilse InvalidCodeError."""
    now = int(time.time() if now is None else now)
    user = users.get_user_by_email(conn, auth.normalize_email(email))
    if not user:
        raise email_codes.InvalidCodeError(email_codes.GENERIC_ERROR)
    if user["email_verified_at"]:
        raise email_codes.InvalidCodeError("Bu e-posta zaten doğrulanmış. Giriş yapabilirsin")
    email_codes.consume(conn, user["id"], PURPOSE, code, now)
    users.mark_email_verified(conn, user["id"])
    return users.get_user_by_id(conn, user["id"])
