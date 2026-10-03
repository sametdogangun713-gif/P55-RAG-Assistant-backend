"""Yonetici hesabi olusturur. Kendi kendine kayit ile yonetici olunamaz.

Calistirma:  python -m scripts.create_admin
Parola ekranda gorunmez (getpass); koda ya da depoya yazilmaz.
"""
import getpass
import sys

from app.db import database
from app.services import auth


def main():
    email = input("Yonetici e-postasi: ").strip()
    password = getpass.getpass("Parola (en az 8 karakter, harf+rakam): ")
    conn = database.get_connection()
    database.run_migrations(conn)
    try:
        user = auth.register_user(conn, email, password, role="admin")
    except (auth.ValidationError, auth.DuplicateUserError) as e:
        print("Hata:", e)
        sys.exit(1)
    print(f"Yonetici olusturuldu: {user['email']}")


if __name__ == "__main__":
    main()
