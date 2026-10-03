"""Hesabim: ad degistirme, parola degistirme (mevcut parola sart), hesap silme (dosyalar dahil), son yonetici korumasi."""
import os
import shutil
import tempfile
import unittest

from app.core import config
from app.db import documents as documents_repo
from app.db import users
from app.services import account, auth
from tests.helpers import TempUploads, make_conn
from tests.test_sifre_sifirlama import Ayar

try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None

PAROLA = "Guclu1234"
YENI = "Yeni5678x"


class HesapServisiTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        auth.reset_failed_attempts()
        self.user = auth.register_user(self.conn, "hesap@example.com", PAROLA, full_name="Eski Ad")

    def test_ad_degisir_ve_dogrulanir(self):
        u = account.update_name(self.conn, self.user, "  Yeni   Ad ")
        self.assertEqual(u["full_name"], "Yeni Ad")
        with self.assertRaises(auth.ValidationError):
            account.update_name(self.conn, self.user, "1")

    def test_parola_degistirme_mevcut_parolayi_ister(self):
        with self.assertRaises(account.WrongPasswordError):
            account.change_password(self.conn, self.user, "Yanlis1234", YENI)
        with self.assertRaises(auth.ValidationError):
            account.change_password(self.conn, self.user, PAROLA, "kisa")
        with self.assertRaises(auth.ValidationError):
            account.change_password(self.conn, self.user, PAROLA, PAROLA)    # ayni parola
        account.change_password(self.conn, self.user, PAROLA, YENI)
        auth.login(self.conn, "hesap@example.com", YENI)
        with self.assertRaises(auth.InvalidCredentialsError):
            auth.login(self.conn, "hesap@example.com", PAROLA)

    def test_hesap_silme_parola_ister_belge_ve_dosyalari_siler(self):
        with TempUploads() as klasor:
            dosya = os.path.join(klasor, "kayit.txt")
            open(dosya, "w").close()
            documents_repo.create_document(self.conn, self.user["id"], "kayit.txt", "kayit.txt", "text/plain", 0)
            with self.assertRaises(account.WrongPasswordError):
                account.delete_account(self.conn, self.user, "Yanlis1234")
            account.delete_account(self.conn, self.user, PAROLA)
            self.assertFalse(os.path.exists(dosya))
        self.assertIsNone(users.get_user_by_id(self.conn, self.user["id"]))
        self.assertEqual(documents_repo.list_documents(self.conn, user_id=self.user["id"]), [])

    def test_son_yonetici_kendini_silemez(self):
        yonetici = auth.register_user(self.conn, "yonetici@example.com", PAROLA, role="admin")
        with self.assertRaises(account.LastAdminError):
            account.delete_account(self.conn, yonetici, PAROLA)
        ikinci = auth.register_user(self.conn, "yonetici2@example.com", PAROLA, role="admin")
        account.delete_account(self.conn, ikinci, PAROLA)               # baska yonetici varken silinebilir


@unittest.skipIf(TestClient is None, "TestClient (httpx) kurulu degil")
class HesapHttpTests(unittest.TestCase):
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
        self.h = {"Authorization": "Bearer " + tok}

    def tearDown(self):
        self._client.__exit__(None, None, None)
        self._ayar.__exit__()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_oturumsuz_erisilemez(self):
        self.assertEqual(self.c.patch("/auth/me", json={"full_name": "X Y"}).status_code, 401)
        self.assertEqual(self.c.request("DELETE", "/auth/me", json={"password": PAROLA}).status_code, 401)

    def test_ad_parola_ve_silme_uctan_uca(self):
        r = self.c.patch("/auth/me", headers=self.h, json={"full_name": "Yeni Ad"})
        self.assertEqual((r.status_code, r.json()["full_name"]), (200, "Yeni Ad"))
        r = self.c.post("/auth/change-password", headers=self.h, json={"current_password": "Yanlis1234", "new_password": YENI})
        self.assertEqual(r.status_code, 400)
        r = self.c.post("/auth/change-password", headers=self.h, json={"current_password": PAROLA, "new_password": YENI})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.c.post("/auth/login", json={"email": "h@example.com", "password": YENI}).status_code, 200)
        r = self.c.request("DELETE", "/auth/me", headers=self.h, json={"password": YENI})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.c.get("/auth/me", headers=self.h).status_code, 401)        # hesap yok


if __name__ == "__main__":
    unittest.main()
