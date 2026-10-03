"""Testlerde ortak kullanilan yardimcilar (gercek kisisel veri YOK, hepsi sentetik).

Varsayilan: her test bellekte temiz bir SQLite veritabani kullanir (kurulum gerektirmez).
P55_TEST_PG_URL ortam degiskeni verilirse ayni testler PostgreSQL'e karsi kosar (Supabase'e giden kodu
dogrulamak icin). Her make_conn() cagrisi kendi semasini (schema) acar; testler birbirini etkilemez.
Ornek:  set P55_TEST_PG_URL=postgresql://postgres@localhost:55432/postgres  &&  pytest
"""
import os
import shutil
import tempfile
import uuid

from app.core import config
from app.db import database, users

PG_URL = os.getenv("P55_TEST_PG_URL", "")
_pg_ready = False


def _make_pg_conn():
    global _pg_ready
    import psycopg
    if not _pg_ready:
        with psycopg.connect(PG_URL, autocommit=True) as c:      # vector tipi her test semasindan gorunsun
            c.execute("CREATE EXTENSION IF NOT EXISTS vector SCHEMA public")
        _pg_ready = True
    raw = psycopg.connect(PG_URL)
    schema = "test_" + uuid.uuid4().hex[:12]
    raw.execute(f"CREATE SCHEMA {schema}")
    raw.execute(f"SET search_path TO {schema}, public")
    raw.commit()
    conn = database.PgConnection(raw)
    database.run_migrations(conn)
    return conn


def make_conn():
    """Migration'lari uygulanmis temiz bir veritabani (SQLite bellekte; ya da PostgreSQL'de yeni sema)."""
    if PG_URL:
        return _make_pg_conn()
    conn = database.get_connection(":memory:")
    database.run_migrations(conn)
    return conn


def make_user(conn, email="ogrenci@example.com", role="user", password_hash="x"):
    return users.create_user(conn, email, password_hash, role)


class TempUploads:
    """UPLOAD_DIR'i gecici bir klasore yonlendirir (with blogu ile kullanilir)."""

    def __enter__(self):
        self.dir = tempfile.mkdtemp(prefix="p55_uploads_")
        self._old = config.UPLOAD_DIR
        config.UPLOAD_DIR = self.dir
        return self.dir

    def __exit__(self, *exc):
        config.UPLOAD_DIR = self._old
        shutil.rmtree(self.dir, ignore_errors=True)


class ScriptedLLM:
    """Testlerde kullanilan sahte LLM: sirayla onceden belirlenmis yanitlari verir ve cagrilari kaydeder.

    Bir yanit Exception ise firlatilir.
    """
    model = "sahte"

    def __init__(self, *yanitlar):
        self.yanitlar = list(yanitlar)
        self.cagrilar = []

    def complete(self, system, messages, max_tokens=None):
        self.cagrilar.append({"system": system, "messages": messages, "max_tokens": max_tokens})
        if not self.yanitlar:
            raise AssertionError("Beklenenden fazla LLM cagrisi")
        y = self.yanitlar.pop(0)
        if isinstance(y, Exception):
            raise y
        return y
