"""Hafta 8 (vize) testleri: modullerin uctan uca birlikte calismasi."""
import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.api import admin as admin_api
from app.api import auth as auth_api
from app.api import deps
from app.api import documents as docs_api
from app.api import search as search_api
from app.core import config
from app.db import database
from app.services import auth
from tests.helpers import TempUploads, make_conn

ROOT = Path(__file__).resolve().parents[1]
PAROLA = "Guclu1234"
VEKTOR_DB = ("Vektor veritabani metinlerin sayisal vektor temsillerini saklar. Benzerlik arama soru vektorune "
             "en yakin vektorleri kosinus benzerligi ile bulur.")
YEMEK = "Makarna tarifi icin once suyu kaynatin. Makarnayi tuzlu suda haslayin ve domates sosuyla servis edin."


def giris(conn, email, role="user"):
    auth.register_user(conn, email, PAROLA, role=role)
    token = auth_api.login(auth_api.Credentials(email=email, password=PAROLA), conn)["access_token"]
    return deps.get_current_user(authorization="Bearer " + token, conn=conn)


def dosya(ad, metin):
    return UploadFile(file=io.BytesIO(metin.encode("utf-8")), filename=ad)


class UctanUcaAkisTests(unittest.TestCase):
    """Kayit -> giris -> belge yukle -> ara -> yetki -> sil: tum katmanlar birlikte."""

    def setUp(self):
        auth.reset_failed_attempts()
        self.conn = make_conn()
        self._tmp = TempUploads()
        self._tmp.__enter__()

    def tearDown(self):
        self._tmp.__exit__()

    def test_tam_senaryo(self):
        ali = giris(self.conn, "ali@example.com")
        veli = giris(self.conn, "veli@example.com")
        yon = giris(self.conn, "yonetici@example.com", role="admin")

        # Ali iki belge yukler; ikisi de indekslenir
        d1 = docs_api.upload(dosya("vektor.txt", VEKTOR_DB), ali, self.conn)
        d2 = docs_api.upload(dosya("yemek.txt", YEMEK), ali, self.conn)
        self.assertEqual((d1["status"], d2["status"]), ("indexed", "indexed"))
        self.assertEqual(len(docs_api.list_documents(ali, self.conn)), 2)

        # Arama dogru belgeyi getirir
        sonuc = search_api.search_documents(search_api.SearchRequest(query="benzerlik arama"), ali, self.conn)
        self.assertEqual(sonuc["results"][0]["filename"], "vektor.txt")

        # Veli Ali'nin verisini goremez
        self.assertEqual(docs_api.list_documents(veli, self.conn), [])
        self.assertEqual(search_api.search_documents(
            search_api.SearchRequest(query="benzerlik arama"), veli, self.conn)["results"], [])
        with self.assertRaises(HTTPException) as e:
            docs_api.get_document(d1["id"], veli, self.conn)
        self.assertEqual(e.exception.status_code, 404)

        # Yonetici kullanici listesini gorur, normal kullanici goremez
        self.assertEqual(len(admin_api.list_all_users(yon, self.conn)), 3)
        with self.assertRaises(HTTPException) as e:
            deps.require_admin(ali)
        self.assertEqual(e.exception.status_code, 403)

        # Silince arama sonucundan da kaybolur
        docs_api.delete_document(d1["id"], ali, self.conn)
        sonuc = search_api.search_documents(search_api.SearchRequest(query="benzerlik arama"), ali, self.conn)
        self.assertNotIn("vektor.txt", [r["filename"] for r in sonuc["results"]])

    def test_kullanici_silinince_belge_ve_dosyalari_temizlenir(self):
        from app.db import users
        ali = giris(self.conn, "ali@example.com")
        docs_api.upload(dosya("a.txt", VEKTOR_DB), ali, self.conn)
        users.delete_user(self.conn, ali["id"])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0], 0)


try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None


@unittest.skipIf(TestClient is None, "TestClient (httpx) kurulu degil")
class HttpDumanTesti(unittest.TestCase):
    """Gercek HTTP katmaniyla kisa duman testi (fastapi + httpx kuruluysa calisir)."""

    def test_http_akisi(self):
        from app.main import app
        tmp = tempfile.mkdtemp()
        eski_url, eski_up = config.DATABASE_URL, config.UPLOAD_DIR
        config.DATABASE_URL = "sqlite:///" + os.path.join(tmp, "test.db")
        config.UPLOAD_DIR = os.path.join(tmp, "uploads")
        try:
            auth.reset_failed_attempts()
            with TestClient(app) as client:
                self.assertEqual(client.get("/").status_code, 200)
                self.assertEqual(client.get("/documents").status_code, 401)
                r = client.post("/auth/register", json={"email": "a@example.com", "password": PAROLA})
                self.assertEqual(r.status_code, 201)
                r = client.post("/auth/login", json={"email": "a@example.com", "password": PAROLA})
                h = {"Authorization": "Bearer " + r.json()["access_token"]}
                self.assertEqual(client.get("/auth/me", headers=h).json()["email"], "a@example.com")
                r = client.post("/documents", headers=h, files={"file": ("not.txt", VEKTOR_DB.encode(), "text/plain")})
                self.assertEqual(r.status_code, 201)
                self.assertEqual(r.json()["status"], "indexed")
                r = client.post("/search", headers=h, json={"query": "benzerlik arama"})
                self.assertEqual(r.json()["results"][0]["filename"], "not.txt")
                self.assertEqual(client.get("/admin/users", headers=h).status_code, 403)
        finally:
            config.DATABASE_URL, config.UPLOAD_DIR = eski_url, eski_up
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
