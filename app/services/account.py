"""Kullanicinin kendi hesabi ("Hesabim"): ad degistirme, parola degistirme, hesabi silme. HTTP bilmez.

Guvenlik kararlari:
  - Parola degistirme ve hesap silme MEVCUT PAROLAYI ister: acik unutulmus bir oturumu ele geciren biri
    parolayi degistirip hesabi kilitleyemesin ya da silemesin.
  - Son yonetici kendini silemez: sistemde yonetici kalmazdi (yeni yonetici ancak betikle acilir).
  - E-posta degistirme yok: yeni adresin dogrulanmasi gerekir (kayit akisindaki gibi); bilinen sinir.
"""
from app.core import security
from app.db import documents as documents_repo
from app.db import users
from app.services import auth
from app.services.documents import remove_stored_files


class WrongPasswordError(Exception):
    pass


class LastAdminError(Exception):
    pass


def _check_password(user: dict, password: str) -> None:
    if not security.verify_password(password or "", user["password_hash"]):
        raise WrongPasswordError("Mevcut parola hatalı")


def update_name(conn, user: dict, full_name: str) -> dict:
    name = auth.validate_name(full_name)
    users.update_full_name(conn, user["id"], name)
    return users.get_user_by_id(conn, user["id"])


def change_password(conn, user: dict, current_password: str, new_password: str) -> None:
    _check_password(user, current_password)
    auth.validate_password(new_password)
    if current_password == new_password:
        raise auth.ValidationError("Yeni parola eskisiyle aynı olamaz")
    users.update_password_hash(conn, user["id"], security.hash_password(new_password))


def delete_account(conn, user: dict, password: str) -> None:
    """Hesabi ve tum verisini (belgeler, dosyalar, sohbetler) kalici olarak siler."""
    _check_password(user, password)
    if user["role"] == "admin" and sum(1 for u in users.list_users(conn) if u["role"] == "admin") <= 1:
        raise LastAdminError("Son yönetici hesabı silinemez. Önce başka bir yönetici ata")
    docs = documents_repo.list_documents(conn, user_id=user["id"])
    remove_stored_files([d.get("stored_name") for d in docs])
    users.delete_user(conn, user["id"])               # veritabani kayitlari CASCADE ile silinir
