"""Hugging Face embedding'ini dener ve (kuruluysa) yerel modelle karsilastirir.

Calistirma (.env icinde HF_TOKEN yazili olmali):
    python -m scripts.hf_dene
Beklenen: boyut 384; ayni cumle icin HF ve yerel vektorlerin benzerligi ~1,00 (ayni model).
Anahtar ekrana YAZDIRILMAZ.
"""
import sys

import numpy as np

from app.services.embedder import EmbeddingError, HFEmbedder, LocalEmbedder

CUMLELER = ["Vektör veritabanı benzer metinleri bulur.",
            "Benzerlik araması için gömme vektörleri kullanılır.",
            "Bugün hava çok güzel."]


def main() -> int:
    hf = HFEmbedder()
    try:
        v = hf.embed_documents(CUMLELER)
    except EmbeddingError as e:
        print("Hugging Face hatası:", e)
        return 1
    print(f"HF: {v.shape[0]} vektör, boyut {v.shape[1]}")
    print(f"  1-2 benzerlik (ilgili):  {float(v[0] @ v[1]):.3f}")
    print(f"  1-3 benzerlik (ilgisiz): {float(v[0] @ v[2]):.3f}")
    try:
        yerel = LocalEmbedder().embed_documents(CUMLELER)
    except EmbeddingError:
        print("Yerel model kurulu değil; karşılaştırma atlandı.")
        return 0
    ayni = [float(a @ b) for a, b in zip(v, yerel)]
    print("HF ile yerel model aynı cümlede:", ", ".join(f"{x:.3f}" for x in ayni), "(1,00'a yakın olmalı)")
    return 0 if min(ayni) > 0.95 and np.isfinite(v).all() else 1


if __name__ == "__main__":
    sys.exit(main())
