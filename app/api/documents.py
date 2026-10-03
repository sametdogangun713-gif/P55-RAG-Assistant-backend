from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db
from app.core import config
from app.services import documents as svc
from app.services.embedder import EmbeddingError
from app.services.storage import StorageError

router = APIRouter(prefix="/documents", tags=["documents"])


def _not_found(e):
    return HTTPException(status_code=404, detail=str(e))


@router.post("", status_code=201)
def upload(file: UploadFile = File(...), user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Belge yukler, metni cikarir ve parcalara boler."""
    # Dosya 1 MB'lik bloklar halinde diske akitilir: 500 MB'lik dosya bile bellege tamamen alinmaz
    try:
        doc = svc.upload_document_stream(conn, user, file.filename, file.file, file.content_type)
    except svc.FileTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except svc.DocumentValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return svc.public_document(doc)


class UploadUrlRequest(BaseModel):
    filename: str
    size_bytes: int


class CompleteUploadRequest(BaseModel):
    path: str
    filename: str
    mime_type: Optional[str] = None


def _storage_enabled():
    if config.STORAGE_BACKEND != "supabase":
        raise HTTPException(status_code=400, detail="Doğrudan depo yüklemesi kapalı; dosyayı POST /documents ile gönderin")


@router.post("/upload-url")
def create_upload_url(body: UploadUrlRequest, user: dict = Depends(get_current_user)):
    """Bulut 1. adim: tarayicinin dosyayi Supabase Storage'a dogrudan yukleyecegi tek kullanimlik adres."""
    _storage_enabled()
    try:
        return svc.prepare_storage_upload(user, body.filename, body.size_bytes)
    except svc.FileTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except svc.DocumentValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/complete", status_code=201)
def complete_upload(body: CompleteUploadRequest, user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Bulut 3. adim: depoya yuklenen dosyayi okur, ayristirir, parcalar ve indeksler."""
    _storage_enabled()
    try:
        doc = svc.complete_storage_upload(conn, user, body.path, body.filename, body.mime_type)
    except svc.FileTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except svc.DocumentValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StorageError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return svc.public_document(doc)


@router.get("/limits")
def upload_limits(user: dict = Depends(get_current_user)):
    """Arayuzun gosterdigi sinirlar (.env'den). '/{doc_id}' rotasindan ONCE tanimli olmali, yoksa ona eslesir.

    upload_mode: "direct" = dosya backend'e gonderilir, "storage" = once Supabase Storage'a (bulut).
    """
    return {"max_upload_mb": config.MAX_UPLOAD_MB, "allowed_extensions": list(config.ALLOWED_EXTENSIONS),
            "max_chunks_per_document": config.MAX_CHUNKS_PER_DOCUMENT,
            "upload_mode": "storage" if config.STORAGE_BACKEND == "supabase" else "direct"}


@router.get("")
def list_documents(user: dict = Depends(get_current_user), conn=Depends(get_db)):
    return [svc.public_document(d) for d in svc.list_user_documents(conn, user)]


@router.get("/{doc_id}")
def get_document(doc_id: int, user: dict = Depends(get_current_user), conn=Depends(get_db)):
    try:
        return svc.public_document(svc.get_owned_document(conn, user, doc_id))
    except svc.DocumentNotFoundError as e:
        raise _not_found(e)


@router.get("/{doc_id}/chunks")
def list_chunks(doc_id: int, limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0),
                user: dict = Depends(get_current_user), conn=Depends(get_db)):
    try:
        return svc.list_document_chunks(conn, user, doc_id, limit, offset)
    except svc.DocumentNotFoundError as e:
        raise _not_found(e)


@router.delete("/{doc_id}")
def delete_document(doc_id: int, user: dict = Depends(get_current_user), conn=Depends(get_db)):
    try:
        svc.delete_document(conn, user, doc_id)
    except svc.DocumentNotFoundError as e:
        raise _not_found(e)
    except StorageError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"deleted": True}


@router.post("/{doc_id}/reindex")
def reindex(doc_id: int, user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Belgeyi yeniden vektorlestirir (embedding modeli degistiginde ya da hata sonrasi)."""
    try:
        return svc.public_document(svc.reindex_document(conn, user, doc_id))
    except svc.DocumentNotFoundError as e:
        raise _not_found(e)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EmbeddingError as e:
        raise HTTPException(status_code=503, detail=str(e))
