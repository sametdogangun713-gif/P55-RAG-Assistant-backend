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


def get_chunk(conn, chunk_id: int):
    row = conn.execute("SELECT * FROM chunks WHERE id = ?", (chunk_id,)).fetchone()
    return dict(row) if row else None


def count_chunks(conn, document_id: int) -> int:
    return conn.execute("SELECT COUNT(*) FROM chunks WHERE document_id = ?",
                        (document_id,)).fetchone()[0]


def delete_chunks(conn, document_id: int) -> int:
    cur = conn.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
    conn.commit()
    return cur.rowcount
