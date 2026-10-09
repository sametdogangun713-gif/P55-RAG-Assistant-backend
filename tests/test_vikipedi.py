"""3. parti API (Vikipedi) entegrasyonunun testleri.

Gercek Vikipedi'ye GIDILMEZ: yerelde calisan sahte bir HTTP sunucusu MediaWiki Action API'nin yanitlarini taklit
eder. Boylece testler internetsiz calisir; istegin bicimi (parametreler, User-Agent) yine de dogrulanir.
"""
import json
import os
import shutil
import tempfile
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app.core import config
from app.db import documents as documents_repo
from app.services import auth, vector_search, wikipedia
from app.services import documents as docs_svc
from tests.helpers import TempUploads, make_conn, make_user

try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None

PAROLA = "Guclu1234"
MAKALE = ("Fotosentez, yeşil bitkilerin ışık enerjisini kullanarak karbondioksit ve sudan glikoz ve oksijen "
          "üretmesidir.\n\nEvreler\nIşığa bağımlı tepkimeler kloroplastın tilakoit zarında gerçekleşir.")


class SahteVikipedi:
    """Gelen istekleri kaydeder; yanitlari self.yanit(params) fonksiyonu uretir: (durum, govde)."""

    def __init__(self):
        self.istekler = []
        self.yanit = self.varsayilan
        dis = self

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                yol, _, sorgu = self.path.partition("?")
                params = dict(urllib.parse.parse_qsl(sorgu))
                dis.istekler.append({"yol": yol, "params": params, "ua": self.headers.get("User-Agent", "")})
                durum, govde = dis.yanit(params)
                veri = govde if isinstance(govde, bytes) else json.dumps(govde).encode()
                self.send_response(durum)
                self.send_header("Content-Length", str(len(veri)))
                self.end_headers()
                self.wfile.write(veri)

            def log_message(self, *a):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/{{lang}}/w/api.php"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    @staticmethod
    def varsayilan(params):
        if params.get("list") == "search":
            return 200, {"query": {"search": [
                {"ns": 0, "title": "Fotosentez", "pageid": 1,
                 "snippet": "<span class=\"searchmatch\">Fotosentez</span>, bitkilerin &quot;ışık&quot; enerjisi"},
                {"ns": 0, "title": "Kloroplast", "pageid": 2, "snippet": "hücre organeli"}]}}
        if params.get("prop") == "extracts":
            if params.get("titles") == "Yok Böyle Bir Sayfa":
                return 200, {"query": {"pages": [{"ns": 0, "title": "Yok Böyle Bir Sayfa", "missing": True}]}}
            return 200, {"query": {"pages": [{"pageid": 1, "ns": 0, "title": "Fotosentez", "extract": MAKALE}]}}
        return 500, {"error": "beklenmeyen istek"}

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class VikipediTabanli(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sunucu = SahteVikipedi()

    @classmethod
    def tearDownClass(cls):
        cls.sunucu.close()

    def setUp(self):
        self._eski = (config.WIKIPEDIA_API_URL, config.WIKIPEDIA_TIMEOUT_SECONDS)
        config.WIKIPEDIA_API_URL = self.sunucu.url
        config.WIKIPEDIA_TIMEOUT_SECONDS = 5
        self.sunucu.istekler.clear()
        self.sunucu.yanit = SahteVikipedi.varsayilan

    def tearDown(self):
        config.WIKIPEDIA_API_URL, config.WIKIPEDIA_TIMEOUT_SECONDS = self._eski


class VikipediIstemciTests(VikipediTabanli):
    def test_arama_sonuclari_ve_istek_bicimi(self):
        sonuc = wikipedia.search("tr", "fotosentez", limit=3)
        self.assertEqual([s["title"] for s in sonuc], ["Fotosentez", "Kloroplast"])
        self.assertEqual(sonuc[0]["snippet"], 'Fotosentez, bitkilerin "ışık" enerjisi')   # HTML temizlendi
        istek = self.sunucu.istekler[0]
        self.assertEqual(istek["yol"], "/tr/w/api.php")
        self.assertEqual(istek["params"]["srsearch"], "fotosentez")
        self.assertEqual(istek["params"]["srlimit"], "3")
        self.assertEqual(istek["params"]["format"], "json")
        self.assertIn("BelgeTabanliSoruAsistani", istek["ua"])          # Wikimedia kurali: tanitici User-Agent

    def test_makale_duz_metin_ve_adres(self):
        m = wikipedia.fetch_article("tr", "fotosentez")
        self.assertEqual(m["title"], "Fotosentez")                       # yonlendirme sonrasi asil baslik
        self.assertEqual(m["url"], "https://tr.wikipedia.org/wiki/Fotosentez")
        self.assertIn("kloroplastın", m["text"])
        params = self.sunucu.istekler[0]["params"]
        self.assertEqual((params["explaintext"], params["redirects"]), ("1", "1"))
        metin = wikipedia.as_document_text(m)
        self.assertTrue(metin.startswith("Fotosentez\nKaynak: Vikipedi, https://tr.wikipedia.org/wiki/Fotosentez"))
        self.assertIn("CC BY-SA", metin)

    def test_olmayan_makale(self):
        with self.assertRaises(wikipedia.WikipediaNotFoundError):
            wikipedia.fetch_article("tr", "Yok Böyle Bir Sayfa")

    def test_gecersiz_girdiler_istek_atmadan_reddedilir(self):
        for dil, sorgu in (("de", "x"), ("tr", ""), ("tr", "   "), ("tr", "a" * 201)):
            with self.assertRaises(wikipedia.WikipediaInputError):
                wikipedia.search(dil, sorgu)
        with self.assertRaises(wikipedia.WikipediaInputError):
            wikipedia.fetch_article("tr", "")
        self.assertEqual(self.sunucu.istekler, [])

    def test_sunucu_hatasi_ve_bozuk_yanit(self):
        self.sunucu.yanit = lambda p: (503, {"error": "bakim"})
        with self.assertRaises(wikipedia.WikipediaError) as cm:
            wikipedia.search("tr", "x")
        self.assertIn("503", str(cm.exception))
        self.sunucu.yanit = lambda p: (200, b"<html>json degil</html>")
        with self.assertRaises(wikipedia.WikipediaError):
            wikipedia.search("tr", "x")
        self.sunucu.yanit = lambda p: (200, {"error": {"code": "badvalue", "info": "Unrecognized value"}})
        with self.assertRaisesRegex(wikipedia.WikipediaError, "Unrecognized value"):
            wikipedia.search("tr", "x")

    def test_ulasilamayan_sunucu(self):
        config.WIKIPEDIA_API_URL = "http://127.0.0.1:9/{lang}/w/api.php"     # 9 = discard portu, dinleyen yok
        with self.assertRaisesRegex(wikipedia.WikipediaError, "ulaşılamadı"):
            wikipedia.search("tr", "x")


class MetinBelgesiTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        self.user = make_user(self.conn)

    def test_metin_belge_olur_aranabilir_dosya_kalmaz(self):
        with TempUploads() as klasor:
            doc = docs_svc.import_text_document(self.conn, self.user, "Vikipedi - Fotosentez.txt", MAKALE)
            self.assertEqual(os.listdir(klasor), [])                     # gecici dosya silindi
        self.assertEqual(doc["status"], "indexed")
        self.assertIsNone(documents_repo.get_document(self.conn, doc["id"])["stored_name"])
        sonuc = vector_search.search(self.conn, self.user["id"], "tilakoit zarı")
        self.assertEqual(sonuc[0]["filename"], "Vikipedi - Fotosentez.txt")
        docs_svc.delete_document(self.conn, self.user, doc["id"])        # silinecek dosya yok; hata vermemeli

    def test_bos_ve_yanlis_uzanti_reddedilir(self):
        with TempUploads():
            with self.assertRaises(docs_svc.DocumentValidationError):
                docs_svc.import_text_document(self.conn, self.user, "a.txt", "   ")
            with self.assertRaises(docs_svc.DocumentValidationError):
                docs_svc.import_text_document(self.conn, self.user, "a.pdf", "metin")


@unittest.skipIf(TestClient is None, "TestClient (httpx) kurulu degil")
class VikipediHttpTests(VikipediTabanli):
    def test_ara_ve_belge_olarak_ekle(self):
        from app.main import app
        tmp = tempfile.mkdtemp()
        eski_url, eski_up = config.DATABASE_URL, config.UPLOAD_DIR
        config.DATABASE_URL = "sqlite:///" + os.path.join(tmp, "test.db")
        config.UPLOAD_DIR = os.path.join(tmp, "uploads")
        try:
            auth.reset_failed_attempts()
            with TestClient(app) as client:
                self.assertEqual(client.get("/wikipedia/search", params={"q": "x"}).status_code, 401)
                client.post("/auth/register", json={"full_name": "Viki Deneme", "email": "viki@example.com",
                                                     "password": PAROLA})
                r = client.post("/auth/login", json={"email": "viki@example.com", "password": PAROLA})
                h = {"Authorization": "Bearer " + r.json()["access_token"]}

                r = client.get("/wikipedia/search", params={"q": "fotosentez", "lang": "tr"}, headers=h)
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.json()["results"][0]["title"], "Fotosentez")
                self.assertEqual(client.get("/wikipedia/search", params={"q": "x", "lang": "de"},
                                            headers=h).status_code, 400)

                r = client.post("/wikipedia/import", json={"title": "Fotosentez", "lang": "tr"}, headers=h)
                self.assertEqual(r.status_code, 201)
                belge = r.json()
                self.assertEqual(belge["filename"], "Vikipedi - Fotosentez.txt")
                self.assertEqual(belge["status"], "indexed")
                self.assertEqual(belge["source_url"], "https://tr.wikipedia.org/wiki/Fotosentez")
                self.assertNotIn("stored_name", belge)
                self.assertEqual([d["id"] for d in client.get("/documents", headers=h).json()], [belge["id"]])

                r = client.post("/wikipedia/import", json={"title": "Yok Böyle Bir Sayfa"}, headers=h)
                self.assertEqual(r.status_code, 404)
                self.sunucu.yanit = lambda p: (503, {"error": "bakim"})
                r = client.post("/wikipedia/import", json={"title": "Fotosentez"}, headers=h)
                self.assertEqual(r.status_code, 502)                     # dis servis hatasi
        finally:
            config.DATABASE_URL, config.UPLOAD_DIR = eski_url, eski_up
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
