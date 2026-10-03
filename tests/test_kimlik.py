"""Hafta 5 testleri: parola hash, token, kayit/giris kurallari, rol kontrolu."""
import time
import unittest

import jwt
from fastapi import HTTPException

from app.api import admin as admin_api
from app.api import auth as auth_api
from app.api import deps
from app.core import config, security
from app.db import users
from app.services import auth
from tests.helpers import make_conn

PAROLA = "Guclu1234"


class ParolaTests(unittest.TestCase):
    def test_duz_metin_saklanmaz_ve_tuzlu(self):
        h1, h2 = security.hash_password(PAROLA), security.hash_password(PAROLA)
        self.assertNotIn(PAROLA, h1)
        self.assertNotEqual(h1, h2)  # farkli tuz -> farkli hash
        self.assertTrue(h1.startswith("scrypt$"))

    def test_dogrulama(self):
        h = security.hash_password(PAROLA)
        self.assertTrue(security.verify_password(PAROLA, h))
        self.assertFalse(security.verify_password("yanlis", h))
        self.assertFalse(security.verify_password(PAROLA, "bozuk-hash"))
        self.assertFalse(security.verify_password(PAROLA, "bcrypt$1$2$3$4$5"))


class TokenTests(unittest.TestCase):
    def test_gidis_donus(self):
        t = security.create_access_token(7, "user")
        p = security.decode_access_token(t)
        self.assertEqual((p["sub"], p["role"]), ("7", "user"))

    def test_suresi_dolmus_token_reddedilir(self):
        t = security.create_access_token(1, "user", expires_minutes=-1)
        with self.assertRaises(security.TokenError):
            security.decode_access_token(t)

    def test_bozulmus_ve_baska_anahtarla_imzali_reddedilir(self):
        t = security.create_access_token(1, "user")
        with self.assertRaises(security.TokenError):
            security.decode_access_token(t[:-3] + "abc")
        yabanci = jwt.encode({"sub": "1", "exp": int(time.time()) + 60}, "baska-anahtar", algorithm="HS256")
        with self.assertRaises(security.TokenError):
            security.decode_access_token(yabanci)

    def test_alg_none_saldirisi_reddedilir(self):
        t = jwt.encode({"sub": "1", "exp": int(time.time()) + 60}, key=None, algorithm="none")
        with self.assertRaises(security.TokenError):
            security.decode_access_token(t)


class KayitGirisTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        auth.reset_failed_attempts()

    def test_kayit_basarili_ve_e_posta_normalize(self):
        u = auth.register_user(self.conn, "  Ali@Example.COM ", PAROLA)
        self.assertEqual(u["email"], "ali@example.com")
        self.assertEqual(u["role"], "user")
        self.assertNotIn(PAROLA, users.get_user_by_id(self.conn, u["id"])["password_hash"])

    def test_kayit_dogrulamalari(self):
        for email, pw in [("gecersiz", PAROLA), ("a@b", PAROLA), ("a@example.com", "kisa1"),
                          ("a@example.com", "sadeceharfler"), ("a@example.com", "12345678")]:
            with self.assertRaises(auth.ValidationError):
                auth.register_user(self.conn, email, pw)

    def test_ayni_e_posta_ikinci_kez_kayit_olmaz(self):
        auth.register_user(self.conn, "a@example.com", PAROLA)
        with self.assertRaises(auth.DuplicateUserError):
            auth.register_user(self.conn, "A@EXAMPLE.com", PAROLA)

    def test_giris_ve_genel_hata_mesaji(self):
        auth.register_user(self.conn, "a@example.com", PAROLA)
        r = auth.login(self.conn, "a@example.com", PAROLA)
        self.assertIn("access_token", r)
        with self.assertRaises(auth.InvalidCredentialsError) as e1:
            auth.login(self.conn, "a@example.com", "Yanlis1234")
        with self.assertRaises(auth.InvalidCredentialsError) as e2:
            auth.login(self.conn, "yok@example.com", PAROLA)
        self.assertEqual(str(e1.exception), str(e2.exception))  # kullanici numaralandirma yok

    def test_cok_basarisiz_denemeden_sonra_kilit(self):
        auth.register_user(self.conn, "a@example.com", PAROLA)
        for _ in range(config.MAX_FAILED_LOGINS):
            with self.assertRaises(auth.InvalidCredentialsError):
                auth.login(self.conn, "a@example.com", "Yanlis1234")
        with self.assertRaises(auth.AccountLockedError):
            auth.login(self.conn, "a@example.com", PAROLA)  # dogru parola bile kilitli

    def test_basarili_giris_sayaci_sifirlar(self):
        auth.register_user(self.conn, "a@example.com", PAROLA)
        for _ in range(config.MAX_FAILED_LOGINS - 1):
            with self.assertRaises(auth.InvalidCredentialsError):
                auth.login(self.conn, "a@example.com", "Yanlis1234")
        auth.login(self.conn, "a@example.com", PAROLA)
        with self.assertRaises(auth.InvalidCredentialsError):
            auth.login(self.conn, "a@example.com", "Yanlis1234")  # kilit degil, sadece hata


class ApiUcNoktaTests(unittest.TestCase):
    """Uc nokta fonksiyonlarini dogrudan cagirir (HTTP katmani olmadan)."""

    def setUp(self):
        self.conn = make_conn()
        auth.reset_failed_attempts()

    def _giris(self, email="a@example.com", role="user"):
        auth.register_user(self.conn, email, PAROLA, role=role)
        r = auth_api.login(auth_api.Credentials(email=email, password=PAROLA), self.conn)
        return "Bearer " + r["access_token"]

    def test_register_login_me_akisi(self):
        out = auth_api.register(auth_api.Credentials(email="b@example.com", password=PAROLA), self.conn)
        self.assertNotIn("password_hash", out)
        bearer = self._giris("c@example.com")
        user = deps.get_current_user(authorization=bearer, conn=self.conn)
        self.assertEqual(auth_api.me(user)["email"], "c@example.com")

    def test_register_hata_kodlari(self):
        with self.assertRaises(HTTPException) as e:
            auth_api.register(auth_api.Credentials(email="x", password=PAROLA), self.conn)
        self.assertEqual(e.exception.status_code, 400)
        auth_api.register(auth_api.Credentials(email="d@example.com", password=PAROLA), self.conn)
        with self.assertRaises(HTTPException) as e:
            auth_api.register(auth_api.Credentials(email="d@example.com", password=PAROLA), self.conn)
        self.assertEqual(e.exception.status_code, 409)

    def test_yanlis_giris_401(self):
        auth.register_user(self.conn, "e@example.com", PAROLA)
        with self.assertRaises(HTTPException) as e:
            auth_api.login(auth_api.Credentials(email="e@example.com", password="Yanlis1234"), self.conn)
        self.assertEqual(e.exception.status_code, 401)

    def test_korumali_uc_noktada_token_sart(self):
        for baslik in [None, "", "Basic abc", "Bearer bozuk.token.degeri"]:
            with self.assertRaises(HTTPException) as e:
                deps.get_current_user(authorization=baslik, conn=self.conn)
            self.assertEqual(e.exception.status_code, 401)

    def test_silinmis_kullanicinin_tokeni_gecersiz(self):
        bearer = self._giris("f@example.com")
        user = deps.get_current_user(authorization=bearer, conn=self.conn)
        users.delete_user(self.conn, user["id"])
        with self.assertRaises(HTTPException) as e:
            deps.get_current_user(authorization=bearer, conn=self.conn)
        self.assertEqual(e.exception.status_code, 401)

    def test_rol_kontrolu_sunucuda(self):
        user = deps.get_current_user(authorization=self._giris("g@example.com"), conn=self.conn)
        with self.assertRaises(HTTPException) as e:
            deps.require_admin(user)
        self.assertEqual(e.exception.status_code, 403)
        adm = deps.get_current_user(authorization=self._giris("h@example.com", "admin"), conn=self.conn)
        self.assertEqual(deps.require_admin(adm)["email"], "h@example.com")
        liste = admin_api.list_all_users(adm, self.conn)
        self.assertTrue(all("password_hash" not in u for u in liste))

    def test_token_icindeki_rol_iddiasi_yetki_vermez(self):
        # Normal kullanici icin 'admin' rollu (gecerli imzali) token uretilse bile yetki DB'den okunur
        u = auth.register_user(self.conn, "i@example.com", PAROLA)
        sahte = "Bearer " + security.create_access_token(u["id"], "admin")
        user = deps.get_current_user(authorization=sahte, conn=self.conn)
        with self.assertRaises(HTTPException):
            deps.require_admin(user)


if __name__ == "__main__":
    unittest.main()
