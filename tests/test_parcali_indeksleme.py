"""Buyuk belge: zaman butceli, kaldigi yerden devam eden indeksleme (Vercel'de bir istek en fazla 300 sn).

- Sure dolunca durur, belge 'chunked' kalir, ilerleme (indexed / total) dogru.
- Tekrar cagrilinca yalnizca eksik parcalar islenir; bitince 'indexed'.
- Model degisince eski modelin vektorleri "eksik" sayilir ve yenisiyle degistirilir.
- Embedding yarida patlarsa o ana kadarki vektorler korunur, sonra kalan yerden devam edilir.
- HTTP: yukleme yaniti ilerlemeyi dondurur, POST /documents/{id}/index-next bitirir, baskasinin belgesi 404.
"""
import os
import tempfile
import unittest

from app.core import config
from app.db import embeddings as embeddings_repo
from app.db import documents as documents_repo
from app.services import auth, indexing, vector_search
from app.services import documents as svc
from app.services.embedder import EmbeddingError, HashingEmbedder
from tests.helpers import TempUploads, make_conn, make_user

try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None

# ~200 parca: her paragraf ayri konu, sonuncusu aramada bulunacak ozel bir cumle
GRUP = 2 * 64    # bir cagrida islenen (sahte saatle)
PARAGRAFLAR = [f"Bolum {i}. Bu paragraf {i} numarali konuyu anlatir ve ornek bir metindir." for i in range(199)]
PARAGRAFLAR.append("Son bolum. Kutuphane pazar gunu kapalidir ve cumartesi ogleden sonra acilir.")
METIN = "\n\n".join(PARAGRAFLAR)


class Saat:
    """Her okunusta 10 sn ilerleyen sahte saat. Butce 15 sn: baslangic 10, 1. gruptan sonra 20 (gecen 10, devam),
    2. gruptan sonra 30 (gecen 20 >= 15, dur) -> her cagri tam 2 grup isler. Gercek saat Windows'ta ~15 ms adimli
    oldugu icin "kac grup" sayisi ona gore degisirdi; sahte saat testi zamandan bagimsiz yapar."""

    def __init__(self):
        self.t = 0.0

    def __call__(self):
        self.t += 10
        return self.t


class BozukEmbedder(HashingEmbedder):
    """Ilk n cagridan sonra hata verir (Hugging Face'in yarida kopmasi gibi)."""

    def __init__(self, n):
        super().__init__()
        self.kalan = n

    def embed_documents(self, texts):
        if self.kalan <= 0:
            raise EmbeddingError("baglanti koptu")
        self.kalan -= 1
        return super().embed_documents(texts)


class ParcaliIndekslemeTests(unittest.TestCase):
    def setUp(self):
        self._eski = (config.CHUNK_SIZE, config.CHUNK_OVERLAP, config.INDEX_BUDGET_SECONDS, config.MIN_SCORE)
        config.CHUNK_SIZE, config.CHUNK_OVERLAP = 80, 10          # kucuk parcalar: cok parca, birden cok grup
        config.INDEX_BUDGET_SECONDS = 15                           # sahte saatle: her cagri 2 grup
        self._eski_saat = indexing._now
        indexing._now = Saat()
        self.conn = make_conn()
        self.u = make_user(self.conn, "buyuk@example.com")
        self.diger = make_user(self.conn, "diger@example.com")
        self._tmp = TempUploads()
        self._tmp.__enter__()
        self.emb = HashingEmbedder()

    def tearDown(self):
        config.CHUNK_SIZE, config.CHUNK_OVERLAP, config.INDEX_BUDGET_SECONDS, config.MIN_SCORE = self._eski
        indexing._now = self._eski_saat
        self._tmp.__exit__()

    def yukle(self):
        return svc.upload_document(self.conn, self.u, "buyuk.txt", METIN.encode(), embedder=self.emb)

    def test_butce_dolunca_durur_ve_ilerleme_dogru(self):
        doc = self.yukle()
        self.assertGreater(doc["chunk_count"], 2 * GRUP)
        self.assertEqual(doc["status"], "chunked")                # bitmedi: arayuz devam ettirecek
        p = indexing.progress(self.conn, doc["id"], self.emb.name)
        self.assertEqual(p, {"indexed": GRUP, "total": doc["chunk_count"], "done": False})
        out = svc.public_document_with_progress(self.conn, doc, embedder=self.emb)
        self.assertEqual((out["indexed_chunks"], out["total_chunks"]), (GRUP, doc["chunk_count"]))

    def test_kaldigi_yerden_devam_eder_ve_biter(self):
        doc = self.yukle()
        tur = 0
        while documents_repo.get_document(self.conn, doc["id"])["status"] == "chunked":
            tur += 1
            self.assertLess(tur, 20, "sonsuz dongu")
            svc.continue_indexing(self.conn, self.u, doc["id"], embedder=self.emb)
        self.assertEqual(documents_repo.get_document(self.conn, doc["id"])["status"], "indexed")
        self.assertEqual(embeddings_repo.count_embeddings(self.conn, doc["id"]), doc["chunk_count"])
        self.assertGreaterEqual(tur, 2)                            # gercekten birden cok istekte bitti
        config.MIN_SCORE = 0.0
        sonuc = vector_search.search(self.conn, self.u["id"], "kutuphane pazar gunu kapali", 3, embedder=self.emb)
        self.assertTrue(any("pazar" in r["content"] for r in sonuc))   # SON parca da aranabiliyor

    def test_butce_sahte_saatle(self):
        doc = self.yukle()
        state = indexing.index_next(self.conn, doc["id"], self.emb, budget_seconds=15, clock=Saat())
        self.assertEqual(state["indexed"], 2 * GRUP)               # yuklemedeki 2 grup + bu cagridaki 2 grup
        state = indexing.index_next(self.conn, doc["id"], self.emb, budget_seconds=0)
        self.assertTrue(state["done"])

    def test_model_degisince_eski_vektorler_yenilenir(self):
        config.INDEX_BUDGET_SECONDS = 0
        doc = self.yukle()
        self.assertEqual(doc["status"], "indexed")
        yeni = HashingEmbedder(dim=256)                            # farkli ad: "hash-v1-256"
        self.assertEqual(indexing.progress(self.conn, doc["id"], yeni.name)["indexed"], 0)
        state = indexing.index_next(self.conn, doc["id"], yeni)
        self.assertTrue(state["done"])
        self.assertEqual(embeddings_repo.count_embeddings(self.conn, doc["id"], model=self.emb.name), 0)
        self.assertEqual(embeddings_repo.count_embeddings(self.conn, doc["id"]), doc["chunk_count"])  # cift kayit yok

    def test_yarida_hata_sonra_devam(self):
        config.INDEX_BUDGET_SECONDS = 0
        doc = svc.upload_document(self.conn, self.u, "buyuk.txt", METIN.encode(), embedder=BozukEmbedder(2))
        doc = documents_repo.get_document(self.conn, doc["id"])
        self.assertEqual(doc["status"], "failed")
        self.assertIn("baglanti koptu", doc["error"])
        self.assertEqual(embeddings_repo.count_embeddings(self.conn, doc["id"]), 2 * indexing.BATCH_SIZE)  # korundu
        with self.assertRaises(EmbeddingError):
            svc.continue_indexing(self.conn, self.u, doc["id"], embedder=BozukEmbedder(0))
        svc.continue_indexing(self.conn, self.u, doc["id"], embedder=self.emb)
        self.assertEqual(documents_repo.get_document(self.conn, doc["id"])["status"], "indexed")

    def test_baskasinin_belgesi_devam_ettirilemez(self):
        doc = self.yukle()
        with self.assertRaises(svc.DocumentNotFoundError):
            svc.continue_indexing(self.conn, self.diger, doc["id"], embedder=self.emb)

    def test_yeniden_indeksle_butceliyken_kaldigi_yerden(self):
        doc = self.yukle()
        out = svc.reindex_document(self.conn, self.u, doc["id"], embedder=self.emb)
        p = indexing.progress(self.conn, doc["id"], self.emb.name)
        self.assertEqual(p["indexed"], 2 * GRUP)                   # bastan degil, kalan yerden devam
        self.assertEqual(out["status"], "chunked")


@unittest.skipIf(TestClient is None, "TestClient (httpx) kurulu degil")
class IndexNextHttpTests(unittest.TestCase):
    def test_yukleme_ilerleme_dondurur_index_next_bitirir(self):
        from app.main import app
        tmp = tempfile.mkdtemp()
        eski = (config.DATABASE_URL, config.UPLOAD_DIR, config.CHUNK_SIZE, config.CHUNK_OVERLAP, config.INDEX_BUDGET_SECONDS)
        config.DATABASE_URL = "sqlite:///" + os.path.join(tmp, "t.db")
        config.UPLOAD_DIR = os.path.join(tmp, "up")
        config.CHUNK_SIZE, config.CHUNK_OVERLAP, config.INDEX_BUDGET_SECONDS = 80, 10, 15
        eski_saat, indexing._now = indexing._now, Saat()
        try:
            auth.reset_failed_attempts()
            with TestClient(app) as c:
                h = {}
                for email in ("a@example.com", "b@example.com"):
                    c.post("/auth/register", json={"full_name": "Deneme Kişi", "email": email, "password": "Guclu1234"})
                    tok = c.post("/auth/login", json={"email": email, "password": "Guclu1234"}).json()["access_token"]
                    h[email] = {"Authorization": "Bearer " + tok}
                ha = h["a@example.com"]
                r = c.post("/documents", headers=ha, files={"file": ("b.txt", METIN.encode(), "text/plain")})
                self.assertEqual(r.status_code, 201)
                d = r.json()
                self.assertEqual(d["status"], "chunked")
                self.assertEqual(d["indexed_chunks"], GRUP)
                self.assertEqual(d["total_chunks"], d["chunk_count"])
                self.assertEqual(c.post(f"/documents/{d['id']}/index-next", headers=h["b@example.com"]).status_code, 404)
                for _ in range(20):
                    d = c.post(f"/documents/{d['id']}/index-next", headers=ha).json()
                    if d["status"] == "indexed":
                        break
                self.assertEqual(d["status"], "indexed")
                self.assertNotIn("indexed_chunks", d)              # bitince ilerleme alani yok
                self.assertEqual(c.get("/documents/limits", headers=ha).json()["index_budget_seconds"], 15)
        finally:
            indexing._now = eski_saat
            (config.DATABASE_URL, config.UPLOAD_DIR, config.CHUNK_SIZE, config.CHUNK_OVERLAP,
             config.INDEX_BUDGET_SECONDS) = eski


if __name__ == "__main__":
    unittest.main()
