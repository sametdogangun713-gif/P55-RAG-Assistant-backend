"""Hafta 3 testleri: iskelet, depo kurallari ve ayarlar."""
import unittest
from pathlib import Path

from app.core import config

ROOT = Path(__file__).resolve().parents[1]


class IskeletTests(unittest.TestCase):
    def test_katman_klasorleri_var(self):
        for d in ["app/api", "app/services", "app/db", "app/core"]:
            self.assertTrue((ROOT / d).is_dir(), f"{d} klasoru yok")

    def test_gitignore_gizli_dosyalari_kapsiyor(self):
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".env", text.splitlines())
        self.assertIn("uploads/*", text)
        self.assertIn("data/*.db", text)

    def test_env_sablonu_gercek_anahtar_icermiyor(self):
        """.env sablonu (scripts/env_olustur.py) depoya gider: icinde gercek anahtar olmamali."""
        from scripts.env_olustur import SABLON
        for line in SABLON.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.upper().endswith(("KEY", "SECRET", "PASSWORD", "TOKEN")):
                self.assertTrue(value == "" or value == "{secret_key}",
                                f"{key} icin gercek deger yazilmis olabilir")

    def test_db_path_sqlite_url_cozumleme(self):
        eski = config.DATABASE_URL
        try:
            config.DATABASE_URL = "sqlite:///./data/test.db"
            self.assertEqual(config.db_path(), "./data/test.db")
            config.DATABASE_URL = "sqlite:///:memory:"
            self.assertEqual(config.db_path(), ":memory:")
            config.DATABASE_URL = "postgresql://x"
            with self.assertRaises(ValueError):
                config.db_path()
        finally:
            config.DATABASE_URL = eski

    def test_health_fonksiyonu(self):
        from app.main import health
        self.assertEqual(health(), {"status": "ok", "database": "sqlite"})   # testler SQLite kullanir


try:
    from fastapi.testclient import TestClient
except ImportError:  # httpx/fastapi kurulu degilse atla
    TestClient = None


@unittest.skipIf(TestClient is None, "TestClient (httpx) kurulu degil")
class HealthHttpTests(unittest.TestCase):
    def test_health_http(self):
        from app.main import app
        r = TestClient(app).get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
