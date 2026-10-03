"""Hafta 4 testleri: sema, iliskiler, kisitlar, migration ve CRUD."""
import unittest

from app.db import chunks, database, documents, users
from scripts import seed
from tests.helpers import make_conn, make_user


class MigrationTests(unittest.TestCase):
    def test_migration_iki_kez_calismaz(self):
        conn = database.get_connection(":memory:")
        ilk = database.run_migrations(conn)
        ikinci = database.run_migrations(conn)
        self.assertIn("001_init", ilk)
        self.assertEqual(ikinci, [])

    def test_tablolar_ve_indeksler_var(self):
        conn = make_conn()
        if database.dialect(conn) == "postgres":
            adlar = {r[0] for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname = current_schema()"
                                                " UNION SELECT indexname FROM pg_indexes WHERE schemaname = current_schema()")}
        else:
            adlar = {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}
        for t in ["users", "documents", "chunks", "embeddings", "conversations",
                  "messages", "message_sources", "schema_migrations"]:
            self.assertIn(t, adlar)
        for i in ["idx_documents_user", "idx_conversations_user", "idx_messages_conversation"]:
            self.assertIn(i, adlar)


class KisitTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()

    def test_yabanci_anahtar_olmayan_kullaniciyi_reddeder(self):
        with self.assertRaises(database.IntegrityError):
            documents.create_document(self.conn, 999, "x.txt")

    def test_e_posta_benzersiz_ve_buyuk_kucuk_harf_duyarsiz(self):
        users.create_user(self.conn, "A@Example.com", "h")
        with self.assertRaises(users.DuplicateEmailError):
            users.create_user(self.conn, "a@example.com", "h")

    def test_gecersiz_rol_ve_durum_reddedilir(self):
        with self.assertRaises(ValueError):
            users.create_user(self.conn, "b@example.com", "h", role="root")
        u = make_user(self.conn)
        d = documents.create_document(self.conn, u["id"], "x.txt")
        with self.assertRaises(ValueError):
            documents.set_status(self.conn, d["id"], "bilinmeyen")
        with self.assertRaises(database.IntegrityError):  # veritabani CHECK kisiti da korur
            self.conn.execute("UPDATE documents SET status='zzz' WHERE id=?", (d["id"],))

    def test_ayni_belgede_ayni_chunk_index_olmaz(self):
        u = make_user(self.conn)
        d = documents.create_document(self.conn, u["id"], "x.txt")
        chunks.add_chunks(self.conn, d["id"], [(0, "a", None)])
        with self.assertRaises(database.IntegrityError):
            chunks.add_chunks(self.conn, d["id"], [(0, "b", None)])

    def test_kullanici_silinince_zincirleme_silinir(self):
        u = make_user(self.conn)
        d = documents.create_document(self.conn, u["id"], "x.txt")
        chunks.add_chunks(self.conn, d["id"], [(0, "a", 1), (1, "b", 1)])
        self.assertTrue(users.delete_user(self.conn, u["id"]))
        self.assertIsNone(documents.get_document(self.conn, d["id"]))
        self.assertEqual(chunks.count_chunks(self.conn, d["id"]), 0)


class CrudTests(unittest.TestCase):
    def setUp(self):
        self.conn = make_conn()
        self.u1 = make_user(self.conn, "bir@example.com")
        self.u2 = make_user(self.conn, "iki@example.com")

    def test_kullanici_crud(self):
        self.assertEqual(users.get_user_by_email(self.conn, "BIR@example.com")["id"], self.u1["id"])
        self.assertTrue(users.update_user_role(self.conn, self.u1["id"], "admin"))
        self.assertEqual(users.get_user_by_id(self.conn, self.u1["id"])["role"], "admin")
        self.assertEqual(len(users.list_users(self.conn)), 2)
        self.assertIsNone(users.get_user_by_id(self.conn, 12345))

    def test_belge_crud_ve_chunk_sayisi(self):
        d = documents.create_document(self.conn, self.u1["id"], "not.txt", "abc.txt", "text/plain", 10)
        self.assertEqual(d["status"], "uploaded")
        self.assertEqual(d["chunk_count"], 0)
        chunks.add_chunks(self.conn, d["id"], [(0, "bir", None), (1, "iki", None), (2, "uc", None)])
        documents.set_status(self.conn, d["id"], "chunked")
        d = documents.get_document(self.conn, d["id"])
        self.assertEqual((d["status"], d["chunk_count"]), ("chunked", 3))
        self.assertEqual([c["content"] for c in chunks.list_chunks(self.conn, d["id"])], ["bir", "iki", "uc"])
        self.assertEqual(len(chunks.list_chunks(self.conn, d["id"], limit=2, offset=1)), 2)
        self.assertTrue(documents.delete_document(self.conn, d["id"]))
        self.assertFalse(documents.delete_document(self.conn, d["id"]))

    def test_belge_listesi_kullaniciya_gore_filtrelenir(self):
        documents.create_document(self.conn, self.u1["id"], "a.txt")
        documents.create_document(self.conn, self.u2["id"], "b.txt")
        self.assertEqual([d["filename"] for d in documents.list_documents(self.conn, self.u1["id"])], ["a.txt"])
        self.assertEqual(len(documents.list_documents(self.conn)), 2)

    def test_sql_enjeksiyonu_parametreli_sorguda_etkisiz(self):
        kotu = "x' OR '1'='1"
        self.assertIsNone(users.get_user_by_email(self.conn, kotu))
        users.create_user(self.conn, "a'; DROP TABLE users;--@example.com", "h")
        self.assertEqual(len(users.list_users(self.conn)), 3)  # tablo yerinde


class SeedTests(unittest.TestCase):
    def test_seed_sentetik_veri_ekler_ve_tekrar_eklemez(self):
        conn = make_conn()
        seed.seed(conn)
        self.assertEqual(len(users.list_users(conn)), 2)
        self.assertTrue(all(u["email"].endswith("@example.com") for u in users.list_users(conn)))
        seed.seed(conn)
        self.assertEqual(len(users.list_users(conn)), 2)


if __name__ == "__main__":
    unittest.main()
