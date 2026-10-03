"""Servis hatalarini HTTP hatalarina cevirir."""
from fastapi import HTTPException

from app.services.llm_client import (LLMConfigError, LLMError, LLMRateLimitError, LLMTimeoutError)


def llm_http_error(e: LLMError) -> HTTPException:
    if isinstance(e, LLMConfigError):
        return HTTPException(status_code=503, detail=str(e))
    if isinstance(e, LLMTimeoutError):
        return HTTPException(status_code=504, detail=str(e))
    if isinstance(e, LLMRateLimitError):
        return HTTPException(status_code=429, detail=str(e))
    return HTTPException(status_code=502, detail=str(e))
