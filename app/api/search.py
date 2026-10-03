from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db
from app.services import vector_search
from app.services.embedder import EmbeddingError

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    document_ids: Optional[List[int]] = None


@router.post("")
def search_documents(body: SearchRequest, user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Kullanicinin kendi belgelerinde anlamsal (vektor) arama yapar."""
    try:
        results = vector_search.search(conn, user["id"], body.query, body.top_k, body.document_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EmbeddingError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"query": body.query, "results": results}
