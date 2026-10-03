"""Benzerlik arama: soru vektorune en yakin parcalari bulur."""
import numpy as np

from app.core import config
from app.db import embeddings as embeddings_repo
from app.db.database import dialect
from app.services.embedder import EmbeddingError, get_embedder


def _build_matrix(rows) -> np.ndarray:
    """BLOB'lari tek seferde (n, dim) float32 matrisine cevirir.

    Hizli yol: tum baytlari birlestirip tek bir frombuffer + reshape. Satir satir np.vstack yapmaya gore
    olculen kazanc: 10 bin parcada ~4 kat, 50 bin parcada ~1,7 kat (384 boyut; olcum kendi makinende
    `python -m scripts.benchmark_search` ile tekrarlanabilir). Asil maliyet SQL'den vektorleri okumaktir;
    matris carpimi (milisaniyeler) ihmal edilebilir.
    """
    dim = rows[0]["dim"]
    if any(len(r["vector"]) != dim * 4 for r in rows):
        raise EmbeddingError("Bozuk vektör kaydı; belgeleri yeniden indeksleyin")
    return np.frombuffer(b"".join(r["vector"] for r in rows), dtype=np.float32).reshape(len(rows), dim)


def search(conn, user_id: int, query: str, top_k=None, document_ids=None, embedder=None) -> list:
    """Kullanicinin KENDI belgelerinde en benzer top_k parcayi (skora gore azalan) dondurur."""
    query = (query or "").strip()
    if not query:
        raise ValueError("Sorgu boş olamaz")
    if len(query) > config.MAX_QUESTION_CHARS:
        raise ValueError(f"Sorgu en fazla {config.MAX_QUESTION_CHARS} karakter olabilir")
    top_k = config.SEARCH_TOP_K if top_k is None else top_k
    if not 1 <= top_k <= 50:
        raise ValueError("top_k 1 ile 50 arasında olmalı")

    emb = embedder or get_embedder()
    if dialect(conn) == "postgres":           # bulut: benzerlik SQL'de (pgvector) hesaplanir
        rows = embeddings_repo.nearest(conn, user_id, emb.name, emb.embed_query(query), top_k, document_ids)
        return [{"chunk_id": r["chunk_id"], "document_id": r["document_id"], "filename": r["filename"],
                 "page_no": r["page_no"], "chunk_index": r["chunk_index"], "content": r["content"],
                 "score": float(r["score"])} for r in rows]

    rows = embeddings_repo.load_vectors(conn, user_id, emb.name, document_ids)
    if not rows:
        return []
    q = emb.embed_query(query)
    matrix = _build_matrix(rows)
    if matrix.shape[1] != q.shape[0]:
        raise EmbeddingError("Vektör boyutları uyuşmuyor; belgeleri yeniden indeksleyin")

    scores = matrix @ q                      # normalized vektorler: nokta carpimi = kosinus benzerligi
    k = min(top_k, len(rows))
    top = np.argpartition(-scores, k - 1)[:k]
    top = top[np.argsort(-scores[top])]
    results = []
    for i in top:
        r = rows[int(i)]
        results.append({
            "chunk_id": r["chunk_id"], "document_id": r["document_id"], "filename": r["filename"],
            "page_no": r["page_no"], "chunk_index": r["chunk_index"], "content": r["content"],
            "score": float(scores[i]),
        })
    return results
