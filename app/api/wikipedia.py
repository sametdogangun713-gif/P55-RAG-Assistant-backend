"""3. parti veri kaynagi: Vikipedi'de arama ve makaleyi belge olarak ekleme."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db
from app.services import documents as docs_svc
from app.services import wikipedia as svc

router = APIRouter(prefix="/wikipedia", tags=["wikipedia"])


def _http_error(e: svc.WikipediaError) -> HTTPException:
    if isinstance(e, svc.WikipediaInputError):
        return HTTPException(status_code=400, detail=str(e))
    if isinstance(e, svc.WikipediaNotFoundError):
        return HTTPException(status_code=404, detail=str(e))
    return HTTPException(status_code=502, detail=str(e))       # dis servis hatasi: bizim hatamiz degil


@router.get("/search")
def search(q: str = Query(..., max_length=svc.MAX_QUERY_LENGTH), lang: str = "tr",
           limit: int = Query(default=5, ge=1, le=svc.MAX_RESULTS), user: dict = Depends(get_current_user)):
    """Vikipedi'de makale arar (baslik + kisa ozet). Veritabanina bir sey yazmaz."""
    try:
        return {"lang": lang, "results": svc.search(lang, q, limit)}
    except svc.WikipediaError as e:
        raise _http_error(e)


class ImportRequest(BaseModel):
    title: str
    lang: str = "tr"


@router.post("/import", status_code=201)
def import_article(body: ImportRequest, user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Makalenin metnini ceker ve kullanicinin belgelerine .txt belgesi olarak ekler (parcalanir, indekslenir)."""
    try:
        article = svc.fetch_article(body.lang, body.title)
    except svc.WikipediaError as e:
        raise _http_error(e)
    safe_title = article["title"].replace("/", "-").replace("\\", "-")   # "AC/DC" yol sayilmasin
    filename = f"Vikipedi - {safe_title}.txt"
    try:
        doc = docs_svc.import_text_document(conn, user, filename, svc.as_document_text(article))
    except docs_svc.FileTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except docs_svc.DocumentValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    out = docs_svc.public_document_with_progress(conn, doc)
    out["source_url"] = article["url"]
    return out
