"""Hafta 14: buyuk dosya yukleme (500 MB) - diske akitarak kaydetme, parca siniri, erken 413, arayuz siniri."""
import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from app.api import documents as docs_api
from app.core import config
from app.db import chunks as chunks_repo
from app.db import documents as documents_repo
from app.services import auth
from app.services import documents as svc
from tests.helpers import TempUploads, make_conn, make_user

try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None

MB = 1024 * 1024
KOK = Path(__file__).resolve().parents[1]
METIN = " ".join(f"Bu {i}. cumle buyuk dosya testleri icin yazilmis ornek bir icerik tasir." for i in range(80))


class KaydedenAkis(io.BytesIO):
    """Her read(n) cagrisinda istenen miktari kaydeder: 'dosyanin tamami tek seferde okunmadi mi?' sorusu icin."""

    def __init__(self, data):
        super().__init__(data)
        self.istenen = []

    def read(self, n=-1):
        self.istenen.append(n)
        return super().read(n)


class Ayar:
    """config degerini gecici olarak degistirir (with blogu)."""

    def __init__(self, **degerler):
        self.degerler = degerler

    def __enter__(self):
        self.eski = {k: getattr(config, k) for k in self.degerler}
        for k, v in self.degerler.items():
            setattr(config, k, v)

    def __exit__(self, *exc):
        for k, v in self.eski.items():
            setattr(config, k, v)


class AkisliKayitTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        self.u = make_user(self.conn, "buyuk@example.com")
        self._tmp = TempUploads()
        self.dir = self._tmp.__enter__()

    def tearDown(self):
        self._tmp.__exit__(None, None, None)
        self.conn.close()

    def test_dosya_parca_parca_okunur_ve_aynen_yazilir(self):
        data = b"Merhaba. " + b" " * (3 * MB)                       # ~3 MB, metni az (hizli)
        akis = KaydedenAkis(data)
        doc = svc.upload_document_stream(self.conn, self.u, "buyuk.txt", akis)
        self.assertEqual(doc["size_bytes"], len(data))
        self.assertTrue(all(0 < n <= svc.COPY_BLOCK for n in akis.istenen), akis.istenen)  # hic read() / read(-1) yok
        kayitli = Path(self.dir) / documents_repo.get_document(self.conn, doc["id"])["stored_name"]
        self.assertEqual(kayitli.read_bytes(), data)

    def test_sinir_asilirsa_yarim_dosya_silinir(self):
        with Ayar(MAX_UPLOAD_MB=1):
            with self.assertRaises(svc.FileTooLargeError):
                svc.upload_document_stream(self.conn, self.u, "b.txt", io.BytesIO(b"a" * (MB + 1)))
            svc.upload_document_stream(self.conn, self.u, "tam.txt", io.BytesIO(b"a" * MB))   # tam sinir: kabul
        self.assertEqual(len(os.listdir(self.dir)), 1)                # yalnizca kabul edilen dosya
        self.assertEqual(len(documents_repo.list_documents(self.conn)), 1)

    def test_tur_ve_bos_kontrolu_diske_yazmadan_yapilir(self):
        with self.assertRaises(svc.DocumentValidationError):
            svc.upload_document_stream(self.conn, self.u, "bos.txt", io.BytesIO(b""))
        with self.assertRaises(svc.DocumentValidationError):
            svc.upload_document_stream(self.conn, self.u, "sahte.pdf", io.BytesIO(b"bu pdf degil" * 1000))
        self.assertEqual(os.listdir(self.dir), [])

    def test_cok_fazla_metin_anlasilir_hatayla_reddedilir(self):
        with Ayar(MAX_CHUNKS_PER_DOCUMENT=3):
            doc = svc.upload_document(self.conn, self.u, "uzun.txt", METIN.encode())
        self.assertEqual(doc["status"], "failed")
        self.assertIn("çok fazla metin", doc["error"])
        self.assertEqual(chunks_repo.count_chunks(self.conn, doc["id"]), 0)   # yarim indeks birakilmaz
        svc.delete_document(self.conn, self.u, doc["id"])                     # kullanici silebilir
        self.assertEqual(os.listdir(self.dir), [])

    def test_sinir_icindeki_metin_normal_islenir(self):
        doc = svc.upload_document(self.conn, self.u, "uzun.txt", METIN.encode())
        self.assertEqual(doc["status"], "indexed")
        self.assertLessEqual(chunks_repo.count_chunks(self.conn, doc["id"]), config.MAX_CHUNKS_PER_DOCUMENT)

    def test_limits_ucu(self):
        with Ayar(MAX_UPLOAD_MB=500, MAX_CHUNKS_PER_DOCUMENT=20000):
            out = docs_api.upload_limits(self.u)
        self.assertEqual(out["max_upload_mb"], 500)
        self.assertEqual(out["max_chunks_per_document"], 20000)
        self.assertIn(".pdf", out["allowed_extensions"])


@unittest.skipIf(TestClient is None, "TestClient (httpx) kurulu degil")
class ErkenReddetmeHttpTests(unittest.TestCase):
    """Gercek HTTP katmani: sinirin ustundeki istek govdesi islenmeden, kimlik kontrolunden bile once 413 alir."""

    def test_content_length_ile_erken_413_ve_limits_rotasi(self):
        from app.main import app
        tmp = tempfile.mkdtemp()
        eski_url, eski_up = config.DATABASE_URL, config.UPLOAD_DIR
        config.DATABASE_URL = "sqlite:///" + os.path.join(tmp, "test.db")
        config.UPLOAD_DIR = os.path.join(tmp, "uploads")
        try:
            auth.reset_failed_attempts()
            with TestClient(app) as client, Ayar(MAX_UPLOAD_MB=0):     # sinir = 0 MB + 1 MB form payi
                buyuk = {"file": ("b.txt", b"a" * (2 * MB), "text/plain")}
                r = client.post("/documents", files=buyuk)
                self.assertEqual(r.status_code, 413)                     # token yok ama 401 degil: erken reddedildi
                self.assertIn("MB sınırını aşıyor", r.json()["detail"])
                r = client.post("/documents", files={"file": ("k.txt", b"kucuk", "text/plain")})
                self.assertEqual(r.status_code, 401)                     # kucuk istek normal yoldan gecer

                client.post("/auth/register", json={"full_name": "Deneme Kullanıcı", "email": "l@example.com", "password": "Guclu1234"})
                tok = client.post("/auth/login", json={"email": "l@example.com", "password": "Guclu1234"}).json()
                h = {"Authorization": "Bearer " + tok["access_token"]}
                r = client.get("/documents/limits", headers=h)          # '/{doc_id}' rotasina takilmamali
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.json()["max_upload_mb"], 0)
        finally:
            config.DATABASE_URL, config.UPLOAD_DIR = eski_url, eski_up
            shutil.rmtree(tmp, ignore_errors=True)


class AyarTests(unittest.TestCase):
    def test_env_example_500_mb(self):
        env = (KOK / ".env.example").read_text(encoding="utf-8")
        self.assertIn("MAX_UPLOAD_MB=500\n", env)
        self.assertIn("MAX_CHUNKS_PER_DOCUMENT=", env)


if __name__ == "__main__":
    unittest.main()
