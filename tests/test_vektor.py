"""Hafta 7 testleri: embedding, vektor saklama, benzerlik arama, indeksleme."""
import importlib.util
import unittest

import numpy as np
from fastapi import HTTPException

from app.api import documents as docs_api
from app.api import search as search_api
from app.core import config
from app.db import documents as documents_repo
from app.db import embeddings as embeddings_repo
from app.services import documents as svc
from app.services import embedder as emb_mod
from app.services import indexing, vector_search
from app.services.embedder import EmbeddingError, HashingEmbedder, tr_lower
from tests.helpers import TempUploads, make_conn, make_user

VEKTOR_DB = ("Vektor veritabani, metinlerin sayisal vektor temsillerini saklar. Benzerlik arama, soru vektorune "
             "en yakin vektorleri kosinus benzerligi ile bulur. Embedding modelleri anlami vektorle gosterir.")
YEMEK = ("Makarna tarifi icin once suyu kaynatin. Makarnayi tuzlu suda haslayin. Domates sosunu ayri tavada "
         "pisirin ve haslanmis makarnanin uzerine dokun. Afiyet olsun.")
FUTBOL = ("Futbol macinda iki takim sahada gol atmak icin mucadele eder. Hakem maci yonetir. "
          "Gol atan takim sayi kazanir ve mac sonunda en cok golu atan takim galip gelir.")


class EmbedderTests(unittest.TestCase):
    def setUp(self):
        self.e = HashingEmbedder()

    def test_birim_norm_ve_boyut(self):
        m = self.e.embed_documents(["Merhaba dunya", "Baska bir metin burada"])
        self.assertEqual(m.shape, (2, self.e.dim))
        self.assertEqual(m.dtype, np.float32)
        self.assertTrue(np.allclose(np.linalg.norm(m, axis=1), 1.0, atol=1e-5))

    def test_deterministik(self):
        a = HashingEmbedder().embed_query("vektor arama")
        b = HashingEmbedder().embed_query("vektor arama")
        self.assertTrue(np.array_equal(a, b))

    def test_benzer_metin_daha_yakin(self):
        q = self.e.embed_query("benzerlik aramasi nasil yapilir")
        v, y = self.e.embed_documents([VEKTOR_DB, YEMEK])
        self.assertGreater(float(q @ v), float(q @ y))

    def test_bos_metin_sifir_vektor_cokmez(self):
        v = self.e.embed_query("")
        self.assertEqual(float(np.linalg.norm(v)), 0.0)

    def test_turkce_kucuk_harf(self):
        self.assertEqual(tr_lower("IŞIK İSTANBUL"), "ışık istanbul")

    def test_bilinmeyen_backend_hata(self):
        eski = config.EMBEDDING_BACKEND
        try:
            config.EMBEDDING_BACKEND = "yok"
            with self.assertRaises(EmbeddingError):
                emb_mod.get_embedder()
        finally:
            config.EMBEDDING_BACKEND = eski

    @unittest.skipIf(importlib.util.find_spec("sentence_transformers") is not None, "paket kurulu")
    def test_yerel_embedder_paket_yoksa_anlasilir_hata(self):
        with self.assertRaises(EmbeddingError) as e:
            emb_mod.LocalEmbedder().embed_query("x")
        self.assertIn("sentence-transformers", str(e.exception))


class AramaTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        self.u1 = make_user(self.conn, "bir@example.com")
        self.u2 = make_user(self.conn, "iki@example.com")
        self._tmp = TempUploads()
        self._tmp.__enter__()
        self.emb = HashingEmbedder()
        self.d_vek = svc.upload_document(self.conn, self.u1, "vektor.txt", VEKTOR_DB.encode(), embedder=self.emb)
        self.d_yem = svc.upload_document(self.conn, self.u1, "yemek.txt", YEMEK.encode(), embedder=self.emb)
        self.d_fut = svc.upload_document(self.conn, self.u1, "futbol.txt", FUTBOL.encode(), embedder=self.emb)

    def tearDown(self):
        self._tmp.__exit__()

    def test_yukleme_belgeyi_indeksler(self):
        self.assertEqual(self.d_vek["status"], "indexed")
        self.assertEqual(embeddings_repo.count_embeddings(self.conn, self.d_vek["id"]), self.d_vek["chunk_count"])

    def test_dogru_belge_ilk_sirada(self):
        for sorgu, beklenen in [("benzerlik aramasi nasil yapilir", "vektor.txt"),
                                ("makarna nasil pisirilir", "yemek.txt"),
                                ("gol atan takim kazanir mi", "futbol.txt")]:
            sonuc = vector_search.search(self.conn, self.u1["id"], sorgu, 3, embedder=self.emb)
            self.assertEqual(sonuc[0]["filename"], beklenen, sorgu)

    def test_skorlar_azalan_ve_alanlar_dolu(self):
        sonuc = vector_search.search(self.conn, self.u1["id"], "makarna", 3, embedder=self.emb)
        skorlar = [r["score"] for r in sonuc]
        self.assertEqual(skorlar, sorted(skorlar, reverse=True))
        self.assertTrue(all(-1.0001 <= s <= 1.0001 for s in skorlar))
        for k in ("chunk_id", "document_id", "filename", "page_no", "content", "score"):
            self.assertIn(k, sonuc[0])

    def test_top_k_sinirlari(self):
        self.assertEqual(len(vector_search.search(self.conn, self.u1["id"], "makarna", 1, embedder=self.emb)), 1)
        self.assertEqual(len(vector_search.search(self.conn, self.u1["id"], "makarna", 50, embedder=self.emb)), 3)
        for kotu in (0, 51):
            with self.assertRaises(ValueError):
                vector_search.search(self.conn, self.u1["id"], "makarna", kotu, embedder=self.emb)
        with self.assertRaises(ValueError):
            vector_search.search(self.conn, self.u1["id"], "   ", 3, embedder=self.emb)

    def test_baska_kullanici_belgeleri_gormez(self):
        self.assertEqual(vector_search.search(self.conn, self.u2["id"], "makarna", 5, embedder=self.emb), [])

    def test_belge_filtresi(self):
        sonuc = vector_search.search(self.conn, self.u1["id"], "makarna", 5,
                                     document_ids=[self.d_fut["id"]], embedder=self.emb)
        self.assertTrue(sonuc and all(r["document_id"] == self.d_fut["id"] for r in sonuc))

    def test_farkli_modelle_uretilen_vektorler_karismaz(self):
        digeri = HashingEmbedder(dim=256)
        self.assertEqual(vector_search.search(self.conn, self.u1["id"], "makarna", 5, embedder=digeri), [])

    def test_belge_silinince_vektorler_gider(self):
        svc.delete_document(self.conn, self.u1, self.d_yem["id"])
        sonuc = vector_search.search(self.conn, self.u1["id"], "makarna tarifi", 5, embedder=self.emb)
        self.assertNotIn("yemek.txt", [r["filename"] for r in sonuc])


class HataVeYenidenIndeksTests(unittest.TestCase):
    class Bozuk(HashingEmbedder):
        def embed_documents(self, texts):
            raise EmbeddingError("model yok")

    def setUp(self):
        self.conn = make_conn()
        self.u = make_user(self.conn)
        self.diger = make_user(self.conn, "baska@example.com")
        self._tmp = TempUploads()
        self._tmp.__enter__()

    def tearDown(self):
        self._tmp.__exit__()

    def test_embedding_hatasinda_belge_failed_ama_parcalar_korunur(self):
        doc = svc.upload_document(self.conn, self.u, "a.txt", VEKTOR_DB.encode(), embedder=self.Bozuk())
        self.assertEqual(doc["status"], "failed")
        self.assertIn("Gömme", doc["error"])
        self.assertGreaterEqual(doc["chunk_count"], 1)
        yeni = svc.reindex_document(self.conn, self.u, doc["id"], embedder=HashingEmbedder())
        self.assertEqual(yeni["status"], "indexed")
        self.assertIsNone(documents_repo.get_document(self.conn, doc["id"])["error"])

    def test_basarisiz_yeniden_indeks_eski_vektorleri_bozmaz(self):
        emb = HashingEmbedder()
        doc = svc.upload_document(self.conn, self.u, "a.txt", VEKTOR_DB.encode(), embedder=emb)
        onceki = embeddings_repo.count_embeddings(self.conn, doc["id"])
        with self.assertRaises(EmbeddingError):
            indexing.index_document(self.conn, doc["id"], embedder=self.Bozuk())
        self.assertEqual(embeddings_repo.count_embeddings(self.conn, doc["id"]), onceki)

    def test_yeniden_indeks_sahiplik_kontrolu(self):
        doc = svc.upload_document(self.conn, self.u, "a.txt", VEKTOR_DB.encode())
        with self.assertRaises(svc.DocumentNotFoundError):
            svc.reindex_document(self.conn, self.diger, doc["id"])


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        self.u = make_user(self.conn)
        self._tmp = TempUploads()
        self._tmp.__enter__()
        svc.upload_document(self.conn, self.u, "vektor.txt", VEKTOR_DB.encode())

    def tearDown(self):
        self._tmp.__exit__()

    def test_search_ucu(self):
        out = search_api.search_documents(search_api.SearchRequest(query="benzerlik arama"), self.u, self.conn)
        self.assertEqual(out["query"], "benzerlik arama")
        self.assertEqual(out["results"][0]["filename"], "vektor.txt")

    def test_search_hata_kodlari(self):
        with self.assertRaises(HTTPException) as e:
            search_api.search_documents(search_api.SearchRequest(query=" "), self.u, self.conn)
        self.assertEqual(e.exception.status_code, 400)
        with self.assertRaises(HTTPException) as e:
            search_api.search_documents(search_api.SearchRequest(query="x", top_k=999), self.u, self.conn)
        self.assertEqual(e.exception.status_code, 400)

    def test_reindex_ucu(self):
        belge = docs_api.list_documents(self.u, self.conn)[0]
        self.assertEqual(docs_api.reindex(belge["id"], self.u, self.conn)["status"], "indexed")
        with self.assertRaises(HTTPException) as e:
            docs_api.reindex(9999, self.u, self.conn)
        self.assertEqual(e.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
