"""Indeksleme: bir belgenin parcalari icin embedding uretip veritabanina yazar."""
from app.db import chunks as chunks_repo
from app.db import documents as documents_repo
from app.db import embeddings as embeddings_repo
from app.services.embedder import get_embedder

BATCH_SIZE = 64


def index_document(conn, doc_id: int, embedder=None) -> int:
    """Belgenin tum parcalarini (yeniden) vektorlestirir; durumu 'indexed' yapar. Yazilan vektor sayisini dondurur.

    Embedding hatasi (EmbeddingError) cagirana yukselir. Once TUM yeni vektorler uretilir, sonra eskiler
    silinip yenileri yazilir: uretim yarida patlarsa eski vektorler yerinde kalir.
    """
    emb = embedder or get_embedder()
    chunk_list = chunks_repo.list_chunks(conn, doc_id)
    if not chunk_list:
        raise ValueError("Belgede parça yok")
    batches = []
    for i in range(0, len(chunk_list), BATCH_SIZE):
        batch = chunk_list[i:i + BATCH_SIZE]
        matrix = emb.embed_documents([c["content"] for c in batch])   # hata burada olursa DB'ye dokunulmaz
        batches.append(([c["id"] for c in batch], matrix))
    embeddings_repo.delete_embeddings_for_document(conn, doc_id)
    total = 0
    for chunk_ids, matrix in batches:
        total += embeddings_repo.save_embeddings(conn, chunk_ids, matrix, emb.name)
    documents_repo.set_status(conn, doc_id, "indexed")
    return total
