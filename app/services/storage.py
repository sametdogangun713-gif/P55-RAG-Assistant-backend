"""Supabase Storage istemcisi (bulutta belge dosyalari). Yalnizca standart kutuphane (urllib).

Neden gerekli? Vercel bir istekte en fazla 4,5 MB kabul eder. Bu yuzden buyuk dosya backend'den GECMEZ:
  1) backend, dosya icin tek kullanimlik "imzali yukleme adresi" uretir     -> create_signed_upload_url
  2) tarayici dosyayi bu adrese dogrudan PUT eder (Supabase'e)
  3) backend dosyayi Supabase'ten parca parca okuyup isler                  -> open_object
Kova (bucket) gizlidir: dosyaya yalnizca SUPABASE_SERVICE_ROLE_KEY ile erisilir. Bu anahtar her seye
erisebildigi icin yalnizca backend'de (.env / Vercel paneli) durur; tarayiciya ASLA gonderilmez.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

from app.core import config


class StorageError(Exception):
    """Dosya deposuna erisilemedi ya da istek reddedildi."""


def _base() -> str:
    if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY:
        raise StorageError("Supabase Storage ayarlı değil (SUPABASE_URL ve SUPABASE_SERVICE_ROLE_KEY gerekli)")
    return config.SUPABASE_URL + "/storage/v1"


def _headers(extra=None) -> dict:
    """Yeni Supabase gizli anahtari (sb_secret_...) yalnizca `apikey` basliginda gider; JWT degildir, Bearer
    olarak gonderilirse reddedilir. Eski "service_role" anahtari bir JWT'dir (eyJ...); onu iki baslikta da gonderiyoruz."""
    key = config.SUPABASE_SERVICE_ROLE_KEY
    h = {"apikey": key, "User-Agent": "P55-RAG-Assistant/1.0"}
    if key.startswith("eyJ"):
        h["Authorization"] = "Bearer " + key
    h.update(extra or {})
    return h


def _quote(path: str) -> str:
    return urllib.parse.quote(path, safe="/")


def _call(method: str, url: str, body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method,
                                 headers=_headers({"Content-Type": "application/json"} if data else None))
    try:
        return urllib.request.urlopen(req, timeout=config.STORAGE_TIMEOUT_SECONDS)
    except urllib.error.HTTPError as e:
        raise StorageError(f"Dosya deposu isteği reddedildi ({e.code})") from None
    except (urllib.error.URLError, TimeoutError) as e:
        raise StorageError(f"Dosya deposuna ulaşılamadı: {getattr(e, 'reason', e)}") from None


def create_signed_upload_url(path: str) -> str:
    """Tarayicinin dosyayi PUT edecegi tam adres (icinde tek kullanimlik token var, ~2 saat gecerli)."""
    url = f"{_base()}/object/upload/sign/{config.SUPABASE_BUCKET}/{_quote(path)}"
    with _call("POST", url, {}) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    rel = data.get("url") or ""
    if "token=" not in rel:
        raise StorageError("Dosya deposu imzalı adres döndürmedi")
    return _base() + rel                       # rel: "/object/upload/sign/<kova>/<yol>?token=..."


def open_object(path: str):
    """Dosyayi okumak icin akis (resp.read(n) ile parca parca okunur; with blogunda kullanilir)."""
    return _call("GET", f"{_base()}/object/{config.SUPABASE_BUCKET}/{_quote(path)}")


def delete_objects(paths) -> None:
    paths = [p for p in paths if p]
    if not paths:
        return
    with _call("DELETE", f"{_base()}/object/{config.SUPABASE_BUCKET}", {"prefixes": paths}):
        pass


def ensure_bucket() -> bool:
    """Gizli kovayi olusturur (kurulum betigi icin). Zaten varsa False doner."""
    body = {"id": config.SUPABASE_BUCKET, "name": config.SUPABASE_BUCKET, "public": False,
            "file_size_limit": config.MAX_UPLOAD_MB * 1024 * 1024}
    try:
        with _call("POST", f"{_base()}/bucket", body):
            return True
    except StorageError as e:
        if "(400)" in str(e) or "(409)" in str(e):      # "already exists"
            return False
        raise
