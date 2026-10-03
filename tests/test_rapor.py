"""Hafta 12 testleri: toplulastirma sorgulari, bos gun doldurma, CSV guvenligi, yonetim uclari."""
import csv
import io
import os
import unittest
from datetime import date

from fastapi import HTTPException

from app.api import admin as admin_api
from app.api import reports as reports_api
from app.db import chunks as chunks_repo
from app.db import conversations as repo
from app.db import documents as documents_repo
from app.services import documents as svc
from app.services import reports
from tests.helpers import TempUploads, make_conn, make_user

BUGUN = date(2026, 10, 10)


def mesaj(conn, conv_id, rol, metin, gun, **kw):
    """Belirli bir tarihli mesaj ekler (created_at'i elle ayarlar)."""
    mid = repo.add_message(conn, conv_id, rol, metin, **kw)
    conn.execute("UPDATE messages SET created_at = ? WHERE id = ?", (f"{gun} 12:00:00", mid))
    conn.commit()
    return mid


class RaporVerisi(unittest.TestCase):
    """u1: 3 soru donemde (+1 donem disi), u2: 1 soru. Beklenen sayilar elle hesaplandi."""

    def setUp(self):
        self.conn = make_conn()
        self.u1 = make_user(self.conn, "bir@example.com")
        self.u2 = make_user(self.conn, "iki@example.com")
        self.admin = make_user(self.conn, "admin@example.com", role="admin")
        self.d1 = documents_repo.create_document(self.conn, self.u1["id"], "birinci.txt")
        self.d2 = documents_repo.create_document(self.conn, self.u1["id"], "ikinci.txt")
        documents_repo.set_status(self.conn, self.d1["id"], "indexed")
        documents_repo.set_status(self.conn, self.d2["id"], "failed", "hata")
        chunks_repo.add_chunks(self.conn, self.d1["id"], [(0, "a", None), (1, "b", None)])
        chunks_repo.add_chunks(self.conn, self.d2["id"], [(0, "c", None)])
        self.cA = chunks_repo.list_chunks(self.conn, self.d1["id"])[0]["id"]
        self.cB = chunks_repo.list_chunks(self.conn, self.d2["id"])[0]["id"]

        c1 = repo.create_conversation(self.conn, self.u1["id"])["id"]
        # 10-10: iki soru
        mesaj(self.conn, c1, "user", "q1", "2026-10-10")
        a1 = mesaj(self.conn, c1, "assistant", "r1", "2026-10-10", status="answered", grounded=True,
                   latency_ms=1000, best_score=0.6)
        repo.add_message_sources(self.conn, a1, [{"n": 1, "chunk_id": self.cA, "score": 0.6}])
        mesaj(self.conn, c1, "user", "q2", "2026-10-10")
        mesaj(self.conn, c1, "assistant", "r2", "2026-10-10", status="no_context", grounded=False,
              latency_ms=10, best_score=0.05)
        # 10-08: bir soru, iki kaynak
        mesaj(self.conn, c1, "user", "q3", "2026-10-08")
        a3 = mesaj(self.conn, c1, "assistant", "r3", "2026-10-08", status="answered", grounded=True,
                   latency_ms=2000, best_score=0.5)
        repo.add_message_sources(self.conn, a3, [{"n": 1, "chunk_id": self.cA, "score": 0.5},
                                                 {"n": 2, "chunk_id": self.cB, "score": 0.4}])
        # 10-01: donem DISI (7 gunluk pencere 10-04'ten baslar)
        mesaj(self.conn, c1, "user", "q4", "2026-10-01")
        a4 = mesaj(self.conn, c1, "assistant", "r4", "2026-10-01", status="answered", grounded=True,
                   latency_ms=500, best_score=0.9)
        repo.add_message_sources(self.conn, a4, [{"n": 1, "chunk_id": self.cA, "score": 0.9}])
        # u2: 10-09, dogrulanamayan yanit
        c2 = repo.create_conversation(self.conn, self.u2["id"])["id"]
        mesaj(self.conn, c2, "user", "q5", "2026-10-09")
        mesaj(self.conn, c2, "assistant", "r5", "2026-10-09", status="unverified", grounded=False, latency_ms=3000)


class RaporTests(RaporVerisi):
    def rapor(self, user_id, days=7):
        return reports.usage_report(self.conn, user_id, days, today=BUGUN)

    def test_kendi_verim_donem_ve_kalite(self):
        r = self.rapor(self.u1["id"])
        self.assertEqual((r["scope"], r["from"], r["to"]), ("me", "2026-10-04", "2026-10-10"))
        p = r["period"]
        self.assertEqual((p["questions"], p["answers"]), (3, 3))          # 10-01'deki donem disi
        self.assertEqual(p["by_status"], {"answered": 2, "no_context": 1, "no_info": 0, "unverified": 0, "general": 0,
                                           "unknown": 0})   # general: belge disi genel sohbet (GENERAL_CHAT)
        self.assertEqual(p["grounded_rate"], 0.667)
        self.assertEqual(p["no_answer_rate"], 0.333)
        self.assertEqual(p["avg_latency_ms"], 1003.3)
        self.assertEqual(p["avg_best_score"], 0.383)                       # (0.6 + 0.05 + 0.5) / 3

    def test_toplamlar(self):
        t = self.rapor(self.u1["id"])["totals"]
        self.assertEqual(t, {"users": None, "documents": 2, "indexed_documents": 1, "failed_documents": 1,
                             "chunks": 3, "conversations": 1})

    def test_en_cok_kullanilan_kaynaklar_yanit_sayisina_gore(self):
        s = self.rapor(self.u1["id"])["top_sources"]
        self.assertEqual([(x["filename"], x["answers"]) for x in s], [("birinci.txt", 2), ("ikinci.txt", 1)])

    def test_gunluk_seri_bos_gunleri_sifirla_doldurur(self):
        d = self.rapor(self.u1["id"])["daily"]
        self.assertEqual(len(d), 7)
        self.assertEqual([x["date"] for x in d][0], "2026-10-04")
        sozluk = {x["date"]: x["questions"] for x in d}
        self.assertEqual((sozluk["2026-10-10"], sozluk["2026-10-08"], sozluk["2026-10-05"]), (2, 1, 0))
        self.assertEqual(sum(sozluk.values()), 3)

    def test_tum_sistem_yonetici_kapsami(self):
        r = self.rapor(None)
        self.assertEqual(r["scope"], "all")
        self.assertEqual(r["period"]["questions"], 4)
        self.assertEqual(r["period"]["by_status"]["unverified"], 1)
        self.assertEqual(r["totals"]["users"], 3)

    def test_baska_kullanicinin_verisi_karismaz(self):
        r = self.rapor(self.u2["id"])
        self.assertEqual(r["period"]["questions"], 1)
        self.assertEqual(r["top_sources"], [])
        self.assertEqual(r["totals"]["documents"], 0)

    def test_veri_yoksa_oranlar_None_sifir_degil(self):
        r = self.rapor(self.admin["id"])
        p = r["period"]
        self.assertEqual((p["questions"], p["answers"]), (0, 0))
        self.assertIsNone(p["grounded_rate"])
        self.assertIsNone(p["avg_latency_ms"])
        self.assertTrue(all(x["questions"] == 0 for x in r["daily"]))

    def test_donem_siniri_ve_gecersiz_gun(self):
        self.assertEqual(self.rapor(self.u1["id"], days=10)["period"]["questions"], 4)   # 10-01 artik donem icinde
        for kotu in (0, 366):
            with self.assertRaises(ValueError):
                self.rapor(self.u1["id"], days=kotu)

    def test_eski_mesajlar_unknown_durumuna_duser(self):
        c = repo.create_conversation(self.conn, self.u2["id"])["id"]
        mesaj(self.conn, c, "assistant", "eski kayit", "2026-10-10")        # status NULL (migration oncesi)
        self.assertEqual(self.rapor(self.u2["id"])["period"]["by_status"]["unknown"], 1)


class CsvTests(RaporVerisi):
    def test_csv_icerik_ve_bom(self):
        r = reports.usage_report(self.conn, self.u1["id"], 7, today=BUGUN)
        text = reports.report_to_csv(r)
        self.assertTrue(text.startswith("\ufeff"))
        satirlar = list(csv.reader(io.StringIO(text.lstrip("\ufeff"))))
        self.assertEqual(satirlar[0], ["bölüm", "anahtar", "değer"])
        self.assertIn(["durum", "answered", "2"], satirlar)
        self.assertIn(["kaynak", "birinci.txt", "2"], satirlar)
        self.assertEqual(len([s for s in satirlar if s[0] == "günlük"]), 7)

    def test_csv_formul_enjeksiyonu_etkisiz(self):
        kotu = documents_repo.create_document(self.conn, self.u1["id"], "=HYPERLINK(\"http://x\",\"t\").txt")
        kc = chunks_repo.add_chunks(self.conn, kotu["id"], [(0, "z", None)])
        cid = chunks_repo.list_chunks(self.conn, kotu["id"])[0]["id"]
        c = repo.create_conversation(self.conn, self.u1["id"])["id"]
        mesaj(self.conn, c, "user", "q", "2026-10-10")
        a = mesaj(self.conn, c, "assistant", "r", "2026-10-10", status="answered", grounded=True, latency_ms=1)
        repo.add_message_sources(self.conn, a, [{"n": 1, "chunk_id": cid, "score": 0.5}])
        text = reports.report_to_csv(reports.usage_report(self.conn, self.u1["id"], 7, today=BUGUN))
        satirlar = list(csv.reader(io.StringIO(text.lstrip("\ufeff"))))
        kaynaklar = [s[1] for s in satirlar if s[0] == "kaynak"]
        self.assertTrue(any(k.startswith("'=HYPERLINK") for k in kaynaklar))
        self.assertFalse(any(k.startswith("=") for k in kaynaklar))


class ApiTests(RaporVerisi):
    def test_usage_kapsam_kurallari(self):
        out = reports_api.usage(7, "me", self.u1, self.conn)
        self.assertEqual(out["scope"], "me")
        with self.assertRaises(HTTPException) as e:
            reports_api.usage(7, "all", self.u1, self.conn)        # normal kullanici tum sistemi goremez
        self.assertEqual(e.exception.status_code, 403)
        self.assertEqual(reports_api.usage(7, "all", self.admin, self.conn)["scope"], "all")
        with self.assertRaises(HTTPException) as e:
            reports_api.usage(7, "baska", self.u1, self.conn)
        self.assertEqual(e.exception.status_code, 400)

    def test_csv_ucu_baslik_ve_icerik(self):
        resp = reports_api.usage_csv(7, "me", self.u1, self.conn)
        self.assertTrue(resp.media_type.startswith("text/csv"))
        self.assertIn("attachment", resp.headers["Content-Disposition"])
        self.assertTrue(resp.body.startswith("\ufeff".encode("utf-8")))
        with self.assertRaises(HTTPException):
            reports_api.usage_csv(7, "all", self.u1, self.conn)


class YonetimTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        self.admin = make_user(self.conn, "admin@example.com", role="admin")
        self.u = make_user(self.conn, "ogrenci@example.com")
        self._tmp = TempUploads()
        self.dir = self._tmp.__enter__()
        self.doc = svc.upload_document(self.conn, self.u, "a.txt", b"Merhaba dunya. Ornek metin.")

    def tearDown(self):
        self._tmp.__exit__()

    def test_tum_belgeleri_listele_sahibiyle(self):
        liste = admin_api.list_all_documents(self.admin, self.conn)
        self.assertEqual([(d["filename"], d["owner_email"]) for d in liste], [("a.txt", "ogrenci@example.com")])
        self.assertNotIn("stored_name", liste[0])

    def test_kullanici_silme_dosya_ve_kayitlari_temizler(self):
        self.assertEqual(len(os.listdir(self.dir)), 1)
        self.assertEqual(admin_api.delete_user(self.u["id"], self.admin, self.conn), {"deleted": True})
        self.assertEqual(os.listdir(self.dir), [])
        for tablo in ("users", "documents", "chunks", "embeddings"):
            beklenen = 1 if tablo == "users" else 0                 # yalnizca yonetici kaldi
            self.assertEqual(self.conn.execute(f"SELECT COUNT(*) FROM {tablo}").fetchone()[0], beklenen)

    def test_kendini_silemez_ve_olmayan_kullanici(self):
        with self.assertRaises(HTTPException) as e:
            admin_api.delete_user(self.admin["id"], self.admin, self.conn)
        self.assertEqual(e.exception.status_code, 400)
        with self.assertRaises(HTTPException) as e:
            admin_api.delete_user(9999, self.admin, self.conn)
        self.assertEqual(e.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
