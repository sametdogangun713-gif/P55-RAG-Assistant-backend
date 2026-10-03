"""documents tablosu icin CRUD."""

STATUSES = ("uploaded", "chunked", "indexed", "failed")

_SELECT = (
    "SELECT d.*, u.email AS owner_email,"
    " (SELECT COUNT(*) FROM chunks c WHERE c.document_id = d.id) AS chunk_count"
    " FROM documents d JOIN users u ON u.id = d.user_id"
)


def create_document(conn, user_id: int, filename: str, stored_name=None,
                    mime_type=None, size_bytes: int = 0) -> dict:
    new_id = conn.execute(
        "INSERT INTO documents (user_id, filename, stored_name, mime_type, size_bytes)"
        " VALUES (?, ?, ?, ?, ?) RETURNING id",
        (user_id, filename, stored_name, mime_type, size_bytes),
    ).fetchone()[0]
    conn.commit()
    return get_document(conn, new_id)


def get_document(conn, doc_id: int):
    row = conn.execute(_SELECT + " WHERE d.id = ?", (doc_id,)).fetchone()
    return dict(row) if row else None


def list_documents(conn, user_id=None) -> list:
    """user_id verilirse yalnizca o kullanicinin belgeleri; verilmezse hepsi (yonetici)."""
    if user_id is None:
        rows = conn.execute(_SELECT + " ORDER BY d.id DESC")
    else:
        rows = conn.execute(_SELECT + " WHERE d.user_id = ? ORDER BY d.id DESC", (user_id,))
    return [dict(r) for r in rows]


def set_status(conn, doc_id: int, status: str, error=None) -> bool:
    if status not in STATUSES:
        raise ValueError(f"Gecersiz durum: {status}")
    cur = conn.execute("UPDATE documents SET status = ?, error = ? WHERE id = ?",
                       (status, error, doc_id))
    conn.commit()
    return cur.rowcount > 0


def delete_document(conn, doc_id: int) -> bool:
    """Belgeyi siler; parcalari ve vektorleri ON DELETE CASCADE ile silinir."""
    cur = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    return cur.rowcount > 0
