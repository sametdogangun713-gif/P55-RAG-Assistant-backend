"""Supabase'i ilk kez hazirlar: veritabani tablolari (migration) + gizli dosya kovasi (bucket).

Calistirma (P55-RAG-Assistant-backend klasorunde, .env icinde Supabase degerleri yazili olmali):
    python -m scripts.supabase_kurulum
Birden cok kez calistirmak zararsizdir: uygulanmis migration ve var olan kova atlanir.
Gizli degerler (parola, service_role anahtari) ekrana YAZDIRILMAZ.
"""
import sys

from app.core import config
from app.db import database
from app.services import storage


def main() -> int:
    if not config.is_postgres():
        print("DATABASE_URL bir PostgreSQL adresi değil. Supabase -> Connect -> Transaction pooler adresini .env'e yaz.")
        return 1
    host = config.DATABASE_URL.split("@")[-1].split("/")[0]       # parola kismi yazdirilmaz
    print(f"Veritabanı: {host}")
    yeni = database.init_db()
    print("Migration:", ", ".join(yeni) if yeni else "hepsi zaten uygulanmış")

    if config.STORAGE_BACKEND != "supabase":
        print("STORAGE_BACKEND=supabase değil; dosya kovası atlandı.")
        return 0
    try:
        olustu = storage.ensure_bucket()
    except storage.StorageError as e:
        print("Dosya kovası oluşturulamadı:", e)
        if config.MAX_UPLOAD_MB > 50:
            print(f"İpucu: MAX_UPLOAD_MB={config.MAX_UPLOAD_MB}. Supabase ücretsiz planında dosya başına sınır 50 MB; "
                  "MAX_UPLOAD_MB=50 ile tekrar dene.")
        return 1
    print(f"Dosya kovası '{config.SUPABASE_BUCKET}':", "oluşturuldu (gizli)" if olustu else "zaten var")
    return 0


if __name__ == "__main__":
    sys.exit(main())
