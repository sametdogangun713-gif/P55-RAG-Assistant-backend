"""Kullanim raporunun PDF hali: gecerli PDF, Turkce harfler dogru, oranlar Turkce bicimde, guvenli metin, yetki."""
import io
import unittest

from fastapi import HTTPException
from pypdf import PdfReader

from app.api import reports as reports_api
from app.db import chunks as chunks_repo
from app.db import conversations as repo
from app.db import documents as documents_repo
from app.services import report_pdf, reports
from tests.test_rapor import BUGUN, RaporVerisi, mesaj


def pdf_metni(pdf: bytes) -> str:
    return "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf)).pages)


class PdfTests(RaporVerisi):
    def rapor(self):
        return reports.usage_report(self.conn, self.u1["id"], 7, today=BUGUN)

    def test_gecerli_pdf_ve_turkce_harfler(self):
        pdf = report_pdf.report_to_pdf(self.rapor(), owner="bir@example.com")
        self.assertTrue(pdf.startswith(b"%PDF-"))
        metin = pdf_metni(pdf)
        for parca in ("Kullanım ve Kaynak Raporu", "Kaynağa dayalı yanıt oranı", "Yanıtsız kalan oranı",
                      "İlgili bölüm bulunamadı", "Günlük soru sayısı", "birinci.txt", "bir@example.com"):
            self.assertIn(parca, metin)                     # ş ğ ı İ bozulmadan basildi (Helvetica basamazdi)

    def test_oranlar_turkce_bicimde(self):
        metin = pdf_metni(report_pdf.report_to_pdf(self.rapor()))
        self.assertIn("%66,7", metin)                       # 0.667 -> %66,7
        self.assertNotIn("grounded_rate", metin)
        self.assertEqual(report_pdf._num(1234), "1.234")
        self.assertEqual(report_pdf._num(0.5), "0,5")
        self.assertEqual(report_pdf._pct(None), "—")
        self.assertEqual(report_pdf._date_tr("2026-10-03"), "03.10.2026")

    def test_dosya_adi_bicim_komutu_olarak_yorumlanmaz(self):
        kotu = documents_repo.create_document(self.conn, self.u1["id"], "<b>kalin</b> & rapor.txt")
        chunks_repo.add_chunks(self.conn, kotu["id"], [(0, "z", None)])
        cid = chunks_repo.list_chunks(self.conn, kotu["id"])[0]["id"]
        c = repo.create_conversation(self.conn, self.u1["id"])["id"]
        mesaj(self.conn, c, "user", "q", "2026-10-10")
        a = mesaj(self.conn, c, "assistant", "r", "2026-10-10", status="answered", grounded=True, latency_ms=1)
        repo.add_message_sources(self.conn, a, [{"n": 1, "chunk_id": cid, "score": 0.5}])
        metin = pdf_metni(report_pdf.report_to_pdf(self.rapor()))
        self.assertIn("<b>kalin</b> & rapor.txt", metin)    # escape edildi: etiket metin olarak gorunur

    def test_bos_donem(self):
        r = reports.usage_report(self.conn, self.u2["id"], 7, today=BUGUN)          # u2: hic sorusu yok
        metin = pdf_metni(report_pdf.report_to_pdf(r))
        self.assertIn("kaynak gösterilen belge yok", metin)

    def test_api_ucu_ve_yetki(self):
        resp = reports_api.usage_pdf(7, "me", self.u1, self.conn)
        self.assertEqual(resp.media_type, "application/pdf")
        self.assertIn('filename="kullanim-raporu.pdf"', resp.headers["Content-Disposition"])
        self.assertTrue(resp.body.startswith(b"%PDF-"))
        with self.assertRaises(HTTPException) as e:
            reports_api.usage_pdf(7, "all", self.u1, self.conn)   # normal kullanici tum sistemi alamaz
        self.assertEqual(e.exception.status_code, 403)
        self.assertIn("Kullanıcı", pdf_metni(reports_api.usage_pdf(7, "all", self.admin, self.conn).body))


if __name__ == "__main__":
    unittest.main()
