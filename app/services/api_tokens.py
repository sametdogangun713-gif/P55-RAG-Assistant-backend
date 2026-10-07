"""Kisisel API anahtarlari: uretme, listeleme, iptal etme ve istekte dogrulama. HTTP bilmez.

Neden JWT'den ayri bir anahtar?
  - Giriste verilen JWT kisa omurludur (ACCESS_TOKEN_EXPIRE_MINUTES) ve tarayici icindir. Bir betik ya da
    baska bir uygulama (3. parti) her saatte parola ile giris yapmamali; parolayi o uygulamaya vermek de yanlis.
  - API anahtari uzun omurludur (en fazla 1 yil) ve tek tek IPTAL edilebilir: biri sizarsa yalnizca o silinir,
    parola ve diger anahtarlar etkilenmez. JWT'de bu yok (bilinen sinir: token iptali yok).

Guvenlik kararlari:
  - Anahtar `secrets` ile uretilir (32 bayt = 256 bit rastgelelik); tahmin edilemez.
  - Veritabaninda yalnizca SHA-256 OZETI saklanir. Parolada yavas scrypt + tuz kullaniyoruz cunku parolalar kisa
    ve tahmin edilebilir; 256 bitlik rastgele bir anahtari kaba kuvvetle bulmak imkansiz oldugundan hizli bir ozet
    yeterli ve her istekte calistigi icin hizli olmasi da gerekli (GitHub'in kisisel anahtarlari da boyle).
  - Anahtar yalnizca uretildigi yanitta bir kez dondurulur; sonra kimse (yonetici dahil) goremez.
  - Anahtar uretilince ve yonetici iptal edince hesap sahibine e-posta gider (anahtarin kendisi e-postada yok).
  - Anahtarla anahtar uretilemez/silinemez, parola degistirilemez, hesap silinemez (api/deps.py require_session):
    sizan bir anahtar kendini kalici hale getiremesin ve hesabi ele geciremesin.
"""
import hashlib
import secrets
import time

from app.core import config
from app.db import api_tokens as repo
from app.db import users

TOKEN_PREFIX = "bsa_"            # JWT'ler "eyJ" ile baslar; bu onek iki tur anahtari ayirmamizi saglar
LEGACY_PREFIXES = ("p55_",)      # eski adla uretilmis anahtarlar suresi dolana kadar calismaya devam eder
PREFIX_LENGTH = 12               # listede gosterilen kisim: "bsa_" + 8 karakter
EXPIRY_DAYS = (7, 30, 90, 365)   # suresiz anahtar yok: unutulan anahtar bir gun kendiliginden olur
DEFAULT_EXPIRY_DAYS = 90
MAX_NAME_LENGTH = 60


class TokenValidationError(Exception):
    pass


class TokenLimitError(Exception):
    pass


def _now() -> float:
    """Testlerde sahte saatle degistirilir."""
    return time.time()


def _text(ts: float) -> str:
    """created_at ile ayni bicim ('YYYY-MM-DD HH:MM:SS', UTC): metin olarak karsilastirilabilir."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ts))


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def looks_like_api_token(token: str) -> bool:
    return token.startswith((TOKEN_PREFIX,) + LEGACY_PREFIXES)


def _with_status(row: dict, now_text: str) -> dict:
    return {**row, "expired": row["expires_at"] <= now_text}


def create_token(conn, user: dict, name: str, expires_in_days=None) -> dict:
    """Yeni anahtar uretir. Donen sozlukteki "token" alani anahtarin TEK gosterimidir; baska yerde saklanmaz."""
    name = " ".join((name or "").split())
    if not name:
        raise TokenValidationError("Anahtara bir ad ver (örneğin: Postman)")
    if len(name) > MAX_NAME_LENGTH:
        raise TokenValidationError(f"Anahtar adı en fazla {MAX_NAME_LENGTH} karakter olabilir")
    days = DEFAULT_EXPIRY_DAYS if expires_in_days is None else expires_in_days
    if days not in EXPIRY_DAYS:
        raise TokenValidationError("Geçerlilik süresi " + ", ".join(map(str, EXPIRY_DAYS)) + " günden biri olmalı")
    if repo.count_for_user(conn, user["id"]) >= config.MAX_API_TOKENS_PER_USER:
        raise TokenLimitError(f"En fazla {config.MAX_API_TOKENS_PER_USER} API anahtarın olabilir. "
                              "Kullanmadığın bir anahtarı sil")
    token = TOKEN_PREFIX + secrets.token_urlsafe(32)
    now = _now()
    row = repo.create_token(conn, user["id"], name, token[:PREFIX_LENGTH], hash_token(token),
                            _text(now), _text(now + days * 86400))
    return {**_with_status(row, _text(now)), "token": token}


def list_tokens(conn, user: dict) -> list:
    now_text = _text(_now())
    return [_with_status(r, now_text) for r in repo.list_for_user(conn, user["id"])]


def revoke_token(conn, user: dict, token_id: int) -> bool:
    return repo.delete_token(conn, user["id"], token_id)


def public_info(row: dict) -> dict:
    """Bildirim e-postasina giden bilgi: anahtarin kendisi ("token") ve ozeti asla bu sozluge girmez."""
    return {k: row.get(k) for k in ("name", "prefix", "created_at", "expires_at")}


# --- Yonetici: anahtarlari GORUR (ad, ilk 12 karakter, sahibi, tarihler) ve sizan anahtari IPTAL EDER.
# Yonetici anahtar URETEMEZ ve anahtarin kendisini goremez: boylece hesaba yalnizca anahtari olusturan sahibi
# girebilir; yonetici ikinci bir giris yolu acamaz. Iptal edilince sahibine e-posta gider (api/admin.py).
def list_all_tokens(conn) -> list:
    now_text = _text(_now())
    return [_with_status(r, now_text) for r in repo.list_all(conn)]


def admin_revoke(conn, token_id: int):
    """Anahtari siler ve silinen satiri (sahibinin e-postasiyla) dondurur; yoksa None."""
    row = repo.get_with_owner(conn, token_id)
    if row is None or not repo.delete_by_id(conn, token_id):
        return None
    return row


def authenticate(conn, token: str):
    """Anahtar gecerliyse sahibini (kullanici satiri) dondurur; yoksa, suresi dolmussa ya da iptal edildiyse None.

    Anahtar ozetiyle aranir: veritabani anahtarin kendisini hic gormez.
    """
    row = repo.get_by_hash(conn, hash_token(token))
    if row is None:
        return None
    now_text = _text(_now())
    if row["expires_at"] <= now_text:
        return None
    # "Son kullanim" dakikada en fazla bir kez yazilir: her istekte veritabanina yazmamak icin
    if (row["last_used_at"] or "")[:16] != now_text[:16]:
        repo.touch(conn, row["id"], now_text)
    return users.get_user_by_id(conn, row["user_id"])
