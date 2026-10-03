"""users tablosu icin CRUD. Tum sorgular parametrelidir (?), SQL enjeksiyonuna karsi."""
import time

from app.db.database import IntegrityError

ROLES = ("user", "admin")


class DuplicateEmailError(Exception):
    """Ayni e-posta ile ikinci kayit denendi."""


def _row(row):
    return dict(row) if row is not None else None


def utc_now_text() -> str:
    """created_at ile ayni bicim ('YYYY-MM-DD HH:MM:SS', UTC); iki veritabaninda da ayni calisir."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


def create_user(conn, email: str, password_hash: str, role: str = "user",
                full_name: str = "", verified: bool = True) -> dict:
    """verified=False: e-posta dogrulanana kadar email_verified_at bos kalir (giris yapamaz)."""
    if role not in ROLES:
        raise ValueError(f"Gecersiz rol: {role}")
    try:
        # RETURNING id: yeni satirin numarasi (SQLite 3.35+ ve PostgreSQL ikisi de destekler)
        new_id = conn.execute(
            "INSERT INTO users (email, password_hash, role, full_name, email_verified_at)"
            " VALUES (?, ?, ?, ?, ?) RETURNING id",
            (email, password_hash, role, full_name, utc_now_text() if verified else None),
        ).fetchone()[0]
        conn.commit()
    except IntegrityError as e:
        conn.rollback()
        if "UNIQUE" in str(e).upper():
            raise DuplicateEmailError(email) from e
        raise
    return get_user_by_id(conn, new_id)


def get_user_by_id(conn, user_id: int):
    return _row(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())


def get_user_by_email(conn, email: str):
    return _row(conn.execute("SELECT * FROM users WHERE lower(email) = lower(?)", (email,)).fetchone())


def list_users(conn) -> list:
    return [dict(r) for r in conn.execute("SELECT * FROM users ORDER BY id")]


def update_user_role(conn, user_id: int, role: str) -> bool:
    if role not in ROLES:
        raise ValueError(f"Gecersiz rol: {role}")
    cur = conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    conn.commit()
    return cur.rowcount > 0


def update_password_hash(conn, user_id: int, password_hash: str) -> bool:
    """Hafta 14: parola sifirlama icin."""
    cur = conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    conn.commit()
    return cur.rowcount > 0


def update_full_name(conn, user_id: int, full_name: str) -> bool:
    cur = conn.execute("UPDATE users SET full_name = ? WHERE id = ?", (full_name, user_id))
    conn.commit()
    return cur.rowcount > 0


def mark_email_verified(conn, user_id: int) -> bool:
    """E-posta dogrulandi. Zaten dogrulanmissa ilk tarih korunur."""
    cur = conn.execute("UPDATE users SET email_verified_at = ? WHERE id = ? AND email_verified_at IS NULL",
                       (utc_now_text(), user_id))
    conn.commit()
    return cur.rowcount > 0


def update_unverified_signup(conn, user_id: int, full_name: str, password_hash: str) -> bool:
    """Dogrulanmamis hesaba yeniden kayit olunursa ad ve parola yenilenir (e-postanin sahibi henuz kanitlanmadi)."""
    cur = conn.execute("UPDATE users SET full_name = ?, password_hash = ? WHERE id = ? AND email_verified_at IS NULL",
                       (full_name, password_hash, user_id))
    conn.commit()
    return cur.rowcount > 0


def delete_user(conn, user_id: int) -> bool:
    """Kullaniciyi siler; belgeleri, parcalari, sohbetleri ON DELETE CASCADE ile silinir."""
    cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    return cur.rowcount > 0
