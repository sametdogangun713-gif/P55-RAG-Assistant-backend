"""users tablosu icin CRUD. Tum sorgular parametrelidir (?), SQL enjeksiyonuna karsi."""
from app.db.database import IntegrityError

ROLES = ("user", "admin")


class DuplicateEmailError(Exception):
    """Ayni e-posta ile ikinci kayit denendi."""


def _row(row):
    return dict(row) if row is not None else None


def create_user(conn, email: str, password_hash: str, role: str = "user") -> dict:
    if role not in ROLES:
        raise ValueError(f"Gecersiz rol: {role}")
    try:
        # RETURNING id: yeni satirin numarasi (SQLite 3.35+ ve PostgreSQL ikisi de destekler)
        new_id = conn.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?) RETURNING id",
            (email, password_hash, role),
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


def delete_user(conn, user_id: int) -> bool:
    """Kullaniciyi siler; belgeleri, parcalari, sohbetleri ON DELETE CASCADE ile silinir."""
    cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    return cur.rowcount > 0
