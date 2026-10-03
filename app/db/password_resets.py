"""password_resets tablosu icin CRUD (Hafta 14). Tum sorgular parametrelidir (?)."""


def _row(row):
    return dict(row) if row is not None else None


def replace_code(conn, user_id: int, code_hash: str, expires_at: int, now: int) -> None:
    """Kullanicinin eski kodlarini siler, yenisini ekler (tek islemde)."""
    with conn:
        conn.execute("DELETE FROM password_resets WHERE user_id = ?", (user_id,))
        conn.execute(
            "INSERT INTO password_resets (user_id, code_hash, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (user_id, code_hash, expires_at, now),
        )


def get_latest(conn, user_id: int):
    return _row(conn.execute(
        "SELECT * FROM password_resets WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)
    ).fetchone())


def add_attempt(conn, reset_id: int) -> None:
    conn.execute("UPDATE password_resets SET attempts = attempts + 1 WHERE id = ?", (reset_id,))
    conn.commit()


def delete_for_user(conn, user_id: int) -> None:
    conn.execute("DELETE FROM password_resets WHERE user_id = ?", (user_id,))
    conn.commit()
