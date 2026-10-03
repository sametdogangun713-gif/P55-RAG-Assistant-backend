"""Gelistirme icin SENTETIK ornek veri ekler (gercek kisisel veri kullanilmaz - KVKK).

Calistirma:  python -m scripts.seed
"""
from app.core.security import hash_password
from app.db import chunks, database, documents, users

# Yalnizca yerel gelistirme icin sentetik demo parolasi (gercek bir parola degil)
DEMO_PAROLA = "Demo12345"

ORNEK_METIN = [
    "RAG, belgelerden ilgili parcalari bulup yanitin bu parcalara dayandirilmasi yontemidir.",
    "Embedding, bir metnin anlamini sayisal bir vektorle temsil eder.",
    "Benzerlik arama, soru vektorune en yakin parca vektorlerini bulur.",
]


def seed(conn):
    if users.list_users(conn):
        print("Veritabani zaten dolu, atlandi.")
        return
    h = hash_password(DEMO_PAROLA)
    u1 = users.create_user(conn, "ornek.ogrenci@example.com", h)
    users.create_user(conn, "ornek.yonetici@example.com", h, role="admin")
    doc = documents.create_document(conn, u1["id"], "ornek_ders_notu.txt", "ornek1.txt", "text/plain", 300)
    chunks.add_chunks(conn, doc["id"], [(i, t, None) for i, t in enumerate(ORNEK_METIN)])
    documents.set_status(conn, doc["id"], "chunked")
    print("Sentetik veri eklendi: 2 kullanici (parola: Demo12345), 1 belge, 3 parca.")


if __name__ == "__main__":
    c = database.get_connection()
    database.run_migrations(c)
    seed(c)
    c.close()
