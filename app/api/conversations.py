from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db, get_llm
from app.api.errors import llm_http_error
from app.services import chat
from app.services.embedder import EmbeddingError
from app.services.llm_client import LLMError

router = APIRouter(prefix="/conversations", tags=["conversations"])


class NewConversation(BaseModel):
    title: Optional[str] = None


class NewMessage(BaseModel):
    content: str


def _not_found(e):
    return HTTPException(status_code=404, detail=str(e))


@router.post("", status_code=201)
def create_conversation(body: NewConversation, user: dict = Depends(get_current_user), conn=Depends(get_db)):
    return chat.create_conversation(conn, user, body.title)


@router.get("")
def list_conversations(user: dict = Depends(get_current_user), conn=Depends(get_db)):
    return chat.list_conversations(conn, user)


@router.get("/{conv_id}/messages")
def list_messages(conv_id: int, user: dict = Depends(get_current_user), conn=Depends(get_db)):
    try:
        return chat.list_messages(conn, user, conv_id)
    except chat.ConversationNotFoundError as e:
        raise _not_found(e)


@router.post("/{conv_id}/messages")
def send_message(conv_id: int, body: NewMessage, user: dict = Depends(get_current_user), conn=Depends(get_db),
                 llm=Depends(get_llm)):
    """Soruyu belgelere dayanarak yanitlar; konusma gecmisini baglam olarak kullanir ve kaydeder."""
    try:
        return chat.send_message(conn, user, conv_id, body.content, llm)
    except chat.ConversationNotFoundError as e:
        raise _not_found(e)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except EmbeddingError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except LLMError as e:
        raise llm_http_error(e)


@router.delete("/{conv_id}")
def delete_conversation(conv_id: int, user: dict = Depends(get_current_user), conn=Depends(get_db)):
    try:
        chat.delete_conversation(conn, user, conv_id)
    except chat.ConversationNotFoundError as e:
        raise _not_found(e)
    return {"deleted": True}
