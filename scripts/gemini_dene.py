"""Gemini embedding'ini dener ve arama esigi (MIN_SCORE) icin olcum yapar.

Calistirma (.env icinde GEMINI_API_KEY yazili olmali):
    python -m scripts.gemini_dene
Belgede OLAN 5 ve OLMAYAN 5 soru icin en iyi benzerlik puanini yazar. Esik, "olan"larin en dusugunun altinda,
"olmayan"larin cogunun ustunde olmali. Anahtar ekrana YAZDIRILMAZ. 3 istek atar (ucretsiz kotadan cok az yer).
"""
import sys

import numpy as np

from app.services.embedder import EmbeddingError, GeminiEmbedder

PARCALAR = [
    "Madde 12. Ödevler, dönemin on ikinci haftasının cuma günü saat 17.00'ye kadar öğretim elemanına e-posta ile teslim edilir.",
    "Madde 13. Geç teslim edilen ödevden her gün için 10 puan düşülür; üç günden sonra ödev kabul edilmez.",
    "Madde 14. Bütünleme sınavına, final sınavına girmeyen ya da başarısız olan öğrenciler katılabilir.",
    "Madde 15. Devam zorunluluğu teorik derslerde yüzde yetmiş, uygulamalı derslerde yüzde sekseridir.",
    "Madde 16. Mazeret sınavı için sağlık raporu sınav tarihinden itibaren beş iş günü içinde bölüme teslim edilir.",
]
OLAN = ["Ödevi en geç ne zaman vermeliyim?", "Geç kalan ödev için puan kesilir mi?", "Bütünlemeye kimler girebilir?",
        "Derslere katılım zorunlu mu?", "Raporlu olursam sınava nasıl girerim?"]
OLMAYAN = ["Yemekhane ücreti ne kadar?", "Kütüphane kaçta kapanır?", "Yarın hava yağmurlu mu?",
           "En iyi futbol takımı hangisi?", "Python'da liste nasıl sıralanır?"]


def main() -> int:
    e = GeminiEmbedder()
    try:
        belge = e.embed_documents(PARCALAR)
        olan = e._embed(OLAN, "RETRIEVAL_QUERY")           # sorular soru turuyle (embed_query ile ayni ayar)
        olmayan = e._embed(OLMAYAN, "RETRIEVAL_QUERY")
    except EmbeddingError as err:
        print("Gemini hatası:", err)
        return 1
    print(f"Model {e.model_name}, boyut {belge.shape[1]}")
    en_iyi = lambda m: (m @ belge.T).max(axis=1)
    a, b = en_iyi(olan), en_iyi(olmayan)
    for q, s in zip(OLAN, a):
        print(f"  belgede VAR  {s:.3f}  {q}")
    for q, s in zip(OLMAYAN, b):
        print(f"  belgede YOK  {s:.3f}  {q}")
    print(f"VAR en düşük {a.min():.3f} | YOK en yüksek {b.max():.3f} -> eşik bu ikisinin arasında olmalı")
    return 0


if __name__ == "__main__":
    sys.exit(main())
