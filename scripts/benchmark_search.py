"""Arama hizi olcumu: 'Arama yavassa ne yaptin?' sorusuna kanit.

Calistirma:  python -m scripts.benchmark_search
Bellekte sentetik (rastgele) vektorlerle farkli buyuklukte parca sayilarinda aramayi zamanlar.
"""
import time

import numpy as np

from app.db import database, embeddings as emb_repo
from app.services import vector_search
from app.services.embedder import Embedder


class SahteEmbedder(Embedder):
    name = "bench"

    def __init__(self, dim):
        self.dim = dim
        self.rng = np.random.default_rng(1)

    def embed_documents(self, texts):
        return self.rng.standard_normal((len(texts), self.dim)).astype(np.float32)


def hazirla(n, dim):
    conn = database.get_connection(":memory:")
    database.run_migrations(conn)
    conn.execute("INSERT INTO users (email, password_hash) VALUES ('b@example.com', 'x')")
    conn.execute("INSERT INTO documents (user_id, filename, status) VALUES (1, 'b.txt', 'indexed')")
    conn.executemany("INSERT INTO chunks (document_id, chunk_index, content) VALUES (1, ?, ?)",
                     [(i, f"parca {i}") for i in range(n)])
    rng = np.random.default_rng(0)
    m = rng.standard_normal((n, dim)).astype(np.float32)
    m /= np.linalg.norm(m, axis=1, keepdims=True)
    ids = [r[0] for r in conn.execute("SELECT id FROM chunks ORDER BY id")]
    emb_repo.save_embeddings(conn, ids, m, "bench")
    return conn


def olc(conn, emb, tekrar=3):
    en_iyi = 1e9
    for _ in range(tekrar):
        t = time.perf_counter()
        vector_search.search(conn, 1, "deneme sorgusu", 5, embedder=emb)
        en_iyi = min(en_iyi, time.perf_counter() - t)
    return en_iyi * 1000


if __name__ == "__main__":
    dim = 384
    emb = SahteEmbedder(dim)
    print(f"Vektor boyutu: {dim}")
    print(f"{'parca sayisi':>14} | {'arama (ms)':>10}")
    for n in (1_000, 10_000, 50_000):
        conn = hazirla(n, dim)
        print(f"{n:>14,} | {olc(conn, emb):>10.1f}")
        conn.close()
