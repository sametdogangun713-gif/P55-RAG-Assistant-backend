"""Hafta 14: kurulum kolayligi ve dokumantasyon tutarliligi testleri."""
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import env_olustur

KOK = Path(__file__).resolve().parent.parent


class EnvOlusturTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_env_olusur_ve_gizli_anahtar_uretilir(self):
        self.assertTrue(env_olustur.olustur(self.dir))
        metin = (self.dir / ".env").read_text(encoding="utf-8")
        anahtar = re.search(r"(?m)^SECRET_KEY=(.*)$", metin).group(1)
        self.assertRegex(anahtar, r"^[0-9a-f]{64}$")              # 32 bayt rastgele, hex
        self.assertIn("ANTHROPIC_API_KEY=\n", metin)                # API anahtari BOS kalir

    def test_her_seferinde_farkli_anahtar(self):
        env_olustur.olustur(self.dir)
        ilk = (self.dir / ".env").read_text(encoding="utf-8")
        (self.dir / ".env").unlink()
        env_olustur.olustur(self.dir)
        self.assertNotEqual(ilk, (self.dir / ".env").read_text(encoding="utf-8"))

    def test_var_olan_env_e_dokunulmaz(self):
        (self.dir / ".env").write_text("ANTHROPIC_API_KEY=benim-anahtarim\n", encoding="utf-8")
        self.assertFalse(env_olustur.olustur(self.dir))
        self.assertEqual((self.dir / ".env").read_text(encoding="utf-8"), "ANTHROPIC_API_KEY=benim-anahtarim\n")


class BelgeTutarlilikTests(unittest.TestCase):
    def test_env_sablonu_ve_readme_degiskenleri_kodda_okunuyor(self):
        """.env sablonundaki ve README ayar tablosundaki her degisken config.py'de gercekten okunuyor mu?
        (unutulmus/yazim hatali ayar kalmasin)"""
        degiskenler = re.findall(r"(?m)^([A-Z_]+)=", env_olustur.SABLON)
        readme = (KOK / "README.md").read_text(encoding="utf-8")
        degiskenler += re.findall(r"(?m)^\| `([A-Z][A-Z0-9_]+)`", readme)
        self.assertIn("MAX_API_TOKENS_PER_USER", degiskenler)
        config = (KOK / "app" / "core" / "config.py").read_text(encoding="utf-8")
        eksik = sorted({d for d in degiskenler if f'"{d}"' not in config})
        self.assertEqual(eksik, [])


    def test_bat_dosyalari_crlf_ve_ascii(self):
        """Windows cmd, LF satir sonlu .bat dosyalarinda etiketleri (goto) yanlis okuyabilir."""
        for ad in ("testleri_calistir.bat",):
            veri = (KOK / ad).read_bytes()
            self.assertTrue(all(b < 128 for b in veri), f"{ad}: ASCII disi karakter")
            self.assertNotIn(b"\n", veri.replace(b"\r\n", b""), f"{ad}: CRLF olmayan satir sonu")

    def test_readme_kurulum_adimlarini_iceriyor(self):
        readme = (KOK / "README.md").read_text(encoding="utf-8")
        for parca in ("uvicorn app.main:app", "testleri_calistir.bat", "requirements.txt", "requirements-dev.txt",
                      "scripts.env_olustur", "scripts.create_admin", "pytest", "ANTHROPIC_API_KEY"):
            self.assertIn(parca, readme)
        self.assertNotIn("KULLANICI_ADIN", readme)


if __name__ == "__main__":
    unittest.main()
