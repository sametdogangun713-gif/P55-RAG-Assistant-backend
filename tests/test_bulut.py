"""Bulut (Supabase + Vercel) icin eklenen kodun testleri.

Gercek Supabase / Hugging Face'e GIDILMEZ: her ikisi de yerelde calisan sahte bir HTTP sunucusuyla taklit edilir.
Boylece testler internetsiz ve anahtarsiz calisir; istegin bicimi (adres, baslik, govde) yine de dogrulanir.
PostgreSQL'e ozel kisim (pgvector aramasi) yalnizca P55_TEST_PG_URL verilince kosar.
"""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

from app.core import config
from app.db import database
from app.services import documents as svc
from app.services.embedder import EmbeddingError, HashingEmbedder, HFEmbedder
from tests.helpers import TempUploads, make_conn, make_user


class SahteBulut:
    """Hugging Face ve Supabase Storage'in sahtesi. Gelen istekleri kaydeder, yanitlari self.yanitlar'dan verir.

    yanitlar: {(yontem, yol_baslangici): [(durum, govde_bayt_ya_da_dict), ...]}  (sirayla tuketilir)
    """

    def __init__(self):
        self.istekler = []
        self.yanitlar = {}
        self.dosyalar = {}                     # sahte depo: yol -> bayt
        dis = self

        class H(BaseHTTPRequestHandler):
            def _isle(self, yontem):
                n = int(self.headers.get("Content-Length", 0) or 0)
                govde = self.rfile.read(n) if n else b""
                dis.istekler.append({"yontem": yontem, "yol": self.path, "basliklar": {k.lower(): v for k, v in self.headers.items()},
                                     "govde": govde})
                durum, cevap = dis._cevap(yontem, self.path)
                veri = cevap if isinstance(cevap, bytes) else json.dumps(cevap).encode()
                self.send_response(durum)
                self.send_header("Content-Length", str(len(veri)))
                self.end_headers()
                self.wfile.write(veri)

            def do_GET(self):
                self._isle("GET")

            def do_POST(self):
                self._isle("POST")

            def do_DELETE(self):
                self._isle("DELETE")

            def log_message(self, *a):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def _cevap(self, yontem, yol):
        for (y, bas), sira in self.yanitlar.items():
            if y == yontem and yol.startswith(bas) and sira:
                return sira.pop(0)
        if yontem == "GET" and "/storage/v1/object/" in yol:            # sahte depodan dosya indir
            ad = yol.split(f"/object/{config.SUPABASE_BUCKET}/", 1)[1]
            return (200, self.dosyalar[ad]) if ad in self.dosyalar else (404, {"error": "not found"})
        if yontem == "POST" and "/object/upload/sign/" in yol:          # imzali yukleme adresi
            return 200, {"url": yol.split("/storage/v1", 1)[1] + "?token=sahte-token"}
        if yontem == "DELETE":
            return 200, []
        return 500, {"error": "beklenmeyen istek"}

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


# ---------------------------------------------------------------- Hugging Face
class HFEmbedderTests(unittest.TestCase):
    def setUp(self):
        self.s = SahteBulut()
        self.beklemeler = []
        self.emb = HFEmbedder(model_name="paraphrase-multilingual-MiniLM-L12-v2", token="hf_sahte_anahtar",
                              base_url=self.s.url, timeout=5, sleep=self.beklemeler.append)

    def tearDown(self):
        self.s.close()

    def test_istek_bicimi_ve_normalizasyon(self):
        yol = "/models/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2/pipeline/feature-extraction"
        self.s.yanitlar[("POST", yol)] = [(200, [[3.0, 4.0], [0.0, 2.0]])]
        m = self.emb.embed_documents(["bir", "iki"])
        istek = self.s.istekler[0]
        self.assertEqual(istek["yol"], yol)
        self.assertEqual(istek["basliklar"]["authorization"], "Bearer hf_sahte_anahtar")
        self.assertEqual(json.loads(istek["govde"]), {"inputs": ["bir", "iki"], "normalize": True, "truncate": True})
        np.testing.assert_allclose(m, [[0.6, 0.8], [0.0, 1.0]], rtol=1e-6)     # birim uzunluga getirildi
        self.assertEqual(self.emb.name, "hf:paraphrase-multilingual-MiniLM-L12-v2")

    def test_model_yukleniyorsa_yeniden_dener(self):
        self.s.yanitlar[("POST", "/models/")] = [(503, {"error": "Model is loading"}), (200, [[1.0, 0.0]])]
        m = self.emb.embed_documents(["x"])
        self.assertEqual(len(self.s.istekler), 2)
        self.assertEqual(self.beklemeler, [1])
        self.assertEqual(m.shape, (1, 2))

    def test_yetkisiz_anahtar_anlasilir_hata_ve_anahtar_sizmaz(self):
        self.s.yanitlar[("POST", "/models/")] = [(401, {"error": "Invalid token"})]
        with self.assertRaises(EmbeddingError) as ctx:
            self.emb.embed_documents(["x"])
        self.assertIn("HF_TOKEN", str(ctx.exception))
        self.assertNotIn("hf_sahte_anahtar", str(ctx.exception))
        self.assertEqual(len(self.s.istekler), 1)                       # 401 yeniden denenmez

    def test_anahtar_yoksa_istek_atilmaz(self):
        emb = HFEmbedder(token="", base_url=self.s.url)
        with self.assertRaises(EmbeddingError):
            emb.embed_documents(["x"])
        self.assertEqual(self.s.istekler, [])

    def test_beklenmeyen_yanit_bicimi(self):
        self.s.yanitlar[("POST", "/models/")] = [(200, {"error": "?"}), (200, [[1.0, 0.0]])]
        with self.assertRaises(EmbeddingError):
            self.emb.embed_documents(["x"])                              # sozluk: vektor listesi degil
        with self.assertRaises(EmbeddingError):
            self.emb.embed_documents(["x", "y"])                         # 2 metne 1 vektor


# ---------------------------------------------------------------- Supabase Storage
class StorageTests(unittest.TestCase):
    def setUp(self):
        self.s = SahteBulut()
        self.eski = (config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY, config.STORAGE_BACKEND, config.MAX_UPLOAD_MB)
        config.SUPABASE_URL = self.s.url
        config.SUPABASE_SERVICE_ROLE_KEY = "sahte-service-role"
        config.STORAGE_BACKEND = "supabase"
        config.MAX_UPLOAD_MB = 1
        self.conn = make_conn()
        self.u = make_user(self.conn, "depo@example.com")
        self.uploads = TempUploads()
        self.uploads.__enter__()
        self.emb = HashingEmbedder()

    def tearDown(self):
        self.uploads.__exit__(None, None, None)
        (config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY, config.STORAGE_BACKEND, config.MAX_UPLOAD_MB) = self.eski
        self.s.close()

    def test_yukleme_adresi_kullanicinin_klasorunde_ve_imzali(self):
        r = svc.prepare_storage_upload(self.u, "Notlar.pdf", 1000)
        self.assertRegex(r["path"], rf"^{self.u['id']}/[0-9a-f]{{32}}\.pdf$")
        self.assertTrue(r["upload_url"].startswith(self.s.url + "/storage/v1/object/upload/sign/belgeler/"))
        self.assertIn("token=", r["upload_url"])
        basliklar = self.s.istekler[0]["basliklar"]
        self.assertEqual(basliklar["apikey"], "sahte-service-role")      # yeni anahtar: yalnizca apikey
        self.assertNotIn("authorization", basliklar)

    def test_eski_jwt_anahtari_bearer_olarak_da_gider(self):
        config.SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiJ9.sahte.imza"
        svc.prepare_storage_upload(self.u, "a.txt", 10)
        self.assertEqual(self.s.istekler[0]["basliklar"]["authorization"], "Bearer eyJhbGciOiJIUzI1NiJ9.sahte.imza")

    def test_hazirlikta_boyut_ve_tur_denetlenir_depoya_gidilmez(self):
        with self.assertRaises(svc.FileTooLargeError):
            svc.prepare_storage_upload(self.u, "a.txt", 2 * 1024 * 1024)
        with self.assertRaises(svc.DocumentValidationError):
            svc.prepare_storage_upload(self.u, "a.exe", 10)
        with self.assertRaises(svc.DocumentValidationError):
            svc.prepare_storage_upload(self.u, "a.txt", 0)
        self.assertEqual(self.s.istekler, [])

    def test_tamamlama_dosyayi_depodan_okur_ve_indeksler(self):
        yol = f"{self.u['id']}/{'a' * 32}.txt"
        self.s.dosyalar[yol] = "Vektör veritabanı benzer metinleri bulur.".encode("utf-8")
        doc = svc.complete_storage_upload(self.conn, self.u, yol, "notlar.txt", "text/plain", embedder=self.emb)
        self.assertEqual(doc["status"], "indexed")
        self.assertEqual(doc["stored_name"], yol)                       # asil dosya depoda kalir
        self.assertEqual(doc["filename"], "notlar.txt")
        import os
        self.assertEqual(os.listdir(self.uploads.dir), [])              # gecici kopya silindi

    def test_baskasinin_yolu_ve_bozuk_yol_reddedilir(self):
        for yol in (f"{self.u['id'] + 1}/{'a' * 32}.txt", f"{self.u['id']}/../x.txt", f"{self.u['id']}/kisa.txt", None):
            with self.assertRaises(svc.DocumentValidationError, msg=str(yol)):
                svc.complete_storage_upload(self.conn, self.u, yol, "x.txt", embedder=self.emb)
        self.assertEqual(self.s.istekler, [])                            # depoya hic gidilmedi

    def test_icerik_uzantiyla_uyusmazsa_depodan_silinir(self):
        yol = f"{self.u['id']}/{'b' * 32}.pdf"
        self.s.dosyalar[yol] = b"bu bir pdf degil"
        with self.assertRaises(svc.DocumentValidationError):
            svc.complete_storage_upload(self.conn, self.u, yol, "x.pdf", embedder=self.emb)
        sil = [i for i in self.s.istekler if i["yontem"] == "DELETE"]
        self.assertEqual(json.loads(sil[0]["govde"]), {"prefixes": [yol]})

    def test_gercek_boyut_siniri_asilirsa_reddedilir(self):
        yol = f"{self.u['id']}/{'c' * 32}.txt"
        self.s.dosyalar[yol] = b"a" * (1024 * 1024 + 10)               # tarayici kucuk dedi ama dosya buyuk
        with self.assertRaises(svc.FileTooLargeError):
            svc.complete_storage_upload(self.conn, self.u, yol, "x.txt", embedder=self.emb)
        self.assertTrue(any(i["yontem"] == "DELETE" for i in self.s.istekler))

    def test_belge_silinince_depodaki_dosya_da_silinir(self):
        yol = f"{self.u['id']}/{'d' * 32}.txt"
        self.s.dosyalar[yol] = "Merhaba dünya".encode("utf-8")
        doc = svc.complete_storage_upload(self.conn, self.u, yol, "m.txt", embedder=self.emb)
        svc.delete_document(self.conn, self.u, doc["id"])
        sil = [i for i in self.s.istekler if i["yontem"] == "DELETE"]
        self.assertEqual(json.loads(sil[-1]["govde"]), {"prefixes": [yol]})

    def test_ayar_yoksa_anlasilir_hata(self):
        from app.services import storage
        config.SUPABASE_SERVICE_ROLE_KEY = ""
        with self.assertRaises(storage.StorageError):
            storage.create_signed_upload_url("1/x.txt")

    def test_kova_varsa_olusturulmaz(self):
        from app.services import storage
        self.s.yanitlar[("GET", "/storage/v1/bucket/belgeler")] = [(200, {"name": "belgeler", "public": False})]
        self.assertFalse(storage.ensure_bucket())
        self.assertFalse([i for i in self.s.istekler if i["yontem"] == "POST"])

    def test_kova_yoksa_gizli_ve_boyut_sinirli_olusturulur(self):
        from app.services import storage
        self.s.yanitlar[("GET", "/storage/v1/bucket/belgeler")] = [
            (400, {"statusCode": "404", "error": "Bucket not found", "message": "Bucket not found"})]
        self.s.yanitlar[("POST", "/storage/v1/bucket")] = [(200, {"name": "belgeler"})]
        self.assertTrue(storage.ensure_bucket())
        govde = json.loads(self.s.istekler[-1]["govde"])
        self.assertEqual((govde["name"], govde["public"], govde["file_size_limit"]), ("belgeler", False, 1024 * 1024))

    def test_kova_olusturma_reddedilirse_zaten_var_denmez(self):
        # Gercek hata (2026-10-03): ucretsiz planin 50 MB sinirini asan file_size_limit -> 400, betik "zaten var" diyordu
        from app.services import storage
        self.s.yanitlar[("GET", "/storage/v1/bucket/belgeler")] = [(400, {"message": "Bucket not found"})]
        self.s.yanitlar[("POST", "/storage/v1/bucket")] = [
            (400, {"statusCode": "413", "message": "The object exceeded the maximum allowed size"})]
        with self.assertRaises(storage.StorageError) as cm:
            storage.ensure_bucket()
        self.assertIn("maximum allowed size", str(cm.exception))
        self.assertNotIn("sahte-service-role", str(cm.exception))


# ---------------------------------------------------------------- HTTP: CORS, sinirlar, kok adres
try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None


@unittest.skipIf(TestClient is None, "TestClient (httpx) kurulu degil")
class BulutHttpTests(unittest.TestCase):
    def setUp(self):
        import shutil
        import tempfile
        self.tmp = tempfile.mkdtemp()
        self.eski = (config.DATABASE_URL, config.UPLOAD_DIR, config.STORAGE_BACKEND)
        config.DATABASE_URL = "sqlite:///" + self.tmp.replace("\\", "/") + "/t.db"
        config.UPLOAD_DIR = self.tmp + "/up"
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def tearDown(self):
        config.DATABASE_URL, config.UPLOAD_DIR, config.STORAGE_BACKEND = self.eski

    def _client(self):
        from app.main import app
        return TestClient(app)

    def _token(self, c):
        c.post("/auth/register", json={"email": "bulut@example.com", "password": "Parola123"})
        r = c.post("/auth/login", json={"email": "bulut@example.com", "password": "Parola123"})
        return {"Authorization": "Bearer " + r.json()["access_token"]}

    def test_cors_izinli_adres_ve_izinsiz_adres(self):
        with self._client() as c:
            izinli = config.ALLOWED_ORIGINS[0]
            r = c.options("/auth/login", headers={"Origin": izinli, "Access-Control-Request-Method": "POST",
                                                  "Access-Control-Request-Headers": "content-type"})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.headers.get("access-control-allow-origin"), izinli)
            r = c.options("/auth/login", headers={"Origin": "https://kotu-site.example.com",
                                                  "Access-Control-Request-Method": "POST"})
            self.assertNotEqual(r.headers.get("access-control-allow-origin"), "https://kotu-site.example.com")

    def test_kok_adres_json_ve_arayuz_sunulmuyor(self):
        with self._client() as c:
            r = c.get("/")
            self.assertEqual(r.json()["docs"], "/docs")
            self.assertEqual(c.get("/static/index.html").status_code, 404)

    def test_limits_yukleme_yontemini_soyler(self):
        with self._client() as c:
            h = self._token(c)
            config.STORAGE_BACKEND = "local"
            self.assertEqual(c.get("/documents/limits", headers=h).json()["upload_mode"], "direct")
            r = c.post("/documents/upload-url", headers=h, json={"filename": "a.txt", "size_bytes": 5})
            self.assertEqual(r.status_code, 400)                        # yerel modda depo yolu kapali
            config.STORAGE_BACKEND = "supabase"
            self.assertEqual(c.get("/documents/limits", headers=h).json()["upload_mode"], "storage")

    def test_depo_uzerinden_yukleme_http_ile_bastan_sona(self):
        """upload-url -> (tarayici depoya yukler) -> complete; sonra belge listede, silinince depodan da silinir."""
        s = SahteBulut()
        eski = (config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY, config.EMBEDDING_BACKEND)
        config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY, config.EMBEDDING_BACKEND = s.url, "sahte", "hash"
        config.STORAGE_BACKEND = "supabase"
        try:
            with self._client() as c:
                h = self._token(c)
                r = c.post("/documents/upload-url", headers=h, json={"filename": "ders.txt", "size_bytes": 40})
                self.assertEqual(r.status_code, 200)
                yol = r.json()["path"]
                s.dosyalar[yol] = "Supabase depolama birimi dosyaları saklar.".encode("utf-8")   # tarayicinin PUT'u
                r = c.post("/documents/complete", headers=h, json={"path": yol, "filename": "ders.txt"})
                self.assertEqual(r.status_code, 201, r.text)
                self.assertEqual(r.json()["status"], "indexed")
                belge_id = r.json()["id"]
                self.assertEqual([d["id"] for d in c.get("/documents", headers=h).json()], [belge_id])
                r = c.post("/documents/complete", headers=h, json={"path": "999/" + "a" * 32 + ".txt", "filename": "x.txt"})
                self.assertEqual(r.status_code, 400)                    # baskasinin klasoru
                r = c.post("/documents/upload-url", headers=h, json={"filename": "b.txt", "size_bytes": 10 ** 9})
                self.assertEqual(r.status_code, 413)
                self.assertEqual(c.delete(f"/documents/{belge_id}", headers=h).status_code, 200)
                self.assertTrue(any(i["yontem"] == "DELETE" for i in s.istekler))
        finally:
            config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY, config.EMBEDDING_BACKEND = eski
            s.close()

    def test_depo_erisilemezse_503(self):
        eski = (config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
        config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY = "http://127.0.0.1:9", "sahte"   # kapali port
        config.STORAGE_BACKEND = "supabase"
        try:
            with self._client() as c:
                h = self._token(c)
                r = c.post("/documents/upload-url", headers=h, json={"filename": "a.txt", "size_bytes": 5})
                self.assertEqual(r.status_code, 503)
                self.assertIn("Dosya deposuna ulaşılamadı", r.json()["detail"])
        finally:
            config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY = eski

    def test_sifre_sifirlama_e_postasi_satir_ici_gonderilebilir(self):
        from app.services import mailer
        gonderilen = []
        eski = (mailer.send_reset_code, mailer.can_deliver, config.SEND_EMAIL_INLINE)
        mailer.send_reset_code = lambda *a: gonderilen.append(a)
        mailer.can_deliver = lambda: True
        config.SEND_EMAIL_INLINE = True
        try:
            with self._client() as c:
                self._token(c)
                r = c.post("/auth/forgot-password", json={"email": "bulut@example.com"})
                self.assertEqual(r.status_code, 200)
                self.assertEqual(len(gonderilen), 1)
                self.assertEqual(gonderilen[0][0], "bulut@example.com")
        finally:
            mailer.send_reset_code, mailer.can_deliver, config.SEND_EMAIL_INLINE = eski


# ---------------------------------------------------------------- PostgreSQL: pgvector aramasi
class PgVectorTests(unittest.TestCase):
    def test_pgvector_ve_numpy_ayni_sonucu_verir(self):
        """Ayni veriyle pgvector (SQL) ve numpy (Python) aramasi ayni siralamayi ve skorlari vermeli."""
        conn = make_conn()
        if database.dialect(conn) != "postgres":
            self.skipTest("P55_TEST_PG_URL verilmedi (yalnizca PostgreSQL'de anlamli)")
        from app.db import embeddings as repo
        from app.services import vector_search
        emb = HashingEmbedder()
        u = make_user(conn)
        metinler = ["Kedi süt içer.", "Köpek kemik sever.", "Vektör veritabanı benzerlik araması yapar.",
                    "Veritabanında vektörler saklanır."]
        with TempUploads():
            for i, m in enumerate(metinler):
                svc.upload_document(conn, u, f"d{i}.txt", m.encode("utf-8"), embedder=emb)
        sql_sonuc = vector_search.search(conn, u["id"], "vektör veritabanı", top_k=3, embedder=emb)
        rows = repo.nearest(conn, u["id"], emb.name, emb.embed_query("vektör veritabanı"), 4)
        self.assertEqual(len(sql_sonuc), 3)
        self.assertEqual([r["chunk_id"] for r in rows[:3]], [r["chunk_id"] for r in sql_sonuc])
        # numpy ile elle hesap: kaydedilen metinlerin vektorleriyle nokta carpimi
        q = emb.embed_query("vektör veritabanı")
        beklenen = sorted((float(emb.embed_documents([m])[0] @ q) for m in metinler), reverse=True)[:3]
        np.testing.assert_allclose([r["score"] for r in sql_sonuc], beklenen, atol=1e-5)


if __name__ == "__main__":
    unittest.main()
