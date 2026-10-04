"""api_tokens tablosu icin CRUD. Tum sorgular parametrelidir (?). Anahtarin kendisi buraya hic gelmez, yalnizca ozeti."""


def _row(row):
    return dict(row) if row is not None else None


# Listede ve API yanitinda gosterilen sutunlar (token_hash bilerek yok)
PUBLIC_COLUMNS = "id, name, prefix, created_at, last_used_at, expires_at"


def create_token(conn, user_id: int, name: str, prefix: str, token_hash: str, created_at: str, expires_at: str) -> dict:
    new_id = conn.execute(
        "INSERT INTO api_tokens (user_id, name, prefix, token_hash, created_at, expires_at)"
        " VALUES (?, ?, ?, ?, ?, ?) RETURNING id",
        (user_id, name, prefix, token_hash, created_at, expires_at),
    ).fetchone()[0]
    conn.commit()
    return _row(conn.execute(f"SELECT {PUBLIC_COLUMNS} FROM api_tokens WHERE id = ?", (new_id,)).fetchone())


def get_by_hash(conn, token_hash: str):
    return _row(conn.execute("SELECT * FROM api_tokens WHERE token_hash = ?", (token_hash,)).fetchone())


def list_for_user(conn, user_id: int) -> list:
    return [dict(r) for r in conn.execute(
        f"SELECT {PUBLIC_COLUMNS} FROM api_tokens WHERE user_id = ? ORDER BY id DESC", (user_id,))]


def count_for_user(conn, user_id: int) -> int:
    return conn.execute("SELECT COUNT(*) FROM api_tokens WHERE user_id = ?", (user_id,)).fetchone()[0]


def touch(conn, token_id: int, now: str) -> None:
    conn.execute("UPDATE api_tokens SET last_used_at = ? WHERE id = ?", (now, token_id))
    conn.commit()


# Yonetici listesi: anahtar bilgisi + sahibi. token_hash yine YOK.
_WITH_OWNER = ("SELECT t.id, t.name, t.prefix, t.created_at, t.last_used_at, t.expires_at, t.user_id,"
               " u.email AS owner_email, u.full_name AS owner_name"
               " FROM api_tokens t JOIN users u ON u.id = t.user_id")


def list_all(conn) -> list:
    return [dict(r) for r in conn.execute(_WITH_OWNER + " ORDER BY t.id DESC")]


def get_with_owner(conn, token_id: int):
    return _row(conn.execute(_WITH_OWNER + " WHERE t.id = ?", (token_id,)).fetchone())


def delete_by_id(conn, token_id: int) -> bool:
    """Yalnizca yonetici iptali icin (services/api_tokens.admin_revoke): sahibi kim olursa olsun siler."""
    cur = conn.execute("DELETE FROM api_tokens WHERE id = ?", (token_id,))
    conn.commit()
    return cur.rowcount > 0


def delete_token(conn, user_id: int, token_id: int) -> bool:
    """Yalnizca kullanicinin KENDI anahtarini siler (user_id kosulu): baskasinin anahtar numarasini bilmek yetmez."""
    cur = conn.execute("DELETE FROM api_tokens WHERE id = ? AND user_id = ?", (token_id, user_id))
    conn.commit()
    return cur.rowcount > 0

