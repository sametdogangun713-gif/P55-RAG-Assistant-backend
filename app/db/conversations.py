"""conversations, messages ve message_sources tablolari icin CRUD."""

DEFAULT_TITLE = "Yeni sohbet"


def create_conversation(conn, user_id: int, title: str = DEFAULT_TITLE) -> dict:
    new_id = conn.execute("INSERT INTO conversations (user_id, title) VALUES (?, ?) RETURNING id",
                          (user_id, title)).fetchone()[0]
    conn.commit()
    return get_conversation(conn, new_id)


def get_conversation(conn, conv_id: int):
    row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
    return dict(row) if row else None


def list_conversations(conn, user_id: int) -> list:
    rows = conn.execute(
        "SELECT c.id, c.title, c.created_at,"
        " (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) AS message_count,"
        " COALESCE((SELECT MAX(m.created_at) FROM messages m WHERE m.conversation_id = c.id), c.created_at) AS last_activity"
        " FROM conversations c WHERE c.user_id = ? ORDER BY last_activity DESC, c.id DESC", (user_id,))
    return [dict(r) for r in rows]


def rename_conversation(conn, conv_id: int, title: str) -> bool:
    cur = conn.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conv_id))
    conn.commit()
    return cur.rowcount > 0


def delete_conversation(conn, conv_id: int) -> bool:
    """Mesajlari ve mesaj kaynaklari ON DELETE CASCADE ile silinir."""
    cur = conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    conn.commit()
    return cur.rowcount > 0


def set_summary(conn, conv_id: int, summary: str, upto_message_id: int) -> None:
    conn.execute("UPDATE conversations SET summary = ?, summary_upto = ? WHERE id = ?",
                 (summary, upto_message_id, conv_id))
    conn.commit()


def add_message(conn, conversation_id: int, role: str, content: str, status=None, grounded=None,
                latency_ms=None, best_score=None) -> int:
    new_id = conn.execute(
        "INSERT INTO messages (conversation_id, role, content, status, grounded, latency_ms, best_score)"
        " VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id",
        (conversation_id, role, content, status, None if grounded is None else int(bool(grounded)),
         latency_ms, best_score)).fetchone()[0]
    conn.commit()
    return new_id


def list_messages(conn, conversation_id: int) -> list:
    rows = conn.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY id", (conversation_id,))
    return [dict(r) for r in rows]


def add_message_sources(conn, message_id: int, sources) -> int:
    """sources: [{'n', 'chunk_id', 'score'}, ...]"""
    conn.executemany(
        "INSERT INTO message_sources (message_id, chunk_id, score, n) VALUES (?, ?, ?, ?)"
        " ON CONFLICT DO NOTHING",
        [(message_id, s["chunk_id"], s.get("score"), s.get("n")) for s in sources])
    conn.commit()
    return len(sources)


def get_message_sources(conn, message_id: int) -> list:
    rows = conn.execute(
        "SELECT ms.n, ms.score, c.id AS chunk_id, c.content, c.page_no, d.id AS document_id, d.filename"
        " FROM message_sources ms JOIN chunks c ON c.id = ms.chunk_id JOIN documents d ON d.id = c.document_id"
        " WHERE ms.message_id = ? ORDER BY ms.n", (message_id,))
    return [dict(r) for r in rows]
