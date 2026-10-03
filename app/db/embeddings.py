"""embeddings tablosu.

- SQLite    : vektorler float32 BLOB olarak saklanir; benzerlik Python'da (numpy) hesaplanir.
- PostgreSQL: vektorler pgvector'un `vector` tipinde saklanir; benzerlik SQL'de (`<=>` = kosinus uzakligi)
              hesaplanir. Boylece her aramada tum vektorleri agdan cekmek gerekmez.
"""
import numpy as np

from app.db.database import dialect


def _pg_vector(vec) -> str:
    """numpy vektoru -> pgvector metin bicimi '[0.1,0.2,...]' (ek kutuphane gerektirmez)."""
    return "[" + ",".join(f"{float(x):.7g}" for x in vec) + "]"


def save_embeddings(conn, chunk_ids, matrix, model: str) -> int:
    matrix = np.asarray(matrix, dtype=np.float32)
    dim = int(matrix.shape[1])
    if dialect(conn) == "postgres":
        sql = ("INSERT INTO embeddings (chunk_id, vector, dim, model) VALUES (?, ?::vector, ?, ?)"
               " ON CONFLICT (chunk_id) DO UPDATE SET vector = excluded.vector, dim = excluded.dim,"
               " model = excluded.model")
        rows = [(cid, _pg_vector(vec), dim, model) for cid, vec in zip(chunk_ids, matrix)]
    else:
        sql = ("INSERT INTO embeddings (chunk_id, vector, dim, model) VALUES (?, ?, ?, ?)"
               " ON CONFLICT (chunk_id) DO UPDATE SET vector = excluded.vector, dim = excluded.dim,"
               " model = excluded.model")
        rows = [(cid, vec.tobytes(), dim, model) for cid, vec in zip(chunk_ids, matrix)]
    conn.executemany(sql, rows)
    conn.commit()
    return len(rows)


def delete_embeddings_for_document(conn, document_id: int) -> int:
    cur = conn.execute(
        "DELETE FROM embeddings WHERE chunk_id IN (SELECT id FROM chunks WHERE document_id = ?)",
        (document_id,))
    conn.commit()
    return cur.rowcount


def count_embeddings(conn, document_id: int) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM embeddings e JOIN chunks c ON c.id = e.chunk_id WHERE c.document_id = ?",
        (document_id,)).fetchone()[0]


_CHUNK_COLUMNS = ("c.id AS chunk_id, c.chunk_index, c.content, c.page_no, d.id AS document_id, d.filename")
_FROM = (" FROM embeddings e JOIN chunks c ON c.id = e.chunk_id JOIN documents d ON d.id = c.document_id"
         " WHERE d.user_id = ? AND e.model = ?")


def _doc_filter(document_ids):
    if not document_ids:
        return "", []
    return " AND d.id IN (" + ",".join("?" * len(document_ids)) + ")", list(document_ids)


def load_vectors(conn, user_id: int, model: str, document_ids=None) -> list:
    """(SQLite) Kullanicinin parcalarini + vektorlerini getirir. Yalnizca ayni modelle uretilen vektorler
    karsilastirilabilir."""
    extra, extra_params = _doc_filter(document_ids)
    sql = "SELECT " + _CHUNK_COLUMNS + ", e.vector, e.dim" + _FROM + extra
    return [dict(r) for r in conn.execute(sql, [user_id, model] + extra_params)]


def nearest(conn, user_id: int, model: str, query_vec, top_k: int, document_ids=None) -> list:
    """(PostgreSQL) En yakin top_k parca, skora gore azalan. score = 1 - kosinus uzakligi = kosinus benzerligi."""
    extra, extra_params = _doc_filter(document_ids)
    q = _pg_vector(query_vec)
    dim = len(query_vec)
    sql = ("SELECT " + _CHUNK_COLUMNS + ", 1 - (e.vector <=> ?::vector) AS score" + _FROM
           + " AND e.dim = ?" + extra + " ORDER BY e.vector <=> ?::vector LIMIT ?")
    rows = conn.execute(sql, [q, user_id, model, dim] + extra_params + [q, top_k])
    return [dict(r) for r in rows]
