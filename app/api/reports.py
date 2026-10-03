from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.api.deps import get_current_user, get_db
from app.services import report_pdf, reports

router = APIRouter(prefix="/reports", tags=["reports"])


def _build(conn, user, days, scope):
    if scope not in ("me", "all"):
        raise HTTPException(status_code=400, detail="scope 'me' veya 'all' olmalı")
    if scope == "all" and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Tüm sistem raporu için yönetici yetkisi gerekli")
    try:
        return reports.usage_report(conn, None if scope == "all" else user["id"], days)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/usage")
def usage(days: int = Query(default=30, ge=1, le=365), scope: str = Query(default="me"),
          user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Kullanim ve kaynak raporu. scope=me: kendi verin; scope=all: tum sistem (yonetici)."""
    return _build(conn, user, days, scope)


@router.get("/usage.csv")
def usage_csv(days: int = Query(default=30, ge=1, le=365), scope: str = Query(default="me"),
              user: dict = Depends(get_current_user), conn=Depends(get_db)):
    text = reports.report_to_csv(_build(conn, user, days, scope))
    return Response(content=text.encode("utf-8"), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="kullanim-raporu.csv"'})


@router.get("/usage.pdf")
def usage_pdf(days: int = Query(default=30, ge=1, le=365), scope: str = Query(default="me"),
              user: dict = Depends(get_current_user), conn=Depends(get_db)):
    """Ayni raporun PDF hali (arayuzdeki "PDF indir"). Excel ayarindan bagimsiz, her yerde ayni gorunur."""
    pdf = report_pdf.report_to_pdf(_build(conn, user, days, scope), owner=user.get("email", ""))
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="kullanim-raporu.pdf"'})
