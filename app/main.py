"""Backend (API) giris noktasi. Arayuz ayri bir depoda (P55-RAG-Assistant-frontend) ve ayri bir adreste calisir."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import admin, ask, auth, conversations, documents, reports, search
from app.core import config
from app.db import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama acilirken: veritabani migration'lari ve yukleme klasoru hazirlanir."""
    config.check_secret_key()
    database.init_db()
    Path(config.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Belge Tabanlı Soru Asistanı (RAG)", version="0.18.2", lifespan=lifespan)
MULTIPART_OVERHEAD = 1024 * 1024     # form sinirlari ve basliklar icin pay (dosyanin kendisi degil)


@app.middleware("http")
async def upload_size_guard(request: Request, call_next):
    """Siniri asan yuklemeyi GOVDESI OKUNMADAN reddeder.

    Aksi halde sunucu (ev bilgisayari) 5 GB'lik bir istegi once gecici diske yazar, sonra reddederdi.
    Content-Length gondermeyen istemciler icin asil kontrol yine services/documents.py'de yapilir.
    """
    if request.method == "POST" and request.url.path.rstrip("/") == "/documents":
        length = request.headers.get("content-length", "")
        if length.isdigit() and int(length) > config.MAX_UPLOAD_MB * 1024 * 1024 + MULTIPART_OVERHEAD:
            return JSONResponse({"detail": f"Dosya {config.MAX_UPLOAD_MB} MB sınırını aşıyor"}, status_code=413)
    return await call_next(request)


# CORS: arayuz baska bir adreste (orn. p55-rag-assistant-frontend.vercel.app) oldugu icin tarayici, backend'e istek atmadan
# once "bu adrese izin veriyor musun?" diye sorar. Yalnizca ALLOWED_ORIGINS'teki adreslere izin verilir.
# Cerez kullanilmiyor (token Authorization basliginda), bu yuzden allow_credentials gerekmez.
# Bu ara katman size_guard'dan SONRA eklendigi icin en distadir: 413 yanitina da CORS basliklari eklenir.
app.add_middleware(CORSMiddleware, allow_origins=config.ALLOWED_ORIGINS,
                   allow_methods=["GET", "POST", "PATCH", "DELETE"],
                   allow_headers=["Authorization", "Content-Type"])

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(ask.router)
app.include_router(conversations.router)
app.include_router(reports.router)

@app.get("/health")
def health():
    """Iskelet calisiyor mu? Hafta 3 demosunda gosterilecek uc nokta.
    'database' hangi veritabaninin kullanildigini soyler (adres/parola DEGIL): Vercel'deki surumun Supabase'e
    mi (postgres) yoksa yanlislikla gecici bir SQLite dosyasina mi bagli oldugu buradan anlasilir."""
    return {"status": "ok", "database": "postgres" if config.is_postgres() else "sqlite"}


@app.get("/", include_in_schema=False)
def index():
    """Backend'in kendi arayuzu yok; adresi tarayicida acan kisiye ne oldugunu soyler."""
    return {"name": "Belge Tabanli Soru Asistani API", "docs": "/docs", "health": "/health"}
