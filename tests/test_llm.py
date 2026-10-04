"""Hafta 9 testleri: Claude API istemcisi (gercek yerel HTTP sunucusuyla), hata yonetimi, admin ucu."""
import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from fastapi import HTTPException

from app.api import admin as admin_api
from app.api import errors
from app.services.llm_client import (ClaudeClient, LLMAPIError, LLMConfigError, LLMError,
                                     LLMRateLimitError, LLMTimeoutError)

GIZLI = "sk-ant-TEST-GIZLI-ANAHTAR"


class SahteSunucu:
    """Yerel, sahte bir 'Claude API'. Sirayla onceden belirlenmis yanitlari verir ve gelen istekleri kaydeder."""

    def __init__(self):
        self.script = []          # [(status, body_dict_or_str, extra_headers, delay_sn)]
        self.requests = []        # [{'path', 'headers', 'body'}]
        outer = self

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                n = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(n).decode("utf-8")
                try:
                    parsed = json.loads(body)
                except ValueError:
                    parsed = body
                outer.requests.append({"path": self.path, "headers": dict(self.headers), "body": parsed})
                status, payload, headers, delay = outer.script.pop(0) if outer.script else (500, {}, {}, 0)
                if delay:
                    time.sleep(delay)
                data = payload if isinstance(payload, str) else json.dumps(payload)
                try:
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json")
                    for k, v in (headers or {}).items():
                        self.send_header(k, v)
                    self.send_header("Content-Length", str(len(data.encode())))
                    self.end_headers()
                    self.wfile.write(data.encode())
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *a):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def ok(text="Merhaba!"):
    return (200, {"content": [{"type": "text", "text": text}], "usage": {"input_tokens": 5, "output_tokens": 3}}, {}, 0)


MESAJ = [{"role": "user", "content": "Selam"}]


class IstemciTests(unittest.TestCase):
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
        return ClaudeClient(base_url=self.srv.url, sleep=self.sleeps.append, **kw)

    def test_basarili_istek_ve_basliklar(self):
        self.srv.script.append(ok("Cevap burada"))
        c = self.client(model="test-model")
        self.assertEqual(c.complete("Sistem istemi", MESAJ, max_tokens=123), "Cevap burada")
        r = self.srv.requests[0]
        self.assertEqual(r["path"], "/v1/messages")
        h = {k.lower(): v for k, v in r["headers"].items()}
        self.assertEqual(h["x-api-key"], GIZLI)
        self.assertEqual(h["anthropic-version"], "2023-06-01")
        self.assertEqual(h["content-type"], "application/json")
        self.assertEqual(r["body"], {"model": "test-model", "max_tokens": 123, "system": "Sistem istemi", "messages": MESAJ})
        self.assertEqual(c.last_usage["output_tokens"], 3)

    def test_birden_cok_metin_blogu_birlestirilir(self):
        self.srv.script.append((200, {"content": [{"type": "text", "text": "Bir "}, {"type": "other"},
                                                  {"type": "text", "text": "iki"}]}, {}, 0))
        self.assertEqual(self.client().complete("s", MESAJ), "Bir iki")

    def test_gecici_hatada_yeniden_dener(self):
        self.srv.script += [(429, {"error": {"message": "yavasla"}}, {}, 0), (503, {}, {}, 0), ok("sonunda")]
        self.assertEqual(self.client().complete("s", MESAJ), "sonunda")
        self.assertEqual(len(self.srv.requests), 3)
        self.assertEqual(self.sleeps, [1.0, 2.0])            # ustel geri cekilme

    def test_retry_after_basligina_uyulur(self):
        self.srv.script += [(429, {}, {"retry-after": "2"}, 0), ok()]
        self.client().complete("s", MESAJ)
        self.assertEqual(self.sleeps, [2.0])

    def test_surekli_500_ise_denemeler_biter_LLMAPIError(self):
        self.srv.script += [(500, {"error": {"message": "sunucu hatasi"}}, {}, 0)] * 3
        with self.assertRaises(LLMAPIError) as e:
            self.client().complete("s", MESAJ)
        self.assertEqual(e.exception.status_code, 500)
        self.assertEqual(len(self.srv.requests), 3)           # ilk + 2 yeniden deneme

    def test_surekli_429_LLMRateLimitError(self):
        self.srv.script += [(429, {}, {}, 0)] * 3
        with self.assertRaises(LLMRateLimitError):
            self.client().complete("s", MESAJ)

    def test_kalici_hata_yeniden_denenmez_ve_anahtar_sizmaz(self):
        self.srv.script.append((401, {"error": {"message": "invalid x-api-key"}}, {}, 0))
        with self.assertRaises(LLMAPIError) as e:
            self.client().complete("s", MESAJ)
        self.assertEqual(e.exception.status_code, 401)
        self.assertEqual(len(self.srv.requests), 1)
        self.assertNotIn(GIZLI, str(e.exception))

    def test_zaman_asimi(self):
        self.srv.script += [(200, {}, {}, 0.6)] * 2
        with self.assertRaises(LLMTimeoutError):
            self.client(timeout=0.15, max_retries=1).complete("s", MESAJ)
        self.assertEqual(len(self.srv.requests), 2)

    def test_baglanti_kurulamazsa(self):
        c = ClaudeClient(api_key=GIZLI, base_url="http://127.0.0.1:1", max_retries=1, sleep=self.sleeps.append)
        with self.assertRaises(LLMAPIError) as e:
            c.complete("s", MESAJ)
        self.assertIn("bağlanılamadı", str(e.exception))
        self.assertEqual(len(self.sleeps), 1)

    def test_bozuk_ve_bos_yanitlar(self):
        self.srv.script.append((200, "json-degil", {}, 0))
        with self.assertRaises(LLMAPIError):
            self.client().complete("s", MESAJ)
        self.srv.script.append((200, {"content": []}, {}, 0))
        with self.assertRaises(LLMAPIError):
            self.client().complete("s", MESAJ)
        self.srv.script.append((200, {"baska": 1}, {}, 0))
        with self.assertRaises(LLMAPIError):
            self.client().complete("s", MESAJ)

    def test_anahtar_yoksa_ag_cagrisi_yapilmaz(self):
        with self.assertRaises(LLMConfigError):
            self.client(api_key="").complete("s", MESAJ)
        self.assertEqual(self.srv.requests, [])

    def test_gecersiz_mesajlar(self):
        c = self.client()
        for kotu in ([], "metin", [{"role": "system", "content": "x"}], [{"role": "user", "content": ""}],
                     [{"role": "assistant", "content": "x"}], [{"role": "user"}]):
            with self.assertRaises(ValueError):
                c.complete("s", kotu)
        self.assertEqual(self.srv.requests, [])


class HataEslemeVeAdminTests(unittest.TestCase):
    def test_http_kodlari(self):
        self.assertEqual(errors.llm_http_error(LLMConfigError("x")).status_code, 503)
        self.assertEqual(errors.llm_http_error(LLMTimeoutError("x")).status_code, 504)
        self.assertEqual(errors.llm_http_error(LLMRateLimitError("x")).status_code, 429)
        self.assertEqual(errors.llm_http_error(LLMAPIError("x", 500)).status_code, 502)

    class Sahte:
        model = "sahte-model"

        def __init__(self, sonuc):
            self.sonuc = sonuc

        def complete(self, system, messages, max_tokens=None):
            if isinstance(self.sonuc, Exception):
                raise self.sonuc
            return self.sonuc

    def test_llm_test_ucu(self):
        out = admin_api.llm_test(admin_api.LLMTestRequest(prompt="Selam"), {"role": "admin"}, self.Sahte("Merhaba"))
        self.assertEqual(out, {"model": "sahte-model", "answer": "Merhaba"})
        with self.assertRaises(HTTPException) as e:
            admin_api.llm_test(admin_api.LLMTestRequest(prompt="x"), {"role": "admin"}, self.Sahte(LLMConfigError("anahtar yok")))
        self.assertEqual(e.exception.status_code, 503)
        with self.assertRaises(HTTPException) as e:
            admin_api.llm_test(admin_api.LLMTestRequest(prompt="  "), {"role": "admin"}, self.Sahte(ValueError("bos")))
        self.assertEqual(e.exception.status_code, 400)


class AnahtarGuvenligiTests(unittest.TestCase):
    def test_anahtar_koda_gomulu_degil(self):
        from pathlib import Path
        kok = Path(__file__).resolve().parents[1]
        from scripts.env_olustur import SABLON
        for p in list((kok / "app").rglob("*.py")) + list((kok / "scripts").rglob("*.py")):
            metin = p.read_text(encoding="utf-8")
            self.assertNotIn("sk-ant-", metin, f"{p.name}: gercek anahtar gibi gorunen deger")
        self.assertIn("ANTHROPIC_API_KEY=\n", SABLON)


if __name__ == "__main__":
    unittest.main()
