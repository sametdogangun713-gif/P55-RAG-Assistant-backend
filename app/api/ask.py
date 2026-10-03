from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db, get_llm
from app.api.errors import llm_http_error
from app.services import rag
from app.services.embedder import EmbeddingError
from app.services.llm_client import LLMError

router = APIRouter(tags=["ask"])


class AskRequest(BaseModel):
    question: str
    top_k: Optional[int] = None


@router.post("/ask")
def ask(body: AskRequest, user: dict = Depends(get_current_user), conn=Depends(get_db), llm=Depends(get_llm)):
    """Tek seferlik (sohbet gecmisi olmayan) kaynakli soru-cevap."""
    try:
        result = rag.answer_question(conn, user["id"], body.question, llm, top_k=body.top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EmbeddingError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except LLMError as e:
        raise llm_http_error(e)
    return result.to_dict()
