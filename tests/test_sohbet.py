"""Hafta 11 testleri: sohbet gecmisi, baglam penceresi, ozetleme, takip sorusu, sahiplik."""
import unittest

from fastapi import HTTPException

from app.api import conversations as conv_api
from app.core import config
from app.db import conversations as repo
from app.db import documents as documents_repo
from app.services import chat, rag
from app.services import documents as svc
from app.services.llm_client import LLMTimeoutError
from app.db import database
from tests.helpers import ScriptedLLM, TempUploads, make_conn, make_user

VEKTOR_DB = ("Vektor veritabani, metinlerin sayisal vektor temsillerini saklar. Benzerlik arama, soru vektorune "
             "en yakin vektorleri kosinus benzerligi ile bulur. Embedding modelleri anlami vektorle gosterir.")
YEMEK = ("Makarna tarifi icin once suyu kaynatin. Makarnayi tuzlu suda haslayin. Domates sosunu ayri tavada "
         "pisirin ve haslanmis makarnanin uzerine dokun. Afiyet olsun.")
SORU = "vektor veritabani ne saklar"


class Temel(unittest.TestCase):
    def setUp(self):
        self._eski = (config.MIN_SCORE, config.CHAT_HISTORY_CHARS, config.CHAT_KEEP_RECENT)
        config.MIN_SCORE = 0.15
        self.conn = make_conn()
        self.u = make_user(self.conn, "bir@example.com")
        self.diger = make_user(self.conn, "iki@example.com")
        self.admin = make_user(self.conn, "admin@example.com", role="admin")
        self._tmp = TempUploads()
        self._tmp.__enter__()
        self.d1 = svc.upload_document(self.conn, self.u, "vektor.txt", VEKTOR_DB.encode())
        svc.upload_document(self.conn, self.u, "yemek.txt", YEMEK.encode())
        self.conv = chat.create_conversation(self.conn, self.u)

    def tearDown(self):
        config.MIN_SCORE, config.CHAT_HISTORY_CHARS, config.CHAT_KEEP_RECENT = self._eski
        self._tmp.__exit__()

    def gonder(self, metin, llm, conv=None):
        return chat.send_message(self.conn, self.u, (conv or self.conv)["id"], metin, llm)


class YardimciFonksiyonTests(unittest.TestCase):
    def test_alintilar_silinir(self):
        self.assertEqual(chat.strip_citations("Saklar [1]. Bulur [2][3]."), "Saklar. Bulur.")

    def test_gecmis_normallestirme(self):
        n = chat.normalize_history([
            {"role": "assistant", "content": "basta"},          # user ile baslamali -> atilir
            {"role": "user", "content": "a"}, {"role": "user", "content": "b"},   # ardisik -> birlestirilir
            {"role": "assistant", "content": "c"},
            {"role": "user", "content": "sonda"},               # assistant ile bitmeli -> atilir
        ])
        self.assertEqual(n, [{"role": "user", "content": "a\nb"}, {"role": "assistant", "content": "c"}])
        self.assertEqual(chat.normalize_history([]), [])


class MesajlasmaTests(Temel):
    def test_ilk_mesaj_kaydedilir_ve_baslik_olusur(self):
        llm = ScriptedLLM("Vektör veritabanı vektör temsillerini saklar [1].")
        out = self.gonder(SORU, llm)
        self.assertEqual(out["assistant_message"]["status"], "answered")
        self.assertEqual(len(llm.cagrilar), 1)                 # ilk turda yeniden yazma/ozet cagrisi yok
        mesajlar = chat.list_messages(self.conn, self.u, self.conv["id"])
        self.assertEqual([m["role"] for m in mesajlar], ["user", "assistant"])
        cevap = mesajlar[1]
        self.assertTrue(cevap["grounded"])
        self.assertEqual(cevap["sources"][0]["filename"], "vektor.txt")
        self.assertEqual(cevap["sources"][0]["n"], 1)
        self.assertIsInstance(cevap["latency_ms"], int)
        self.assertEqual(repo.get_conversation(self.conn, self.conv["id"])["title"], SORU)
        self.assertEqual(chat.list_conversations(self.conn, self.u)[0]["message_count"], 2)

    def test_takip_sorusu_yeniden_yazilir_ve_gecmis_baglama_girer(self):
        self.gonder(SORU, ScriptedLLM("Saklar [1]."))
        llm = ScriptedLLM(SORU, "Benzerlik aramayla bulunur [1].")          # 1: yeniden yazma, 2: yanit
        out = self.gonder("peki ya o nasil bulunur?", llm)
        self.assertEqual(out["retrieval_query"], SORU)
        self.assertEqual(out["assistant_message"]["status"], "answered")
        self.assertEqual(llm.cagrilar[0]["system"], chat.REWRITE_SYSTEM)
        rag_cagrisi = llm.cagrilar[1]["messages"]
        self.assertEqual([m["role"] for m in rag_cagrisi], ["user", "assistant", "user"])
        self.assertEqual(rag_cagrisi[0]["content"], SORU)
        self.assertNotIn("[1]", rag_cagrisi[1]["content"])                     # eski alinti numaralari temizlendi
        self.assertIn("SORU: peki ya o nasil bulunur?", rag_cagrisi[2]["content"])
        self.assertEqual(len(chat.list_messages(self.conn, self.u, self.conv["id"])), 4)

    def test_yeniden_yazma_hata_verirse_orijinal_soruyla_devam(self):
        self.gonder(SORU, ScriptedLLM("Saklar [1]."))
        llm = ScriptedLLM(LLMTimeoutError("yavas"))
        out = self.gonder("peki ya o?", llm)                    # bu soru tek basina bulunamaz -> LLM'e gitmez
        self.assertEqual(out["retrieval_query"], "peki ya o?")
        self.assertEqual(out["assistant_message"]["status"], "no_context")

    def test_belgede_olmayan_soru_kaydedilir_kaynaksiz(self):
        out = self.gonder("uzay roketi yakiti nedir", ScriptedLLM())
        m = chat.list_messages(self.conn, self.u, self.conv["id"])[1]
        self.assertEqual((m["status"], m["grounded"], m["sources"]), ("no_context", False, []))
        self.assertEqual(out["assistant_message"]["content"], rag.NO_INFO_TEXT)
        satir = self.conn.execute("SELECT best_score FROM messages WHERE role='assistant'").fetchone()
        self.assertIsNotNone(satir["best_score"])

    def test_llm_hatasinda_hicbir_sey_kaydedilmez(self):
        with self.assertRaises(LLMTimeoutError):
            self.gonder(SORU, ScriptedLLM(LLMTimeoutError("x")))
        self.assertEqual(chat.list_messages(self.conn, self.u, self.conv["id"]), [])
        self.assertEqual(repo.get_conversation(self.conn, self.conv["id"])["title"], repo.DEFAULT_TITLE)

    def test_bos_soru_llm_e_gitmeden_reddedilir(self):
        self.gonder(SORU, ScriptedLLM("Saklar [1]."))
        llm = ScriptedLLM()
        with self.assertRaises(ValueError):
            self.gonder("   ", llm)
        self.assertEqual(llm.cagrilar, [])

    def test_cok_uzun_gecmis_mesaji_kirpilir(self):
        repo.add_message(self.conn, self.conv["id"], "user", "x" * 3000)
        repo.add_message(self.conn, self.conv["id"], "assistant", "y" * 3000)
        llm = ScriptedLLM(SORU, "Saklar [1].")
        self.gonder(SORU, llm)
        for m in llm.cagrilar[1]["messages"][:-1]:
            self.assertLessEqual(len(m["content"]), config.HISTORY_MSG_MAX_CHARS)


class OzetlemeTests(Temel):
    def _gecmis_doldur(self):
        ids = []
        for i in range(3):
            ids.append(repo.add_message(self.conn, self.conv["id"], "user", f"{i}. soru metni " + "a" * 40))
            ids.append(repo.add_message(self.conn, self.conv["id"], "assistant", f"{i}. cevap metni [1] " + "b" * 40))
        return ids

    def test_uzun_gecmis_ozetlenir_son_mesajlar_korunur(self):
        config.CHAT_HISTORY_CHARS, config.CHAT_KEEP_RECENT = 100, 2
        ids = self._gecmis_doldur()
        llm = ScriptedLLM("OZET-METNI", SORU, "Saklar [1].")      # 1 ozet, 2 yeniden yazma, 3 yanit
        out = self.gonder(SORU, llm)
        self.assertEqual(out["assistant_message"]["status"], "answered")
        self.assertEqual(llm.cagrilar[0]["system"], chat.SUMMARY_SYSTEM)
        self.assertIn("(yok)", llm.cagrilar[0]["messages"][0]["content"])
        conv = repo.get_conversation(self.conn, self.conv["id"])
        self.assertEqual((conv["summary"], conv["summary_upto"]), ("OZET-METNI", ids[3]))
        rag_cagrisi = llm.cagrilar[2]
        self.assertIn("OZET-METNI", rag_cagrisi["system"])
        self.assertIn("KAYNAĞI değildir", rag_cagrisi["system"])
        self.assertEqual([m["role"] for m in rag_cagrisi["messages"]], ["user", "assistant", "user"])  # son 2 + yeni soru
        self.assertIn("2. soru metni", rag_cagrisi["messages"][0]["content"])

    def test_ozet_bir_sonraki_turda_birlestirilir(self):
        config.CHAT_HISTORY_CHARS, config.CHAT_KEEP_RECENT = 100, 2
        self._gecmis_doldur()
        self.gonder(SORU, ScriptedLLM("ILK-OZET", SORU, "Saklar [1]."))
        llm = ScriptedLLM("IKINCI-OZET", SORU, "Saklar [1].")
        self.gonder(SORU, llm)
        self.assertIn("ILK-OZET", llm.cagrilar[0]["messages"][0]["content"])      # onceki ozet girdi olarak verildi
        self.assertEqual(repo.get_conversation(self.conn, self.conv["id"])["summary"], "IKINCI-OZET")

    def test_ozetleme_basarisiz_olursa_soru_yine_yanitlanir(self):
        config.CHAT_HISTORY_CHARS, config.CHAT_KEEP_RECENT = 100, 2
        self._gecmis_doldur()
        out = self.gonder(SORU, ScriptedLLM(LLMTimeoutError("x"), SORU, "Saklar [1]."))
        self.assertEqual(out["assistant_message"]["status"], "answered")
        conv = repo.get_conversation(self.conn, self.conv["id"])
        self.assertEqual((conv["summary"], conv["summary_upto"]), (None, 0))       # sonraki turda tekrar denenir

    def test_kisa_gecmis_ozetlenmez(self):
        self.gonder(SORU, ScriptedLLM("Saklar [1]."))
        llm = ScriptedLLM(SORU, "Saklar [1].")
        self.gonder(SORU, llm)
        self.assertNotIn(chat.SUMMARY_SYSTEM, [c["system"] for c in llm.cagrilar])


class SahiplikTests(Temel):
    def test_baskasinin_sohbetine_erisilemez_yonetici_dahil(self):
        for kisi in (self.diger, self.admin):
            with self.assertRaises(chat.ConversationNotFoundError):
                chat.list_messages(self.conn, kisi, self.conv["id"])
            with self.assertRaises(chat.ConversationNotFoundError):
                chat.send_message(self.conn, kisi, self.conv["id"], SORU, ScriptedLLM())
            with self.assertRaises(chat.ConversationNotFoundError):
                chat.delete_conversation(self.conn, kisi, self.conv["id"])
        with self.assertRaises(chat.ConversationNotFoundError):
            chat.list_messages(self.conn, self.u, 9999)
        self.assertEqual(chat.list_conversations(self.conn, self.diger), [])

    def test_sohbet_silinince_mesaj_ve_kaynaklar_gider(self):
        self.gonder(SORU, ScriptedLLM("Saklar [1]."))
        chat.delete_conversation(self.conn, self.u, self.conv["id"])
        for tablo in ("messages", "message_sources"):
            self.assertEqual(self.conn.execute(f"SELECT COUNT(*) FROM {tablo}").fetchone()[0], 0)

    def test_belge_silinince_mesaj_kalir_kaynak_gider(self):
        self.gonder(SORU, ScriptedLLM("Saklar [1]."))
        svc.delete_document(self.conn, self.u, self.d1["id"])
        mesajlar = chat.list_messages(self.conn, self.u, self.conv["id"])
        self.assertEqual(len(mesajlar), 2)
        self.assertEqual(mesajlar[1]["sources"], [])

    def test_sema_migrationlari_uygulanmis(self):
        def sutunlar(tablo):      # SQLite ve PostgreSQL'de ayni calisir (PRAGMA yalnizca SQLite'ta var)
            return {d[0] for d in self.conn.execute(f"SELECT * FROM {tablo} LIMIT 0").description}
        kolonlar = sutunlar("messages")
        self.assertTrue({"status", "grounded", "latency_ms", "best_score"} <= kolonlar)
        kolonlar = sutunlar("conversations")
        self.assertTrue({"summary", "summary_upto"} <= kolonlar)
        uygulanan = {r["version"] for r in self.conn.execute("SELECT version FROM schema_migrations")}
        if database.dialect(self.conn) == "postgres":     # PostgreSQL semasi tek dosyada (001..004'un toplami)
            self.assertIn("001_init", uygulanan)
        else:
            self.assertTrue({"001_init", "002_message_quality", "003_conversation_summary"} <= uygulanan)


class YenidenAdlandirmaTests(Temel):
    def test_ad_temizlenir_kirpilir_bos_olamaz(self):
        c = chat.rename_conversation(self.conn, self.u, self.conv["id"], "  Vize   hazırlığı  ")
        self.assertEqual(c["title"], "Vize hazırlığı")
        c = chat.rename_conversation(self.conn, self.u, self.conv["id"], "x" * 200)
        self.assertEqual(len(c["title"]), chat.MAX_TITLE_CHARS)
        with self.assertRaises(ValueError):
            chat.rename_conversation(self.conn, self.u, self.conv["id"], "   ")

    def test_baskasinin_sohbeti_adlandirilamaz(self):
        with self.assertRaises(chat.ConversationNotFoundError):
            chat.rename_conversation(self.conn, self.diger, self.conv["id"], "Ele geçirildi")
        with self.assertRaises(HTTPException) as e:
            conv_api.rename_conversation(self.conv["id"], conv_api.RenameConversation(title="X"), self.diger, self.conn)
        self.assertEqual(e.exception.status_code, 404)


class ApiTests(Temel):
    def test_akis(self):
        c = conv_api.create_conversation(conv_api.NewConversation(title="Deneme"), self.u, self.conn)
        self.assertEqual(c["title"], "Deneme")
        out = conv_api.send_message(c["id"], conv_api.NewMessage(content=SORU), self.u, self.conn,
                                    ScriptedLLM("Saklar [1]."))
        self.assertEqual(out["assistant_message"]["status"], "answered")
        self.assertEqual(len(conv_api.list_messages(c["id"], self.u, self.conn)), 2)
        self.assertTrue(any(x["id"] == c["id"] for x in conv_api.list_conversations(self.u, self.conn)))
        self.assertEqual(conv_api.delete_conversation(c["id"], self.u, self.conn), {"deleted": True})

    def test_hata_kodlari(self):
        with self.assertRaises(HTTPException) as e:
            conv_api.list_messages(self.conv["id"], self.diger, self.conn)
        self.assertEqual(e.exception.status_code, 404)
        with self.assertRaises(HTTPException) as e:
            conv_api.send_message(self.conv["id"], conv_api.NewMessage(content=" "), self.u, self.conn, ScriptedLLM())
        self.assertEqual(e.exception.status_code, 400)
        with self.assertRaises(HTTPException) as e:
            conv_api.send_message(self.conv["id"], conv_api.NewMessage(content=SORU), self.u, self.conn,
                                  ScriptedLLM(LLMTimeoutError("x")))
        self.assertEqual(e.exception.status_code, 504)


if __name__ == "__main__":
    unittest.main()
