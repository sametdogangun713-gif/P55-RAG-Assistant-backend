"""Belge yukleme is kurallari: dogrulama, kaydetme, ayristirma, parcalama, sahiplik kontrolu."""
import io
import os
import re
import uuid
from pathlib import Path

from app.core import config
from app.db import chunks as chunks_repo
from app.db import documents as documents_repo
from app.services import chunker, indexing, parser, storage
from app.services.embedder import EmbeddingError


class DocumentValidationError(Exception):
    pass


class FileTooLargeError(DocumentValidationError):
    pass


class DocumentNotFoundError(Exception):
    pass


COPY_BLOCK = 1024 * 1024        # diske yazarken her seferde okunan miktar (1 MB): 500 MB'lik dosya bellege alinmaz


def sanitize_filename(name) -> str:
    """Yol bilesenlerini ve kontrol karakterlerini atar ('../../x.txt' -> 'x.txt')."""
    base = os.path.basename(str(name or "").replace("\\", "/"))
    base = re.sub(r"[\x00-\x1f\x7f]", "", base).strip()
    if not base or base in (".", ".."):
        raise DocumentValidationError("Geçerli bir dosya adı gerekli")
    if len(base) > 150:                      # kirparken UZANTIYI koru (aksi halde gecerli dosya reddedilirdi)
        stem, ext = os.path.splitext(base)
        ext = ext[:20]
        base = stem[:150 - len(ext)] + ext
    return base


def _content_matches_extension(ext: str, data: bytes) -> bool:
    if ext == ".pdf":
        return data[:5] == b"%PDF-"
    if ext == ".docx":
        return data[:2] == b"PK"     # docx bir zip dosyasidir
    return True


def upload_document(conn, user: dict, filename, data: bytes, mime_type=None, embedder=None) -> dict:
    """Bayt dizisiyle yukleme (testler, betikler). Asil is upload_document_stream'de."""
    return upload_document_stream(conn, user, filename, io.BytesIO(data), mime_type, embedder)


def _save_stream(stream, first: bytes, path: Path) -> int:
    """Akistaki veriyi COPY_BLOCK'luk parcalar halinde diske yazar, yazilan bayt sayisini dondurur.

    Sinir asilirsa yarim dosya silinir ve FileTooLargeError atilir. Bellekte ayni anda en fazla 1 MB tutulur.
    """
    limit = config.MAX_UPLOAD_MB * 1024 * 1024
    size = 0
    try:
        with open(path, "wb") as f:
            block = first
            while block:
                size += len(block)
                if size > limit:
                    raise FileTooLargeError(f"Dosya {config.MAX_UPLOAD_MB} MB sınırını aşıyor")
                f.write(block)
                block = stream.read(COPY_BLOCK)
    except BaseException:
        path.unlink(missing_ok=True)          # yarim kalan dosya diskte yer kaplamasin
        raise
    return size


def _check_name(filename):
    """Dosya adini temizler, uzantiyi denetler. (temiz_ad, uzanti) dondurur."""
    name = sanitize_filename(filename)
    ext = Path(name).suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise DocumentValidationError("Desteklenen türler: " + ", ".join(config.ALLOWED_EXTENSIONS))
    return name, ext


def _read_head(stream, ext: str) -> bytes:
    head = stream.read(8)                             # tur kontrolu icin ilk baytlar yeter (%PDF- / PK)
    if not head:
        raise DocumentValidationError("Dosya boş")
    if not _content_matches_extension(ext, head):
        raise DocumentValidationError("Dosya içeriği uzantısıyla uyuşmuyor")
    return head


def _temp_path(ext: str) -> Path:
    upload_dir = Path(config.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir / f"{uuid.uuid4().hex}{ext}"    # kullanici adi diske yazilmaz -> yol saldirisi olmaz


def upload_document_stream(conn, user: dict, filename, stream, mime_type=None, embedder=None) -> dict:
    """stream: .read(n) metodu olan dosya benzeri nesne (FastAPI'de UploadFile.file). Dosya sunucu diskinde kalir."""
    name, ext = _check_name(filename)
    head = _read_head(stream, ext)
    path = _temp_path(ext)
    size = _save_stream(stream, head, path)
    return _process(conn, user, name, ext, path, path.name, mime_type, size, embedder)


# --- Bulut: Supabase Storage uzerinden yukleme (STORAGE_BACKEND=supabase) ---
def _storage_path_re(user_id: int):
    exts = "|".join(e.lstrip(".") for e in config.ALLOWED_EXTENSIONS)
    return re.compile(rf"^{int(user_id)}/[0-9a-f]{{32}}\.({exts})$")


def prepare_storage_upload(user: dict, filename, size_bytes: int) -> dict:
    """1. adim: dosya icin depoda bir yol ve tek kullanimlik yukleme adresi uretir (dosya henuz yok).

    Boyut burada tarayicinin SOYLEDIGI degerle erken denetlenir; asil denetim 3. adimda gercek baytlarla yapilir.
    """
    _, ext = _check_name(filename)
    if size_bytes <= 0:
        raise DocumentValidationError("Dosya boş")
    if size_bytes > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise FileTooLargeError(f"Dosya {config.MAX_UPLOAD_MB} MB sınırını aşıyor")
    path = f"{user['id']}/{uuid.uuid4().hex}{ext}"    # kullanici klasoru + rastgele ad: tahmin edilemez
    return {"path": path, "upload_url": storage.create_signed_upload_url(path)}


def complete_storage_upload(conn, user: dict, path: str, filename, mime_type=None, embedder=None) -> dict:
    """3. adim: tarayici dosyayi depoya yukledi; backend dosyayi okuyup ayristirir, parcalar, indeksler.

    Kullanici yalnizca KENDI klasorundeki bir yolu bildirebilir (baskasinin dosyasini isletemez).
    """
    if not isinstance(path, str) or not _storage_path_re(user["id"]).match(path):
        raise DocumentValidationError("Geçersiz dosya yolu")
    name, ext = _check_name(filename)
    if not path.endswith(ext):
        raise DocumentValidationError("Dosya adı ile yüklenen dosyanın uzantısı uyuşmuyor")
    tmp = _temp_path(ext)
    try:
        with storage.open_object(path) as stream:
            head = _read_head(stream, ext)
            size = _save_stream(stream, head, tmp)
    except DocumentValidationError:
        storage.delete_objects([path])                # gecersiz/cok buyuk dosya depoda yer kaplamasin
        raise
    try:
        return _process(conn, user, name, ext, tmp, path, mime_type, size, embedder)
    finally:
        tmp.unlink(missing_ok=True)                   # asil dosya depoda; gecici kopya silinir


def _process(conn, user, name, ext, path: Path, stored_name, mime_type, size, embedder) -> dict:
    """Diskteki dosyayi ayristirir, parcalar ve indeksler; belge kaydini dondurur."""
    doc = documents_repo.create_document(conn, user["id"], name, stored_name, mime_type, size)
    try:
        pages = parser.parse_file(path, ext)
        chunk_list = chunker.chunk_pages(pages)
        if not chunk_list:
            documents_repo.set_status(conn, doc["id"], "failed",
                                      "Belgeden metin çıkarılamadı (taranmış/görsel bir PDF olabilir)")
        elif len(chunk_list) > config.MAX_CHUNKS_PER_DOCUMENT:
            documents_repo.set_status(conn, doc["id"], "failed",
                                      f"Belgede çok fazla metin var ({len(chunk_list)} parça, sınır "
                                      f"{config.MAX_CHUNKS_PER_DOCUMENT}). Belgeyi bölerek yükleyin.")
        else:
            chunks_repo.add_chunks(conn, doc["id"], [(c.index, c.content, c.page_no) for c in chunk_list])
            documents_repo.set_status(conn, doc["id"], "chunked")
            _try_index(conn, doc["id"], embedder)
    except parser.ParseError as e:
        documents_repo.set_status(conn, doc["id"], "failed", str(e))
    return documents_repo.get_document(conn, doc["id"])


def _try_index(conn, doc_id: int, embedder=None) -> None:
    """Embedding basarisiz olsa da parcalar korunur; belge 'failed' olur ve yeniden indekslenebilir."""
    try:
        indexing.index_document(conn, doc_id, embedder)
    except EmbeddingError as e:
        documents_repo.set_status(conn, doc_id, "failed", f"Gömme üretilemedi: {e}")


def reindex_document(conn, user: dict, doc_id: int, embedder=None) -> dict:
    """Parcalari olan bir belgeyi yeniden vektorlestirir (model degisti ya da onceki deneme basarisiz oldu).

    EmbeddingError cagirana yukselir (API 503 doner).
    """
    get_owned_document(conn, user, doc_id)
    indexing.index_document(conn, doc_id, embedder)
    return documents_repo.get_document(conn, doc_id)


def get_owned_document(conn, user: dict, doc_id: int) -> dict:
    """Belge yoksa VEYA baskasinin ise ayni hata (varligini sizdirmamak icin). Yonetici hepsine erisir."""
    doc = documents_repo.get_document(conn, doc_id)
    if doc is None or (doc["user_id"] != user["id"] and user["role"] != "admin"):
        raise DocumentNotFoundError("Belge bulunamadı")
    return doc


def list_user_documents(conn, user: dict) -> list:
    return documents_repo.list_documents(conn, user_id=user["id"])


def list_document_chunks(conn, user: dict, doc_id: int, limit: int = 50, offset: int = 0) -> list:
    get_owned_document(conn, user, doc_id)
    return chunks_repo.list_chunks(conn, doc_id, limit=limit, offset=offset)


def remove_stored_files(stored_names) -> None:
    """Belgelerin dosyalarini siler. 'kullanici/ad.pdf' bicimli adlar Supabase Storage'da, digerleri diskte."""
    remote = [s for s in stored_names if s and "/" in s]
    for s in stored_names:
        if s and "/" not in s:
            (Path(config.UPLOAD_DIR) / s).unlink(missing_ok=True)
    if remote:
        storage.delete_objects(remote)


def delete_document(conn, user: dict, doc_id: int) -> None:
    doc = get_owned_document(conn, user, doc_id)
    remove_stored_files([doc.get("stored_name")])
    documents_repo.delete_document(conn, doc_id)      # parcalar CASCADE ile silinir


def public_document(doc: dict) -> dict:
    """API'ye donecek alanlar (stored_name gibi ic ayrintilar cikarilir)."""
    keys = ("id", "filename", "mime_type", "size_bytes", "status", "error", "uploaded_at",
            "chunk_count", "owner_email")
    return {k: doc.get(k) for k in keys}
