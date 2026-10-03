"""email_codes tablosu icin CRUD. Tum sorgular parametrelidir (?).

Bir tabloda iki amacli tek kullanimlik kod tutulur: 'verify' (e-posta dogrulama) ve 'reset' (parola sifirlama).
Kullanicinin her amac icin ayni anda tek gecerli kodu olur; yeni kod eskisini siler.
"""

PURPOSES = ("verify", "reset")


def _row(row):
    return dict(row) if row is not None else None


def _check(purpose: str):
    if purpose not in PURPOSES:
        raise ValueError(f"Gecersiz kod amaci: {purpose}")


def replace_code(conn, user_id: int, purpose: str, code_hash: str, expires_at: int, now: int) -> None:
    """Kullanicinin bu amactaki eski kodunu siler, yenisini ekler (tek islemde)."""
    _check(purpose)
    with conn:
        conn.execute("DELETE FROM email_codes WHERE user_id = ? AND purpose = ?", (user_id, purpose))
        conn.execute(
            "INSERT INTO email_codes (user_id, purpose, code_hash, expires_at, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, purpose, code_hash, expires_at, now),
        )


def get_latest(conn, user_id: int, purpose: str):
    _check(purpose)
    return _row(conn.execute(
        "SELECT * FROM email_codes WHERE user_id = ? AND purpose = ? ORDER BY id DESC LIMIT 1", (user_id, purpose)
    ).fetchone())


def add_attempt(conn, code_id: int) -> None:
    conn.execute("UPDATE email_codes SET attempts = attempts + 1 WHERE id = ?", (code_id,))
    conn.commit()


def delete_for_user(conn, user_id: int, purpose: str) -> None:
    _check(purpose)
    conn.execute("DELETE FROM email_codes WHERE user_id = ? AND purpose = ?", (user_id, purpose))
    conn.commit()
