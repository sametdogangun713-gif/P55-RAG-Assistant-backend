"""Gemini embedding: istek bicimi, gruplama, normalizasyon, 429 (dakikalik / gunluk sinir), gecersiz anahtar.

Gercek Google'a gidilmez: yerelde sahte bir sunucu Gemini'nin yanit bicimini taklit eder.
Hugging Face'in 402 (aylik ucretsiz kredi bitti) hatasinin anlasilir mesaji da burada denenir.
"""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

import numpy as np

from app.core import config
from app.services import embedder as emb_mod
from app.services.embedder import EmbeddingError, GeminiEmbedder, HFEmbedder

ANAHTAR = "AIza-sahte-anahtar-123"


class SahteGemini:
    """Her istegi kaydeder; sirayla verilen (durum, govde) yanitlarini dondurur, bitince basarili yanit."""

    def __init__(self, dim=8):
        self.istekler, self.yanitlar, self.dim = [], [], dim
        sahte = self

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                govde = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                sahte.istekler.append({"yol": self.path, "anahtar": self.headers.get("x-goog-api-key"), "govde": govde})
                durum, cevap = sahte.yanitlar.pop(0) if sahte.yanitlar else (200, None)
                if cevap is None:            # basarili: her metin icin normalize EDILMEMIS bir vektor
                    cevap = {"embeddings": [{"values": [float(len(r["content"]["parts"][0]["text"]))] + [1.0] * (sahte.dim - 1)}
                                            for r in govde["requests"]]}
                veri = json.dumps(cevap).encode()
                self.send_response(durum)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(veri)))
                self.end_headers()
                self.wfile.write(veri)

            def log_message(self, *a):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/v1beta"

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def sinir_hatasi(gunluk=False, bekle="7s"):
    """Gemini'nin 429 RESOURCE_EXHAUSTED govdesi (QuotaFailure + RetryInfo)."""
    kota = "EmbedContentRequestsPerDayPerUserPerProjectPerModel-FreeTier" if gunluk else "EmbedContentRequestsPerMinutePerProjectPerModel-FreeTier"
    return (429, {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "quota", "details": [
        {"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{"quotaId": kota}]},
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": bekle}]}})


class GeminiEmbedderTests(unittest.TestCase):
    def setUp(self):
        self.sahte = SahteGemini()
        self.bekleme = []
        self.e = GeminiEmbedder(model_name="gemini-embedding-001", api_key=ANAHTAR, base_url=self.sahte.url,
                                dim=8, batch_size=2, sleep=self.bekleme.append)

    def tearDown(self):
        self.sahte.close()

    def test_istek_bicimi_gruplama_ve_normalizasyon(self):
        v = self.e.embed_documents(["bir", "iki", "üçüncü", "dört", "beş"])
        self.assertEqual(v.shape, (5, 8))
        self.assertTrue(np.allclose(np.linalg.norm(v, axis=1), 1.0))      # 768 < 3072: biz normalize ederiz
        self.assertEqual(len(self.sahte.istekler), 3)                       # 5 metin, grupta 2 -> 3 istek
        ilk = self.sahte.istekler[0]
        self.assertEqual(ilk["yol"], "/v1beta/models/gemini-embedding-001:batchEmbedContents")
        self.assertEqual(ilk["anahtar"], ANAHTAR)                           # anahtar baslikta, URL'de degil
        self.assertNotIn(ANAHTAR, ilk["yol"])
        r = ilk["govde"]["requests"][0]
        self.assertEqual((r["model"], r["taskType"], r["outputDimensionality"]), ("models/gemini-embedding-001", "RETRIEVAL_DOCUMENT", 8))
        self.assertEqual(r["content"]["parts"][0]["text"], "bir")
        self.assertEqual(self.e.name, "gemini:gemini-embedding-001:8")

    def test_soru_retrieval_query_ile_gider(self):
        q = self.e.embed_query("Ödev ne zaman?")
        self.assertEqual(q.shape, (8,))
        self.assertEqual(self.sahte.istekler[0]["govde"]["requests"][0]["taskType"], "RETRIEVAL_QUERY")

    def test_dakikalik_sinirda_soylenen_sure_kadar_bekleyip_yeniden_dener(self):
        self.sahte.yanitlar = [sinir_hatasi(bekle="7s")]
        v = self.e.embed_documents(["a"])
        self.assertEqual(v.shape, (1, 8))
        self.assertEqual(self.bekleme, [7.0])
        self.assertEqual(len(self.sahte.istekler), 2)

    def test_bekleme_suresi_ust_sinirla_kesilir_ve_israrla_429_anlasilir_hata(self):
        self.sahte.yanitlar = [sinir_hatasi(bekle="120s")] * 3
        with self.assertRaises(EmbeddingError) as cm:
            self.e.embed_documents(["a"])
        self.assertIn("dakikalık", str(cm.exception))
        self.assertIn("Devam et", str(cm.exception))
        self.assertEqual(self.bekleme, [GeminiEmbedder.MAX_WAIT] * 2)        # 2 yeniden deneme, her biri en fazla 30 sn

    def test_gunluk_sinirda_beklemeden_anlasilir_hata(self):
        self.sahte.yanitlar = [sinir_hatasi(gunluk=True)]
        with self.assertRaises(EmbeddingError) as cm:
            self.e.embed_documents(["a"])
        self.assertIn("günlük", str(cm.exception))
        self.assertEqual(self.bekleme, [])
        self.assertEqual(len(self.sahte.istekler), 1)

    def test_gecersiz_anahtar_anlasilir_hata_ve_anahtar_sizmaz(self):
        self.sahte.yanitlar = [(400, {"error": {"code": 400, "message": "API key not valid. Please pass a valid API key.",
                                                "status": "INVALID_ARGUMENT", "details": [{"reason": "API_KEY_INVALID"}]}})]
        with self.assertRaises(EmbeddingError) as cm:
            self.e.embed_documents(["a"])
        self.assertIn("GEMINI_API_KEY", str(cm.exception))
        self.assertNotIn(ANAHTAR, str(cm.exception))

    def test_anahtar_yoksa_istek_atilmaz(self):
        e = GeminiEmbedder(api_key="", base_url=self.sahte.url, dim=8)
        with self.assertRaises(EmbeddingError):
            e.embed_documents(["a"])
        self.assertEqual(self.sahte.istekler, [])

    def test_beklenmeyen_boyut_reddedilir(self):
        self.sahte.yanitlar = [(200, {"embeddings": [{"values": [1.0, 2.0]}]})]
        with self.assertRaises(EmbeddingError):
            self.e.embed_documents(["a"])

    def test_ayarla_secilir(self):
        with mock.patch.object(config, "EMBEDDING_BACKEND", "gemini"), mock.patch.dict(emb_mod._cache, clear=True):
            self.assertIsInstance(emb_mod.get_embedder(), GeminiEmbedder)


class HF402Tests(unittest.TestCase):
    def test_aylik_kredi_bitince_anlasilir_hata(self):
        sahte = SahteGemini()
        sahte.yanitlar = [(402, {"error": "You have exceeded your monthly included credits for Inference Providers."})]
        try:
            e = HFEmbedder(token="hf_sahte", base_url=sahte.url, sleep=lambda s: None)
            with self.assertRaises(EmbeddingError) as cm:
                e.embed_documents(["a"])
        finally:
            sahte.close()
        self.assertIn("aylık ücretsiz", str(cm.exception))
        self.assertIn("EMBEDDING_BACKEND=gemini", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
