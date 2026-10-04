"""Groq destegi testleri: OpenAI uyumlu istek bicimi, yanit ayristirma, saglayici secimi.

Yeniden deneme/zaman asimi mantigi Claude ile ORTAK taban siniftadir (tests/test_llm.py zaten sinar);
burada yalnizca Groq'a ozgu farklar ve LLM_PROVIDER secimi test edilir.
"""
import unittest
from pathlib import Path

from fastapi import HTTPException

from app.api import deps
from app.core import config
from app.services.llm_client import (ClaudeClient, GroqClient, LLMAPIError, LLMConfigError, LLMRateLimitError,
                                     get_llm_client)
from tests.test_llm import MESAJ, SahteSunucu

GIZLI = "gsk_TEST-GIZLI-ANAHTAR"


def groq_ok(text="Merhaba!"):
    return (200, {"choices": [{"index": 0, "message": {"role": "assistant", "content": text},
                               "finish_reason": "stop"}],
                  "usage": {"prompt_tokens": 7, "completion_tokens": 4, "total_tokens": 11}}, {}, 0)


class GroqIstemciTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = SahteSunucu()

    @classmethod
    def tearDownClass(cls):
        cls.srv.close()

    def setUp(self):
        self.srv.script.clear()
        self.srv.requests.clear()
        self.sleeps = []

    def client(self, **kw):
        kw.setdefault("api_key", GIZLI)
        kw.setdefault("max_retries", 2)
        kw.setdefault("reasoning_effort", "")
        return GroqClient(base_url=self.srv.url, sleep=self.sleeps.append, **kw)

    def test_istek_bicimi_openai_uyumlu(self):
        self.srv.script.append(groq_ok("Cevap burada"))
        c = self.client(model="test-model")
        self.assertEqual(c.complete("Sistem istemi", MESAJ, max_tokens=123), "Cevap burada")
        r = self.srv.requests[0]
        self.assertEqual(r["path"], "/chat/completions")
        h = {k.lower(): v for k, v in r["headers"].items()}
        self.assertEqual(h["authorization"], f"Bearer {GIZLI}")
        self.assertNotIn("x-api-key", h)
        self.assertNotIn("python-urllib", h["user-agent"].lower())
        # Sistem istemi ayri alan degil, ilk mesajdir
        self.assertEqual(r["body"], {"model": "test-model", "max_tokens": 123,
                                     "messages": [{"role": "system", "content": "Sistem istemi"}] + MESAJ})

    def test_dusunen_model_ayari_gonderilir(self):
        self.srv.script.append(groq_ok())
        self.client(reasoning_effort="low").complete("s", MESAJ)
        self.assertEqual(self.srv.requests[0]["body"]["reasoning_effort"], "low")

    def test_yanita_karismis_dusunce_temizlenir(self):
        self.srv.script.append(groq_ok("<think>Kullanici selam verdi, kisa yanitlayayim.</think>\nMerhaba! [1]"))
        self.assertEqual(self.client().complete("s", MESAJ), "Merhaba! [1]")
        self.srv.script.append(groq_ok("<think>yarida kesilen dusunce"))       # butce dusuncede bitti
        with self.assertRaises(LLMAPIError):
            self.client().complete("s", MESAJ)

    def test_kullanim_claude_adlarina_cevrilir(self):
        self.srv.script.append(groq_ok())
        c = self.client()
        c.complete("s", MESAJ)
        self.assertEqual(c.last_usage, {"input_tokens": 7, "output_tokens": 4})

    def test_cagiranin_listesi_degistirilmez(self):
        self.srv.script.append(groq_ok())
        mesajlar = [{"role": "user", "content": "Selam"}]
        self.client().complete("s", mesajlar)
        self.assertEqual(mesajlar, [{"role": "user", "content": "Selam"}])    # system mesaji eklenmemis

    def test_gecici_hatada_yeniden_dener(self):
        self.srv.script += [(429, {"error": {"message": "rate limit"}}, {}, 0), groq_ok("sonunda")]
        self.assertEqual(self.client().complete("s", MESAJ), "sonunda")
        self.assertEqual(self.sleeps, [1.0])

    def test_hata_mesajlari_groq_adini_tasir_anahtari_tasimaz(self):
        self.srv.script.append((401, {"error": {"message": "Invalid API Key"}}, {}, 0))
        with self.assertRaises(LLMAPIError) as e:
            self.client().complete("s", MESAJ)
        self.assertIn("Groq API hatası (401)", str(e.exception))
        self.assertNotIn(GIZLI, str(e.exception))
        self.srv.script += [(429, {}, {}, 0)] * 3
        with self.assertRaises(LLMRateLimitError) as e:
            self.client().complete("s", MESAJ)
        self.assertIn("Groq", str(e.exception))

    def test_bozuk_ve_bos_yanitlar(self):
        for govde in ({"choices": []}, {"choices": [{"message": {"content": None}}]},
                      {"choices": [{"message": {"content": "   "}}]}, {"baska": 1}, "json-degil"):
            self.srv.script.append((200, govde, {}, 0))
            with self.assertRaises(LLMAPIError):
                self.client().complete("s", MESAJ)

    def test_anahtar_yoksa_ag_cagrisi_yapilmaz(self):
        with self.assertRaises(LLMConfigError) as e:
            self.client(api_key="").complete("s", MESAJ)
        self.assertIn("GROQ_API_KEY", str(e.exception))
        self.assertEqual(self.srv.requests, [])


class SaglayiciSecimiTests(unittest.TestCase):
    def setUp(self):
        self.eski = config.LLM_PROVIDER

    def tearDown(self):
        config.LLM_PROVIDER = self.eski

    def test_env_degerine_gore_istemci(self):
        config.LLM_PROVIDER = "groq"
        self.assertIsInstance(get_llm_client(), GroqClient)
        config.LLM_PROVIDER = "claude"
        self.assertIsInstance(get_llm_client(), ClaudeClient)
        self.assertIsInstance(get_llm_client(" GROQ "), GroqClient)       # bosluk/buyuk harf toleransi

    def test_bilinmeyen_saglayici(self):
        config.LLM_PROVIDER = "openai"
        with self.assertRaises(LLMConfigError):
            get_llm_client()
        with self.assertRaises(HTTPException) as e:                      # API katmani: 500 degil 503
            deps.get_llm()
        self.assertEqual(e.exception.status_code, 503)

    def test_groq_varsayilanlari(self):
        c = GroqClient(api_key="x")
        self.assertEqual(c.base_url, config.GROQ_BASE_URL.rstrip("/"))
        self.assertEqual(c.model, config.GROQ_MODEL)
        self.assertEqual(c.reasoning_effort, config.GROQ_REASONING_EFFORT)


class GroqAnahtarGuvenligiTests(unittest.TestCase):
    def test_groq_anahtari_koda_gomulu_degil(self):
        kok = Path(__file__).resolve().parents[1]
        from scripts.env_olustur import SABLON
        for p in list((kok / "app").rglob("*.py")) + list((kok / "scripts").rglob("*.py")):
            self.assertNotIn("gsk_", p.read_text(encoding="utf-8"), f"{p.name}: gercek Groq anahtari gibi gorunen deger")
        self.assertIn("GROQ_API_KEY=\n", SABLON)


if __name__ == "__main__":
    unittest.main()
