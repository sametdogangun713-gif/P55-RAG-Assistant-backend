"""Hafta 14: parola sifirlama (sifremi unuttum) - kod uretimi, dogrulama, sinirlar, e-posta ve HTTP uclari."""
import os
import shutil
import tempfile
import unittest
from unittest import mock

from app.core import config, security
from app.db import email_codes, users
from app.services import auth, mailer, password_reset
from tests.helpers import make_conn

try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None

PAROLA = "eskiParola1"
YENI = "yeniParola2"
SIMDI = 1_800_000_000


class Ayar:
    """config degerlerini gecici olarak degistirir (with blogu)."""

    def __init__(self, **degerler):
        self.degerler = degerler

    def __enter__(self):
        self.eski = {k: getattr(config, k) for k in self.degerler}
        for k, v in self.degerler.items():
            setattr(config, k, v)

    def __exit__(self, *exc):
        for k, v in self.eski.items():
            setattr(config, k, v)


class SifirlamaServisiTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        self.user = auth.register_user(self.conn, "unutkan@example.com", PAROLA)
        auth.reset_failed_attempts()

    def kod_al(self, simdi=SIMDI, email="unutkan@example.com"):
        sonuc = password_reset.request_reset(self.conn, email, now=simdi)
        self.assertIsNotNone(sonuc)
        return sonuc[1]

    def test_kod_alti_haneli_ve_duz_metin_saklanmaz(self):
        kod = self.kod_al()
        self.assertRegex(kod, r"^\d{6}$")
        satir = email_codes.get_latest(self.conn, self.user["id"], "reset")
        self.assertNotIn(kod, satir["code_hash"])
        self.assertEqual(satir["expires_at"], SIMDI + config.RESET_CODE_MINUTES * 60)

    def test_kayitli_olmayan_eposta_icin_kod_uretilmez(self):
        self.assertIsNone(password_reset.request_reset(self.conn, "yok@example.com", now=SIMDI))
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM email_codes").fetchone()[0], 0)

    def test_eposta_buyuk_kucuk_harf_ve_bosluk_farki_onemsiz(self):
        kod = self.kod_al(email="  Unutkan@Example.com ")
        password_reset.reset_password(self.conn, "UNUTKAN@example.com", kod, YENI, now=SIMDI + 10)
        self.assertTrue(auth.login(self.conn, "unutkan@example.com", YENI)["access_token"])

    def test_dogru_kodla_parola_degisir_eski_parola_gecmez(self):
        kod = self.kod_al()
        password_reset.reset_password(self.conn, "unutkan@example.com", kod, YENI, now=SIMDI + 60)
        self.assertTrue(auth.login(self.conn, "unutkan@example.com", YENI)["access_token"])
        with self.assertRaises(auth.InvalidCredentialsError):
            auth.login(self.conn, "unutkan@example.com", PAROLA)

    def test_kod_tek_kullanimlik(self):
        kod = self.kod_al()
        password_reset.reset_password(self.conn, "unutkan@example.com", kod, YENI, now=SIMDI + 5)
        with self.assertRaises(password_reset.InvalidResetCodeError):
            password_reset.reset_password(self.conn, "unutkan@example.com", kod, "baskaParola3", now=SIMDI + 6)

    def test_suresi_dolan_kod_reddedilir(self):
        kod = self.kod_al()
        gec = SIMDI + config.RESET_CODE_MINUTES * 60 + 1
        with self.assertRaises(password_reset.InvalidResetCodeError):
            password_reset.reset_password(self.conn, "unutkan@example.com", kod, YENI, now=gec)

    def test_bes_yanlis_denemeden_sonra_dogru_kod_da_gecmez(self):
        """Kaba kuvvet onlemi: 6 hane = 1 milyon olasilik; 5 denemede sansla bulma olasiligi 1/200 000."""
        kod = self.kod_al()
        yanlis = f"{(int(kod) + 1) % 1_000_000:06d}"
        for _ in range(config.RESET_MAX_ATTEMPTS):
            with self.assertRaises(password_reset.InvalidResetCodeError):
                password_reset.reset_password(self.conn, "unutkan@example.com", yanlis, YENI, now=SIMDI + 1)
        with self.assertRaises(password_reset.InvalidResetCodeError):
            password_reset.reset_password(self.conn, "unutkan@example.com", kod, YENI, now=SIMDI + 2)

    def test_zayif_yeni_parola_kodu_harcamaz(self):
        kod = self.kod_al()
        with self.assertRaises(auth.ValidationError):
            password_reset.reset_password(self.conn, "unutkan@example.com", kod, "kisa", now=SIMDI + 1)
        password_reset.reset_password(self.conn, "unutkan@example.com", kod, YENI, now=SIMDI + 2)

    def test_sik_istekte_yeni_kod_uretilmez_sure_dolunca_uretilir(self):
        ilk = self.kod_al()
        self.assertIsNone(password_reset.request_reset(self.conn, "unutkan@example.com", now=SIMDI + 10))
        ikinci = self.kod_al(simdi=SIMDI + config.RESET_RESEND_SECONDS)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM email_codes").fetchone()[0], 1)
        if ilk != ikinci:                       # yeni kod gelince eskisi gecersiz
            with self.assertRaises(password_reset.InvalidResetCodeError):
                password_reset.reset_password(self.conn, "unutkan@example.com", ilk, YENI, now=SIMDI + 61)

    def test_sifirlama_giris_kilidini_kaldirir(self):
        for _ in range(config.MAX_FAILED_LOGINS):
            with self.assertRaises(auth.InvalidCredentialsError):
                auth.login(self.conn, "unutkan@example.com", "yanlisParola9")
        with self.assertRaises(auth.AccountLockedError):
            auth.login(self.conn, "unutkan@example.com", PAROLA)
        kod = self.kod_al()
        password_reset.reset_password(self.conn, "unutkan@example.com", kod, YENI, now=SIMDI + 1)
        self.assertTrue(auth.login(self.conn, "unutkan@example.com", YENI)["access_token"])

    def test_kullanici_silinince_kodlari_da_silinir(self):
        self.kod_al()
        users.delete_user(self.conn, self.user["id"])
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM email_codes").fetchone()[0], 0)

    def test_parola_ozeti_yeni_parolayla_dogrulanir(self):
        kod = self.kod_al()
        password_reset.reset_password(self.conn, "unutkan@example.com", kod, YENI, now=SIMDI + 1)
        ozet = users.get_user_by_id(self.conn, self.user["id"])["password_hash"]
        self.assertTrue(security.verify_password(YENI, ozet))
        self.assertNotIn(YENI, ozet)


class EpostaTests(unittest.TestCase):
    def test_smtp_yoksa_gelistirmede_konsola_uretimde_hicbir_yere(self):
        with Ayar(SMTP_HOST="", APP_ENV="development"), mock.patch("builtins.print") as yaz:
            self.assertTrue(mailer.can_deliver())
            mailer.send_reset_code("a@example.com", "123456")
            self.assertIn("123456", yaz.call_args[0][0])
        with Ayar(SMTP_HOST="", APP_ENV="production"), mock.patch("builtins.print") as yaz:
            self.assertFalse(mailer.can_deliver())
            mailer.send_reset_code("a@example.com", "123456")
            yaz.assert_not_called()

    def test_smtp_ayarliysa_starttls_ile_gonderir(self):
        ayar = dict(SMTP_HOST="smtp.example.com", SMTP_PORT=587, SMTP_USER="gonderen@example.com",
                    SMTP_PASSWORD="test-uygulama-sifresi", SMTP_FROM="")
        with Ayar(**ayar), mock.patch("smtplib.SMTP") as smtp:
            mailer.send_reset_code("alici@example.com", "654321")
        s = smtp.return_value.__enter__.return_value
        s.starttls.assert_called_once()
        s.login.assert_called_once_with("gonderen@example.com", "test-uygulama-sifresi")
        mesaj = s.send_message.call_args[0][0]
        self.assertEqual(mesaj["To"], "alici@example.com")
        self.assertEqual(mesaj["From"], "gonderen@example.com")
        self.assertIn("654321", mesaj.get_content())

    def test_smtp_hatasi_uygulamayi_cokertmez(self):
        ayar = dict(SMTP_HOST="smtp.example.com", SMTP_PORT=587, SMTP_USER="u@example.com", SMTP_PASSWORD="x")
        with Ayar(**ayar), mock.patch("smtplib.SMTP", side_effect=OSError("baglanti yok")):
            with self.assertLogs("asistan.mailer", level="ERROR"):
                mailer.send_reset_code("alici@example.com", "111111")


@unittest.skipIf(TestClient is None, "TestClient (httpx) kurulu degil")
class SifirlamaHttpTests(unittest.TestCase):
    def setUp(self):
        from app.main import app
        self.tmp = tempfile.mkdtemp()
        self._ayar = Ayar(DATABASE_URL="sqlite:///" + os.path.join(self.tmp, "t.db"),
                          UPLOAD_DIR=os.path.join(self.tmp, "up"), SMTP_HOST="", APP_ENV="development")
        self._ayar.__enter__()
        auth.reset_failed_attempts()
        self._client = TestClient(app)
        self.client = self._client.__enter__()
        self.client.post("/auth/register", json={"full_name": "Deneme Kullanıcı", "email": "http@example.com", "password": PAROLA})
        self.gonderilen = []
        self._yama = mock.patch.object(mailer, "send_reset_code", side_effect=lambda e, k: self.gonderilen.append((e, k)))
        self._yama.start()

    def tearDown(self):
        self._yama.stop()
        self._client.__exit__(None, None, None)
        self._ayar.__exit__()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_kayitli_ve_kayitsiz_eposta_ayni_yaniti_alir(self):
        a = self.client.post("/auth/forgot-password", json={"email": "http@example.com"})
        b = self.client.post("/auth/forgot-password", json={"email": "kimseyok@example.com"})
        self.assertEqual((a.status_code, a.json()), (b.status_code, b.json()))
        self.assertEqual(len(self.gonderilen), 1)                     # yalnizca kayitli olana e-posta gider
        self.assertNotIn(self.gonderilen[0][1], a.text)               # kod HTTP yanitinda ASLA yok

    def test_uctan_uca_sifirlama_ve_yeni_parolayla_giris(self):
        self.client.post("/auth/forgot-password", json={"email": "http@example.com"})
        kod = self.gonderilen[0][1]
        r = self.client.post("/auth/reset-password", json={"email": "http@example.com", "code": "000000" if kod != "000000" else "111111", "new_password": YENI})
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/auth/reset-password", json={"email": "http@example.com", "code": kod, "new_password": YENI})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.client.post("/auth/login", json={"email": "http@example.com", "password": PAROLA}).status_code, 401)
        self.assertEqual(self.client.post("/auth/login", json={"email": "http@example.com", "password": YENI}).status_code, 200)

    def test_uretimde_smtp_yoksa_503(self):
        with Ayar(APP_ENV="production"):
            r = self.client.post("/auth/forgot-password", json={"email": "http@example.com"})
        self.assertEqual(r.status_code, 503)
        self.assertEqual(self.gonderilen, [])


if __name__ == "__main__":
    unittest.main()
