"""Kayit ekrani: ad soyad, e-posta dogrulama kodu, dogrulanmamis hesabin giris yapamamasi, migration 005.

Diger test dosyalarinda dogrulama kapalidir (tests/__init__.py); burada her test kendisi acar.
"""
import os
import shutil
import sqlite3
import tempfile
import unittest
from unittest import mock

from app.db import database, email_codes, users
from app.services import auth, email_codes as codes_service, email_verification, mailer, password_reset
from tests.helpers import make_conn
from tests.test_sifre_sifirlama import Ayar

try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None

PAROLA = "Guclu1234"
SIMDI = 1_800_000_000


class AdSoyadTests(unittest.TestCase):
    def test_bosluklar_temizlenir_turkce_harf_kabul(self):
        self.assertEqual(auth.validate_name("  Şule   Çağlar  "), "Şule Çağlar")

    def test_gecersiz_adlar(self):
        for ad in ["", "   ", "A", "1234", "--", "a" * 101, "Ali\x00Veli", "Ali​Veli"]:
            with self.subTest(ad=ad), self.assertRaises(auth.ValidationError):
                auth.validate_name(ad)


class KayitServisiTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        auth.reset_failed_attempts()
        self._ayar = Ayar(REQUIRE_EMAIL_VERIFICATION=True)
        self._ayar.__enter__()
        self.addCleanup(self._ayar.__exit__)

    def kayit(self, ad="Deneme Kullanıcı", email="yeni@example.com", parola=PAROLA):
        return auth.sign_up(self.conn, ad, email, parola)

    def kod(self, user, simdi=SIMDI):
        k = email_verification.issue_code(self.conn, user, now=simdi)
        self.assertRegex(k, r"^\d{6}$")
        return k

    def test_hesap_dogrulanmamis_acilir_ad_kaydedilir(self):
        u = self.kayit(ad="  Ayşe   Yılmaz ")
        self.assertEqual(u["full_name"], "Ayşe Yılmaz")
        self.assertIsNone(u["email_verified_at"])
        self.assertFalse(auth.public_user(u)["email_verified"])

    def test_dogrulanmamis_hesap_giris_yapamaz_yanlis_parola_bunu_sizdirmaz(self):
        self.kayit()
        with self.assertRaises(auth.EmailNotVerifiedError):
            auth.login(self.conn, "yeni@example.com", PAROLA)
        with self.assertRaises(auth.InvalidCredentialsError):       # parola yanlissa "dogrulanmamis" denmez
            auth.login(self.conn, "yeni@example.com", "Yanlis1234")

    def test_kod_ozeti_saklanir_dogru_kodla_dogrulanir_ve_giris_acilir(self):
        u = self.kayit()
        k = self.kod(u)
        satir = email_codes.get_latest(self.conn, u["id"], "verify")
        self.assertNotIn(k, satir["code_hash"])
        dogrulanan = email_verification.verify(self.conn, "YENI@example.com ", k, now=SIMDI + 10)
        self.assertTrue(dogrulanan["email_verified_at"])
        self.assertIn("access_token", auth.login(self.conn, "yeni@example.com", PAROLA))

    def test_yanlis_kod_sayilir_bes_denemeden_sonra_dogru_kod_da_gecmez(self):
        u = self.kayit()
        k = self.kod(u)
        yanlis = "000000" if k != "000000" else "111111"
        for _ in range(5):
            with self.assertRaises(codes_service.InvalidCodeError):
                email_verification.verify(self.conn, "yeni@example.com", yanlis, now=SIMDI)
        with self.assertRaises(codes_service.InvalidCodeError):
            email_verification.verify(self.conn, "yeni@example.com", k, now=SIMDI)

    def test_suresi_dolan_kod_reddedilir(self):
        from app.core import config
        u = self.kayit()
        k = self.kod(u)
        with self.assertRaises(codes_service.InvalidCodeError):
            email_verification.verify(self.conn, "yeni@example.com", k, now=SIMDI + config.VERIFY_CODE_MINUTES * 60 + 1)

    def test_kod_tek_kullanimlik_ve_dogrulanmis_hesaba_kod_gitmez(self):
        u = self.kayit()
        k = self.kod(u)
        email_verification.verify(self.conn, "yeni@example.com", k, now=SIMDI)
        with self.assertRaises(codes_service.InvalidCodeError) as e:
            email_verification.verify(self.conn, "yeni@example.com", k, now=SIMDI)
        self.assertIn("zaten doğrulanmış", str(e.exception))
        self.assertIsNone(email_verification.request_code(self.conn, "yeni@example.com", now=SIMDI + 999))
        self.assertIsNone(email_verification.request_code(self.conn, "kimse@example.com", now=SIMDI + 999))

    def test_sik_yeniden_gonderimde_yeni_kod_uretilmez(self):
        u = self.kayit()
        self.kod(u)
        self.assertIsNone(email_verification.request_code(self.conn, "yeni@example.com", now=SIMDI + 30))
        self.assertIsNotNone(email_verification.request_code(self.conn, "yeni@example.com", now=SIMDI + 61))

    def test_dogrulanmamis_hesaba_yeniden_kayit_ad_ve_parolayi_yeniler(self):
        ilk = self.kayit(ad="Yanlış Kişi", parola="Eski12345")
        ikinci = self.kayit(ad="Gerçek Sahip", parola="Yeni12345")
        self.assertEqual(ilk["id"], ikinci["id"])
        self.assertEqual(ikinci["full_name"], "Gerçek Sahip")
        email_verification.verify(self.conn, "yeni@example.com", self.kod(ikinci), now=SIMDI)
        auth.login(self.conn, "yeni@example.com", "Yeni12345")
        with self.assertRaises(auth.InvalidCredentialsError):
            auth.login(self.conn, "yeni@example.com", "Eski12345")

    def test_dogrulanmis_hesaba_yeniden_kayit_olunamaz(self):
        u = self.kayit()
        email_verification.verify(self.conn, "yeni@example.com", self.kod(u), now=SIMDI)
        with self.assertRaises(auth.DuplicateUserError):
            self.kayit(ad="Başka Biri")

    def test_dogrulama_ve_sifirlama_kodlari_birbirini_silmez(self):
        u = self.kayit()
        k = self.kod(u)
        password_reset.request_reset(self.conn, "yeni@example.com", now=SIMDI)
        email_verification.verify(self.conn, "yeni@example.com", k, now=SIMDI)     # dogrulama kodu hala gecerli

    def test_parola_sifirlama_e_postayi_da_dogrular(self):
        self.kayit()
        _, k = password_reset.request_reset(self.conn, "yeni@example.com", now=SIMDI)
        password_reset.reset_password(self.conn, "yeni@example.com", k, "Yeni12345", now=SIMDI)
        self.assertIn("access_token", auth.login(self.conn, "yeni@example.com", "Yeni12345"))

    def test_dogrulama_kapaliyken_hesap_hemen_acilir(self):
        with Ayar(REQUIRE_EMAIL_VERIFICATION=False):
            u = self.kayit()
            self.assertTrue(u["email_verified_at"])
            auth.login(self.conn, "yeni@example.com", PAROLA)

    def test_gecersiz_kod_amaci_reddedilir(self):
        with self.assertRaises(ValueError):
            email_codes.get_latest(self.conn, 1, "baska")


class Migration005Tests(unittest.TestCase):
    def test_eski_hesaplar_dogrulanmis_sayilir_ve_password_resets_kalkar(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT)")
        for f in sorted(database.MIGRATIONS_DIR.glob("00[1-4]_*.sql")):          # 005'ten onceki durum
            conn.executescript(f.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (f.stem,))
        conn.execute("INSERT INTO users (email, password_hash) VALUES ('eski@example.com', 'x')")
        conn.commit()
        self.assertIn("005_name_and_email_verification", database.run_migrations(conn))
        eski = users.get_user_by_email(conn, "eski@example.com")
        self.assertEqual(eski["email_verified_at"], eski["created_at"])
        self.assertEqual(eski["full_name"], "")
        tablolar = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertIn("email_codes", tablolar)
        self.assertNotIn("password_resets", tablolar)


class DogrulamaEpostasiTests(unittest.TestCase):
    def test_konu_ve_kod_e_postada(self):
        mesaj = mailer.build_verification_message("alici@example.com", "246810")
        self.assertIn("doğrulama", mesaj["Subject"])
        self.assertIn("246810", mesaj.get_content())

    def test_smtp_yoksa_gelistirmede_konsola_uretimde_hicbir_yere(self):
        with Ayar(SMTP_HOST="", APP_ENV="development"), mock.patch("builtins.print") as yaz:
            mailer.send_verification_code("a@example.com", "135790")
            self.assertIn("135790", yaz.call_args[0][0])
        with Ayar(SMTP_HOST="", APP_ENV="production"), mock.patch("builtins.print") as yaz:
            mailer.send_verification_code("a@example.com", "135790")
            yaz.assert_not_called()


@unittest.skipIf(TestClient is None, "TestClient (httpx) kurulu degil")
class KayitHttpTests(unittest.TestCase):
    def setUp(self):
        from app.main import app
        self.tmp = tempfile.mkdtemp()
        self._ayar = Ayar(DATABASE_URL="sqlite:///" + os.path.join(self.tmp, "t.db"),
                          UPLOAD_DIR=os.path.join(self.tmp, "up"), SMTP_HOST="", APP_ENV="development",
                          REQUIRE_EMAIL_VERIFICATION=True, SEND_EMAIL_INLINE=False)
        self._ayar.__enter__()
        auth.reset_failed_attempts()
        self._client = TestClient(app)
        self.client = self._client.__enter__()
        self.gonderilen = []
        self._yama = mock.patch.object(mailer, "send_verification_code",
                                       side_effect=lambda e, k: self.gonderilen.append((e, k)))
        self._yama.start()

    def tearDown(self):
        self._yama.stop()
        self._client.__exit__(None, None, None)
        self._ayar.__exit__()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def kayit(self, **ek):
        govde = {"full_name": "Deneme Kullanıcı", "email": "kayit@example.com", "password": PAROLA, **ek}
        return self.client.post("/auth/register", json=govde)

    def test_ad_soyad_zorunlu(self):
        r = self.client.post("/auth/register", json={"email": "kayit@example.com", "password": PAROLA})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.kayit(full_name=" ").status_code, 400)

    def test_kayit_kod_dogrulama_ve_giris_uctan_uca(self):
        r = self.kayit()
        self.assertEqual(r.status_code, 201, r.text)
        self.assertTrue(r.json()["verification_required"])
        self.assertEqual(r.json()["full_name"], "Deneme Kullanıcı")
        self.assertNotIn("password_hash", r.json())
        self.assertEqual(len(self.gonderilen), 1)
        email, kod = self.gonderilen[0]
        self.assertNotIn(kod, r.text)                                   # kod HTTP yanitinda ASLA yok

        r = self.client.post("/auth/login", json={"email": email, "password": PAROLA})
        self.assertEqual(r.status_code, 403)
        self.assertIn("doğrulanmadı", r.json()["detail"])

        yanlis = "000000" if kod != "000000" else "111111"
        self.assertEqual(self.client.post("/auth/verify-email", json={"email": email, "code": yanlis}).status_code, 400)
        r = self.client.post("/auth/verify-email", json={"email": email, "code": kod})
        self.assertEqual(r.status_code, 200, r.text)
        h = {"Authorization": "Bearer " + r.json()["access_token"]}    # dogrulayinca dogrudan giris yapilmis olur
        me = self.client.get("/auth/me", headers=h).json()
        self.assertEqual((me["full_name"], me["email_verified"]), ("Deneme Kullanıcı", True))
        self.assertEqual(self.client.post("/auth/login", json={"email": email, "password": PAROLA}).status_code, 200)
        self.assertEqual(self.kayit().status_code, 409)

    def test_kodu_yeniden_gonder_her_durumda_ayni_yanit(self):
        self.kayit()
        self.gonderilen.clear()
        a = self.client.post("/auth/resend-verification", json={"email": "kayit@example.com"})
        b = self.client.post("/auth/resend-verification", json={"email": "kimseyok@example.com"})
        self.assertEqual((a.status_code, a.json()), (b.status_code, b.json()))
        self.assertEqual(self.gonderilen, [])          # kayittan 60 sn gecmedi: yeni kod uretilmez

    def test_uretimde_smtp_yoksa_kayit_503_ve_hesap_acilmaz(self):
        with Ayar(APP_ENV="production"):
            r = self.kayit()
        self.assertEqual(r.status_code, 503)
        self.assertEqual(self.client.post("/auth/login", json={"email": "kayit@example.com", "password": PAROLA}).status_code, 401)


if __name__ == "__main__":
    unittest.main()
