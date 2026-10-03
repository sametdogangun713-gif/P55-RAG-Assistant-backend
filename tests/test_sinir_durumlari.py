"""Hafta 13: sinir (edge) durumlari ve hata senaryolari. Mutlu yolun disindaki davranislari sinar."""
import io
import os
import shutil
import sqlite3
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path

import numpy as np
from fastapi import HTTPException, UploadFile

from app.api import documents as docs_api
from app.api import search as search_api
from app.core import config, security
from app.db import database, documents as documents_repo, users
from app.services import auth, chunker, parser, vector_search
from app.services import documents as svc
from app.services.embedder import EmbeddingError, HashingEmbedder
from tests.helpers import TempUploads, make_conn, make_user


class ParcalamaSinirlari(unittest.TestCase):
    def test_buyuk_metin_makul_surede_parcalanir(self):
        metin = " ".join(f"Bu {i}. cumle, belge tabanli soru cevap sistemi icin ornek icerik tasir." for i in range(30000))
        self.assertGreater(len(metin), 2_000_000)
        t = time.perf_counter()
        parcalar = chunker.split_text(metin, 600, 100)
        self.assertLess(time.perf_counter() - t, 10.0)
        self.assertGreater(len(parcalar), 1000)
        self.assertTrue(all(len(p) <= 600 for p in parcalar))

    def test_yalnizca_noktalama_ve_bosluk(self):
        self.assertEqual(chunker.split_text("...  ?!  \n\n  ", 600, 100), ["... ?!"])
        self.assertEqual(chunker.split_text("\n\n\n", 600, 100), [])

    def test_sayfa_sinirinda_bos_sayfalar_atlanir(self):
        out = chunker.chunk_pages([(1, "Bir."), (2, ""), (3, "Uc.")])
        self.assertEqual([(c.index, c.page_no) for c in out], [(0, 1), (1, 3)])


class YuklemeSinirlari(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        self.u = make_user(self.conn)
        self._tmp = TempUploads()
        self.dir = self._tmp.__enter__()

    def tearDown(self):
        self._tmp.__exit__()

    def test_cok_uzun_dosya_adi_uzantisini_kaybetmez(self):
        ad = "a" * 200 + ".txt"
        doc = svc.upload_document(self.conn, self.u, ad, b"Merhaba dunya. Ornek.")
        self.assertTrue(doc["filename"].endswith(".txt"))
        self.assertLessEqual(len(doc["filename"]), 150)
        self.assertIn(doc["status"], ("chunked", "indexed"))

    def test_yalnizca_bosluk_iceren_dosya_failed_olur(self):
        doc = svc.upload_document(self.conn, self.u, "bos.txt", b"   \n\n   \t  ")
        self.assertEqual(doc["status"], "failed")

    def test_ikili_cop_veri_txt_olarak_cokmez(self):
        doc = svc.upload_document(self.conn, self.u, "cop.txt", bytes(range(256)) * 20)
        self.assertIn(doc["status"], ("chunked", "indexed", "failed"))

    def test_emoji_ve_unicode_dosya_adi(self):
        doc = svc.upload_document(self.conn, self.u, "📄 ders notu çğış.txt", "Türkçe içerik. İkinci cümle.".encode())
        self.assertEqual(doc["filename"], "📄 ders notu çğış.txt")

    def test_docx_zip_bombasi_reddedilir(self):
        eski = config.MAX_DOCX_UNCOMPRESSED_MB
        config.MAX_DOCX_UNCOMPRESSED_MB = 1
        try:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("word/document.xml", b"0" * (3 * 1024 * 1024))   # 3 MB, siktirilinca birkac KB
            self.assertLess(len(buf.getvalue()), 100_000)
            doc = svc.upload_document(self.conn, self.u, "bomba.docx", buf.getvalue())
            self.assertEqual(doc["status"], "failed")
            self.assertIn("büyük", doc["error"])
        finally:
            config.MAX_DOCX_UNCOMPRESSED_MB = eski


class GuvenlikSinirlari(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        auth.reset_failed_attempts()

    def test_verify_password_beklenmedik_girdilerde_cokmez(self):
        for kotu in (None, "", "scrypt", "scrypt$a$b$c$d$e", 123):
            self.assertFalse(security.verify_password("x", kotu))

    def test_suresi_tam_dolan_token_gecersiz(self):
        t = security.create_access_token(1, "user", expires_minutes=0)
        with self.assertRaises(security.TokenError):
            security.decode_access_token(t)

    def test_basarisiz_giris_sayaci_sinirsiz_buyumez(self):
        eski_sinir, eski_dogrula = auth.MAX_TRACKED_EMAILS, auth.security.verify_password
        auth.MAX_TRACKED_EMAILS = 50
        auth.security.verify_password = lambda *a, **k: False       # testi hizlandir (gercek scrypt yavas)
        try:
            for i in range(200):
                with self.assertRaises(auth.InvalidCredentialsError):
                    auth.login(self.conn, f"hedef{i}@example.com", "Yanlis1234")
            self.assertLessEqual(len(auth._failed), 50)
            self.assertIn("hedef199@example.com", auth._failed)       # en yeni kayit korunur, en eskiler atilir
            self.assertNotIn("hedef0@example.com", auth._failed)
        finally:
            auth.MAX_TRACKED_EMAILS, auth.security.verify_password = eski_sinir, eski_dogrula

    def test_varsayilan_gizli_anahtar_uretimde_reddedilir(self):
        eskiler = (config.SECRET_KEY, config.APP_ENV)
        try:
            config.SECRET_KEY, config.APP_ENV = "degistir-bunu", "production"
            with self.assertRaises(RuntimeError):
                config.check_secret_key()
            config.SECRET_KEY = "kisa"
            with self.assertRaises(RuntimeError):
                config.check_secret_key()
            config.SECRET_KEY = "x" * 40
            config.check_secret_key()                                   # guclu anahtar: sorun yok
            config.SECRET_KEY, config.APP_ENV = "degistir-bunu", "development"
            with self.assertWarns(UserWarning):                          # gelistirmede yalnizca uyari
                config.check_secret_key()
        finally:
            config.SECRET_KEY, config.APP_ENV = eskiler


class AramaSinirlari(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        self.u = make_user(self.conn)
        self._tmp = TempUploads()
        self._tmp.__enter__()
        svc.upload_document(self.conn, self.u, "a.txt", b"Vektor veritabani benzerlik arama ornek metni.")

    def tearDown(self):
        self._tmp.__exit__()

    def test_asiri_uzun_sorgu_reddedilir(self):
        with self.assertRaises(ValueError):
            vector_search.search(self.conn, self.u["id"], "x" * (config.MAX_QUESTION_CHARS + 1))
        with self.assertRaises(HTTPException) as e:
            search_api.search_documents(search_api.SearchRequest(query="y" * 5000), self.u, self.conn)
        self.assertEqual(e.exception.status_code, 400)

    def test_embedding_hatasi_503(self):
        class Bozuk(HashingEmbedder):
            def embed_query(self, text):
                raise EmbeddingError("model yok")
        with self.assertRaises(EmbeddingError):
            vector_search.search(self.conn, self.u["id"], "arama", embedder=Bozuk())

    def test_emoji_ve_ozel_karakterli_sorgu_cokmez(self):
        r = vector_search.search(self.conn, self.u["id"], "🔍 ' OR 1=1 -- <script>alert(1)</script>")
        self.assertIsInstance(r, list)

    def test_hic_belge_yoksa_bos_liste(self):
        yeni = make_user(self.conn, "yeni@example.com")
        self.assertEqual(vector_search.search(self.conn, yeni["id"], "arama"), [])


class VeritabaniSinirlari(unittest.TestCase):
    def test_hatali_migration_geri_alinir_ve_kaydedilmez(self):
        tmp = Path(tempfile.mkdtemp())
        eski = database.MIGRATIONS_DIR
        try:
            (tmp / "001_iyi.sql").write_text("CREATE TABLE a (id INTEGER);", encoding="utf-8")
            (tmp / "002_bozuk.sql").write_text("CREATE TABLE b (id INTEGER); INSERT INTO yok_tablo VALUES (1);", encoding="utf-8")
            database.MIGRATIONS_DIR = tmp
            conn = database.get_connection(":memory:")
            with self.assertRaises(sqlite3.Error):
                database.run_migrations(conn)
            tablolar = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertIn("a", tablolar)                    # 001 uygulandi
            self.assertNotIn("b", tablolar)                 # 002 tamamen geri alindi
            uygulanan = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
            self.assertEqual(uygulanan, {"001_iyi"})
        finally:
            database.MIGRATIONS_DIR = eski
            shutil.rmtree(tmp, ignore_errors=True)

    def test_eszamanli_yazmalar_kilitlenmez(self):
        tmp = tempfile.mkdtemp()
        yol = os.path.join(tmp, "t.db")
        try:
            c0 = database.get_connection(yol)
            database.run_migrations(c0)
            kul = users.create_user(c0, "a@example.com", "x")
            c0.close()
            hatalar = []

            def isci(n):
                try:
                    c = database.get_connection(yol)
                    for i in range(25):
                        documents_repo.create_document(c, kul["id"], f"d{n}_{i}.txt")
                    c.close()
                except Exception as e:     # noqa
                    hatalar.append(repr(e))

            threads = [threading.Thread(target=isci, args=(n,)) for n in range(8)]
            [t.start() for t in threads]
            [t.join() for t in threads]
            self.assertEqual(hatalar, [])
            c = database.get_connection(yol)
            self.assertEqual(c.execute("SELECT COUNT(*) FROM documents").fetchone()[0], 200)
            c.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
