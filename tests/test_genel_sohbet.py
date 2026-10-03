"""Belge disi genel sohbet (GENERAL_CHAT): selamlasma ve genel sorulara etiketli, kaynaksiz yanit.

Kural: belgelerde yanit varsa davranis DEGISMEZ (kaynakli yanit). Yalnizca "ilgili parca yok" (no_context) ya da
"model BILGI_YOK dedi" (no_info) durumunda modelin genel bilgisine gidilir; yanit "general" durumuyla, kaynaksiz
ve grounded=False kaydedilir. Genel cagri basarisiz olursa eski "bilgi bulamadim" yaniti kalir.
"""
import unittest

from app.core import config
from app.services import chat, prompts, rag
from app.services import documents as svc
from app.services import reports
from app.services.llm_client import LLMTimeoutError
from tests.helpers import ScriptedLLM, TempUploads, make_conn, make_user

VEKTOR_DB = ("Vektor veritabani, metinlerin sayisal vektor temsillerini saklar. Benzerlik arama, soru vektorune "
             "en yakin vektorleri kosinus benzerligi ile bulur. Embedding modelleri anlami vektorle gosterir.")


class GenelSohbetTests(unittest.TestCase):
    def setUp(self):
        self._eski = (config.MIN_SCORE, config.GENERAL_CHAT)
        config.MIN_SCORE, config.GENERAL_CHAT = 0.15, True
        self.conn = make_conn()
        self.u = make_user(self.conn, "genel@example.com")
        self._tmp = TempUploads()
        self._tmp.__enter__()
        svc.upload_document(self.conn, self.u, "vektor.txt", VEKTOR_DB.encode())
        self.conv = chat.create_conversation(self.conn, self.u)

    def tearDown(self):
        config.MIN_SCORE, config.GENERAL_CHAT = self._eski
        self._tmp.__exit__()

    def gonder(self, metin, llm):
        return chat.send_message(self.conn, self.u, self.conv["id"], metin, llm)

    def test_selamlasmaya_genel_yanit_kaynaksiz_ve_etiketli(self):
        llm = ScriptedLLM("Merhaba! Belgelerinle ilgili ne sormak istersin?")
        out = self.gonder("merhaba", llm)["assistant_message"]
        self.assertEqual(out["status"], chat.GENERAL)
        self.assertFalse(out["grounded"])
        self.assertEqual(out["sources"], [])
        self.assertIn("Merhaba", out["content"])
        self.assertEqual(llm.cagrilar[-1]["system"], prompts.GENERAL_SYSTEM_PROMPT)   # RAG istemi degil
        self.assertNotIn("<kaynaklar>", llm.cagrilar[-1]["messages"][-1]["content"])  # belge metni gitmez

    def test_model_bilgi_yok_derse_genel_yanita_gecer(self):
        llm = ScriptedLLM(prompts.NO_INFO_MARKER, "Bunu belgelerinde bulamadım; genel olarak ...")
        out = self.gonder("vektor veritabani hangi yil icat edildi", llm)["assistant_message"]
        self.assertEqual(out["status"], chat.GENERAL)
        self.assertEqual(len(llm.cagrilar), 2)                # once RAG, sonra genel

    def test_belgede_yanit_varsa_davranis_degismez(self):
        llm = ScriptedLLM("Vektor temsillerini saklar [1].")
        out = self.gonder("vektor veritabani ne saklar", llm)["assistant_message"]
        self.assertEqual(out["status"], rag.ANSWERED)
        self.assertTrue(out["grounded"])
        self.assertEqual(len(llm.cagrilar), 1)                # genel cagri yapilmaz

    def test_genel_yanittaki_sahte_alinti_silinir(self):
        out = self.gonder("merhaba", ScriptedLLM("Merhaba【1】, yardımcı olabilirim [2]."))["assistant_message"]
        self.assertNotRegex(out["content"], r"\[\d\]|【")
        self.assertEqual(out["sources"], [])

    def test_genel_cagri_hata_verirse_bilgi_yok_kalir(self):
        out = self.gonder("merhaba", ScriptedLLM(LLMTimeoutError("zaman asimi")))["assistant_message"]
        self.assertEqual(out["status"], rag.NO_CONTEXT)
        self.assertEqual(out["content"], rag.NO_INFO_TEXT)

    def test_kapaliyken_eski_davranis(self):
        config.GENERAL_CHAT = False
        out = self.gonder("merhaba", ScriptedLLM())["assistant_message"]   # LLM hic cagrilmamali
        self.assertEqual(out["status"], rag.NO_CONTEXT)

    def test_gecmiste_kalici_ve_raporda_ayri_sayilir(self):
        self.gonder("merhaba", ScriptedLLM("Merhaba!"))
        mesajlar = chat.list_messages(self.conn, self.u, self.conv["id"])
        self.assertEqual(mesajlar[-1]["status"], chat.GENERAL)
        r = reports.usage_report(self.conn, self.u["id"], days=7)
        self.assertEqual(r["period"]["by_status"]["general"], 1)
        self.assertEqual(r["period"]["grounded_rate"], 0.0)   # genel yanit kaynaga dayali SAYILMAZ

    def test_istem_kurallari(self):
        s = prompts.GENERAL_SYSTEM_PROMPT
        self.assertIn("BULUNAMADI", s)
        self.assertIn("kaynak numarası YAZMA", s)
        self.assertIn("uydurma", s)


if __name__ == "__main__":
    unittest.main()
