"""chunks tablosu icin CRUD."""


def add_chunks(conn, document_id: int, chunks) -> int:
    """chunks: (chunk_index, content, page_no) uclulerinin listesi. Eklenen sayiyi dondurur."""
    rows = [(document_id, idx, content, page) for idx, content, page in chunks]
    conn.executemany(
        "INSERT INTO chunks (document_id, chunk_index, content, page_no) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows)


def list_chunks(conn, document_id: int, limit=None, offset: int = 0) -> list:
    sql = "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index"
    params = [document_id]
    if limit is not None:
        sql += " LIMIT ? OFFSET ?"
        params += [limit, offset]
    return [dict(r) for r in conn.execute(sql, params)]


def list_unindexed_chunks(conn, document_id: int, model: str, limit: int) -> list:
    """Bu modelle vektoru OLMAYAN parcalar (hic vektoru yok ya da eski bir modelle uretilmis), sirayla.

    Kaldigi yerden devam eden indeksleme bunu kullanir: yarida kalan ya da model degisen belgede yalnizca
    eksikler islenir. embeddings.chunk_id UNIQUE oldugu icin eski modelin vektoru yenisiyle degistirilir.
    """
    return [dict(r) for r in conn.execute(
        "SELECT c.* FROM chunks c LEFT JOIN embeddings e ON e.chunk_id = c.id"
        " WHERE c.document_id = ? AND (e.id IS NULL OR e.model <> ?)"
        " ORDER BY c.chunk_index LIMIT ?", (document_id, model, limit))]


def count_chunks(conn, document_id: int) -> int:
    return conn.execute("SELECT COUNT(*) FROM chunks WHERE document_id = ?",
                        (document_id,)).fetchone()[0]
