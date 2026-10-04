"""Kisisel API anahtari: uretme, ozetle saklama, sure, sinir, iptal ve 3. parti uygulamanin anahtarla baglanmasi."""
import os
import shutil
import tempfile
import unittest
from unittest import mock

from app.core import config
from app.db import api_tokens as repo
from app.services import api_tokens, auth
from tests.helpers import make_conn
from tests.test_sifre_sifirlama import Ayar

try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None

PAROLA = "Guclu1234"
GUN = 86400


class AnahtarServisiTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        self.user = auth.register_user(self.conn, "anahtar@example.com", PAROLA)

    def test_anahtar_onekli_ve_yalnizca_ozeti_saklanir(self):
        yeni = api_tokens.create_token(self.conn, self.user, "Postman")
        token = yeni["token"]
        self.assertTrue(token.startswith("p55_"))
        self.assertGreaterEqual(len(token), 40)
        self.assertEqual(yeni["prefix"], token[:12])
        satir = repo.get_by_hash(self.conn, api_tokens.hash_token(token))
        self.assertNotIn(token, satir.values())                       # anahtarin kendisi veritabaninda yok
        self.assertNotIn("token_hash", yeni)
        liste = api_tokens.list_tokens(self.conn, self.user)
        self.assertEqual([t["name"] for t in liste], ["Postman"])
        self.assertNotIn("token", liste[0])                           # bir daha gosterilmez
        self.assertNotIn("token_hash", liste[0])

    def test_her_anahtar_farkli(self):
        a = api_tokens.create_token(self.conn, self.user, "A")["token"]
        b = api_tokens.create_token(self.conn, self.user, "B")["token"]
        self.assertNotEqual(a, b)

    def test_dogrulama_sahibini_dondurur_yanlis_anahtar_none(self):
        token = api_tokens.create_token(self.conn, self.user, "Betik")["token"]
        self.assertEqual(api_tokens.authenticate(self.conn, token)["id"], self.user["id"])
        self.assertIsNone(api_tokens.authenticate(self.conn, token[:-1] + ("A" if token[-1] != "A" else "B")))
        self.assertIsNone(api_tokens.authenticate(self.conn, "p55_"))

    def test_suresi_dolan_anahtar_gecersiz(self):
        simdi = 1_800_000_000
        with mock.patch.object(api_tokens, "_now", return_value=simdi):
            yeni = api_tokens.create_token(self.conn, self.user, "Kisa", expires_in_days=7)
        with mock.patch.object(api_tokens, "_now", return_value=simdi + 7 * GUN - 60):
            self.assertIsNotNone(api_tokens.authenticate(self.conn, yeni["token"]))
        with mock.patch.object(api_tokens, "_now", return_value=simdi + 7 * GUN):
            self.assertIsNone(api_tokens.authenticate(self.conn, yeni["token"]))
            self.assertTrue(api_tokens.list_tokens(self.conn, self.user)[0]["expired"])

    def test_son_kullanim_dakikada_bir_yazilir(self):
        simdi = 1_800_000_000
        with mock.patch.object(api_tokens, "_now", return_value=simdi):
            token = api_tokens.create_token(self.conn, self.user, "Saat")["token"]
            self.assertIsNone(api_tokens.list_tokens(self.conn, self.user)[0]["last_used_at"])
            api_tokens.authenticate(self.conn, token)
        ilk = api_tokens.list_tokens(self.conn, self.user)[0]["last_used_at"]
        self.assertIsNotNone(ilk)
        with mock.patch.object(api_tokens, "_now", return_value=simdi + 120), \
                mock.patch.object(repo, "touch", wraps=repo.touch) as yaz:
            api_tokens.authenticate(self.conn, token)
            api_tokens.authenticate(self.conn, token)               # ayni dakika: ikinci kez yazilmaz
        self.assertEqual(yaz.call_count, 1)

    def test_ad_ve_sure_dogrulanir(self):
        for ad in ("", "   ", "x" * 61):
            with self.assertRaises(api_tokens.TokenValidationError):
                api_tokens.create_token(self.conn, self.user, ad)
        for gun in (0, 1, -7, 366, 100000):
            with self.assertRaises(api_tokens.TokenValidationError):
                api_tokens.create_token(self.conn, self.user, "Ad", expires_in_days=gun)
        self.assertEqual(api_tokens.create_token(self.conn, self.user, "  Çok   boşluklu  ad ")["name"], "Çok boşluklu ad")

    def test_anahtar_sayisi_sinirli(self):
        with Ayar(MAX_API_TOKENS_PER_USER=2):
            api_tokens.create_token(self.conn, self.user, "1")
            ikinci = api_tokens.create_token(self.conn, self.user, "2")
            with self.assertRaises(api_tokens.TokenLimitError):
                api_tokens.create_token(self.conn, self.user, "3")
            api_tokens.revoke_token(self.conn, self.user, ikinci["id"])
            api_tokens.create_token(self.conn, self.user, "3")           # silince yer acilir

    def test_iptal_yalnizca_sahibine_ait(self):
        baskasi = auth.register_user(self.conn, "baskasi@example.com", PAROLA)
        yeni = api_tokens.create_token(self.conn, self.user, "Benim")
        self.assertFalse(api_tokens.revoke_token(self.conn, baskasi, yeni["id"]))
        self.assertIsNotNone(api_tokens.authenticate(self.conn, yeni["token"]))
        self.assertTrue(api_tokens.revoke_token(self.conn, self.user, yeni["id"]))
        self.assertIsNone(api_tokens.authenticate(self.conn, yeni["token"]))

    def test_hesap_silinince_anahtarlar_silinir(self):
        from app.services import account
        token = api_tokens.create_token(self.conn, self.user, "Gidecek")["token"]
        account.delete_account(self.conn, self.user, PAROLA)
        self.assertIsNone(repo.get_by_hash(self.conn, api_tokens.hash_token(token)))


@unittest.skipIf(TestClient is None, "TestClient (httpx) kurulu degil")
class AnahtarHttpTests(unittest.TestCase):
    def setUp(self):
        from app.main import app
        self.tmp = tempfile.mkdtemp()
        self._ayar = Ayar(DATABASE_URL="sqlite:///" + os.path.join(self.tmp, "t.db"), UPLOAD_DIR=os.path.join(self.tmp, "up"))
        self._ayar.__enter__()
        auth.reset_failed_attempts()
        self._client = TestClient(app)
        self.c = self._client.__enter__()
        self.c.post("/auth/register", json={"full_name": "Http Kullanıcı", "email": "h@example.com", "password": PAROLA})
        tok = self.c.post("/auth/login", json={"email": "h@example.com", "password": PAROLA}).json()["access_token"]
        self.oturum = {"Authorization": "Bearer " + tok}

    def tearDown(self):
        self._client.__exit__(None, None, None)
        self._ayar.__exit__()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _anahtar_uret(self, ad="Postman", **ek):
        r = self.c.post("/auth/tokens", headers=self.oturum, json={"name": ad, **ek})
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()

    def test_ucuncu_parti_uygulama_anahtarla_baglanir(self):
        yeni = self._anahtar_uret()
        anahtar = {"Authorization": "Bearer " + yeni["token"]}
        r = self.c.get("/auth/me", headers=anahtar)
        self.assertEqual((r.status_code, r.json()["email"]), (200, "h@example.com"))
        self.assertEqual(self.c.get("/documents", headers=anahtar).status_code, 200)
        self.assertEqual(self.c.get("/conversations", headers=anahtar).status_code, 200)
        liste = self.c.get("/auth/tokens", headers=self.oturum).json()
        self.assertIsNotNone(liste[0]["last_used_at"])
        self.assertNotIn("token", liste[0])

    def test_iptal_edilen_anahtar_401(self):
        yeni = self._anahtar_uret()
        anahtar = {"Authorization": "Bearer " + yeni["token"]}
        r = self.c.delete(f"/auth/tokens/{yeni['id']}", headers=self.oturum)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.c.get("/auth/me", headers=anahtar).status_code, 401)
        self.assertEqual(self.c.delete(f"/auth/tokens/{yeni['id']}", headers=self.oturum).status_code, 404)
        self.assertEqual(self.c.get("/auth/me", headers={"Authorization": "Bearer p55_uydurma"}).status_code, 401)

    def test_anahtarla_hesap_yonetilemez(self):
        """Sizan anahtar yeni anahtar uretemez, parolayi degistiremez, hesabi silemez, yonetim yapamaz."""
        anahtar = {"Authorization": "Bearer " + self._anahtar_uret()["token"]}
        self.assertEqual(self.c.post("/auth/tokens", headers=anahtar, json={"name": "Kalici"}).status_code, 403)
        self.assertEqual(self.c.get("/auth/tokens", headers=anahtar).status_code, 403)
        self.assertEqual(self.c.post("/auth/change-password", headers=anahtar,
                                     json={"current_password": PAROLA, "new_password": "Yeni5678x"}).status_code, 403)
        self.assertEqual(self.c.request("DELETE", "/auth/me", headers=anahtar, json={"password": PAROLA}).status_code, 403)
        self.assertEqual(self.c.patch("/auth/me", headers=anahtar, json={"full_name": "Ele Geçirilmiş"}).status_code, 403)
        self.assertEqual(self.c.get("/admin/users", headers=anahtar).status_code, 403)

    def test_hatali_istekler(self):
        self.assertEqual(self.c.post("/auth/tokens", json={"name": "X"}).status_code, 401)
        self.assertEqual(self.c.post("/auth/tokens", headers=self.oturum, json={"name": ""}).status_code, 400)
        self.assertEqual(self.c.post("/auth/tokens", headers=self.oturum,
                                     json={"name": "X", "expires_in_days": 5}).status_code, 400)
        with Ayar(MAX_API_TOKENS_PER_USER=1):
            self._anahtar_uret("Bir", expires_in_days=30)
            self.assertEqual(self.c.post("/auth/tokens", headers=self.oturum, json={"name": "İki"}).status_code, 409)

    def test_baskasinin_anahtari_silinemez(self):
        yeni = self._anahtar_uret()
        self.c.post("/auth/register", json={"full_name": "Diğer Kişi", "email": "d@example.com", "password": PAROLA})
        tok = self.c.post("/auth/login", json={"email": "d@example.com", "password": PAROLA}).json()["access_token"]
        r = self.c.delete(f"/auth/tokens/{yeni['id']}", headers={"Authorization": "Bearer " + tok})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(self.c.get("/auth/me", headers={"Authorization": "Bearer " + yeni["token"]}).status_code, 200)


if __name__ == "__main__":
    unittest.main()
