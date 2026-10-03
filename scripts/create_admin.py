"""Yonetici hesabi olusturur. Kendi kendine kayit ile yonetici olunamaz.

Calistirma:  python -m scripts.create_admin
Parola ekranda gorunmez (getpass); koda ya da depoya yazilmaz.
"""
import getpass
import sys

from app.db import database
from app.services import auth


def main():
    full_name = input("Yonetici ad soyad: ").strip()
    email = input("Yonetici e-postasi: ").strip()
    password = getpass.getpass("Parola (en az 8 karakter, harf+rakam): ")
    conn = database.get_connection()
    database.run_migrations(conn)
    try:
        # Yoneticiyi betikle sunucunun sahibi olusturur: e-posta dogrulanmis sayilir.
        user = auth.register_user(conn, email, password, role="admin",
                                  full_name=auth.validate_name(full_name), verified=True)
    except (auth.ValidationError, auth.DuplicateUserError) as e:
        print("Hata:", e)
        sys.exit(1)
    print(f"Yonetici olusturuldu: {user['email']}")


if __name__ == "__main__":
    main()
