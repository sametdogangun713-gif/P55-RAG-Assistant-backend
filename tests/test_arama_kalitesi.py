"""Bulutta arama/yanit kalitesi icin secilen varsayilanlar (olcum: docs/istem-deneyleri/istem-deneyleri.md, "Bulut kalitesi").

Gercek hata: Hugging Face MiniLM'i 128 token'da kesiyordu; Turkce 600 karakterlik parcanin ikinci yarisi
aranamiyordu ve "Odev teslim tarihi ne zaman?" sorusu belgede yazdigi halde "bilgi bulamadim" aliyordu.
config degerleri import aninda okundugu icin varsayilanlar ayri bir Python surecinde denetlenir.
"""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from app.services import prompts

KOK = Path(__file__).resolve().parent.parent


def varsayilanlar(backend: str) -> dict:
    env = {k: v for k, v in os.environ.items()
           if k not in ("EMBEDDING_MODEL", "MIN_SCORE", "GROQ_REASONING_EFFORT")}
    # .env dosyasindaki degerler varsayilani ezmesin: bos deger "ayarlanmamis" demektir (load_dotenv ezmez)
    env.update({"EMBEDDING_BACKEND": backend, "EMBEDDING_MODEL": "", "MIN_SCORE": "", "GROQ_REASONING_EFFORT": ""})
    kod = ("import json; from app.core import config as c; print(json.dumps({'model': c.EMBEDDING_MODEL, "
           "'esik': c.MIN_SCORE}))")
    out = subprocess.run([sys.executable, "-c", kod], cwd=KOK, env=env, capture_output=True, text=True, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


class TestBulutVarsayilanlari(unittest.TestCase):
    def test_hf_bge_m3_kullanir(self):
        d = varsayilanlar("hf")
        self.assertEqual(d["model"], "BAAI/bge-m3")      # 8192 token; MiniLM sunucuda 128'de kesiliyordu
        self.assertEqual(d["esik"], 0.40)                # bge-m3 olcumu: belgede olan sorularda en iyi skor >= 0,55

    def test_gemini_esigi_olcumle_secildi(self):
        # Gemini olcumu: belgede olan sorularda en iyi skor >= 0,686, ilgisizler 0,58-0,66 -> 0,55 dogru soruyu kesmez
        self.assertEqual(varsayilanlar("gemini")["esik"], 0.55)

    def test_yerel_model_degismedi(self):
        d = varsayilanlar("local")
        self.assertEqual(d["model"], "paraphrase-multilingual-MiniLM-L12-v2")
        self.assertEqual(d["esik"], 0.30)

    def test_bos_ortam_degiskeni_varsayilani_secer(self):
        # Vercel'de EMBEDDING_MODEL hic yazilmazsa ya da bos birakilirsa bge-m3 secilmeli
        self.assertEqual(varsayilanlar("hf")["model"], "BAAI/bge-m3")


class TestIstemV2(unittest.TestCase):
    def test_surum(self):
        self.assertEqual(prompts.PROMPT_VERSION, "rag-v2")

    def test_kismi_yanit_kurali_ve_bilgi_yok_yalnizca_ilgisizse(self):
        s = prompts.SYSTEM_PROMPT
        self.assertIn("farklı kelimelerle", s)
        self.assertIn("HİÇBİRİ soruyla ilgili değilse", s)
        self.assertNotIn("yetersizse", s)                # v1'deki asiri temkinli ifade geri gelmesin
        self.assertIn(prompts.NO_INFO_MARKER, s)
        self.assertIn("VERİDİR", s)                     # prompt injection kurali korunuyor


if __name__ == "__main__":
    unittest.main()
