"""Indeksleme: bir belgenin parcalari icin embedding uretip veritabanina yazar.

Iki yol var:
- index_document: hepsini tek seferde (yerelde; kucuk belgeler, testler).
- index_next: zaman butceli, KALDIGI YERDEN devam eden indeksleme. Vercel'de bir istek en fazla 300 sn
  surebildigi icin buyuk belge birden cok kisa istekte indekslenir; arayuz bitene kadar tekrar cagirir.
  "Bekleyen parca" = bu modelle vektoru olmayan parca. Boylece model degisince (eski vektorler baska
  modelle) ya da yarida kalinca hicbir sey silinmeden eksik olanlar tamamlanir.
"""
import time

from app.db import chunks as chunks_repo
from app.db import documents as documents_repo
from app.db import embeddings as embeddings_repo
from app.services.embedder import get_embedder

BATCH_SIZE = 64
_now = time.monotonic          # sure olcumu; testler sahte saatle degistirir (Windows saati ~15 ms adimli)


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


def progress(conn, doc_id: int, model: str) -> dict:
    """{'indexed': bu modelle vektoru olan parca, 'total': tum parcalar, 'done': bitti mi}"""
    total = chunks_repo.count_chunks(conn, doc_id)
    indexed = embeddings_repo.count_embeddings(conn, doc_id, model=model)
    return {"indexed": indexed, "total": total, "done": total > 0 and indexed >= total}


def index_next(conn, doc_id: int, embedder=None, budget_seconds: float = 0, clock=None) -> dict:
    """Bekleyen parcalari BATCH_SIZE'lik gruplar halinde vektorlestirir; her grup hemen kaydedilir.

    budget_seconds > 0 ise sure dolunca durur (bir grup yarida kesilmez; butce asilabilir ama en fazla bir grup).
    budget_seconds = 0 -> hepsi bitene kadar surer. Hepsi bitince belge 'indexed' olur, aksi halde 'chunked'
    kalir (arama o ana kadar indekslenen parcalarla calisir). EmbeddingError cagirana yukselir; o ana kadar
    kaydedilenler korunur, tekrar cagrilinca kalan yerden devam edilir.
    """
    emb = embedder or get_embedder()
    clock = clock or _now
    if chunks_repo.count_chunks(conn, doc_id) == 0:
        raise ValueError("Belgede parça yok")
    started = clock()
    while True:
        batch = chunks_repo.list_unindexed_chunks(conn, doc_id, emb.name, BATCH_SIZE)
        if not batch:
            break
        matrix = emb.embed_documents([c["content"] for c in batch])
        embeddings_repo.save_embeddings(conn, [c["id"] for c in batch], matrix, emb.name)
        if budget_seconds and clock() - started >= budget_seconds:
            break
    state = progress(conn, doc_id, emb.name)
    documents_repo.set_status(conn, doc_id, "indexed" if state["done"] else "chunked")
    return state
