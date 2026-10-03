"""Yonetim islemleri (yalnizca yonetici uclarindan cagrilir)."""
from app.db import documents as documents_repo
from app.db import users
from app.services.documents import remove_stored_files


class UserNotFoundError(Exception):
    pass


def delete_user_and_files(conn, admin: dict, user_id: int) -> None:
    """Kullaniciyi, belgelerini, parcalarini, vektorlerini, sohbetlerini ve dosyalarini (disk/depo) siler."""
    if admin["id"] == user_id:
        raise ValueError("Kendi hesabınızı silemezsiniz")
    if users.get_user_by_id(conn, user_id) is None:
        raise UserNotFoundError("Kullanıcı bulunamadı")
    docs = documents_repo.list_documents(conn, user_id=user_id)
    remove_stored_files([d.get("stored_name") for d in docs])
    users.delete_user(conn, user_id)      # veritabani kayitlari CASCADE ile silinir
