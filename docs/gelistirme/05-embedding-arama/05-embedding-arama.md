# Adım 5 — Embedding ve vektör arama

> Ders planındaki karşılığı: **Hafta 7**. Bu belge eski `hafta-07/README.md` ve `hafta-07/aciklama.md` dosyalarının birleşimidir.

## Ne yapıldı

### Amaç
Belge parçalarını vektöre çevirip (embedding) benzerlik araması yapan modülü geliştirmek ve belge yüklemeyle birleştirmek.

### Bu hafta eklenen / değişen dosyalar
| Dosya | Ne işe yarıyor |
|---|---|
| `app/services/embedder.py` | `LocalEmbedder` (sentence-transformers, çok dilli, ücretsiz) ve `HashingEmbedder` (indirme gerektirmeyen yedek) |
| `app/db/embeddings.py` | Vektörleri `float32` BLOB olarak kaydetme/yükleme |
| `app/services/indexing.py` | Bir belgenin parçalarını vektörleştirip yazma |
| `app/services/vector_search.py` | Soru vektörüne en yakın parçaları bulma (kosinüs benzerliği) |
| `app/services/documents.py` | Yüklemeden sonra otomatik indeksleme, `reindex_document` |
| `app/api/search.py` | `POST /search` |
| `app/api/documents.py` | `POST /documents/{id}/reindex` |
| `tests/__init__.py` | Testlerde hızlı `hash` embedder kullanılır (model indirme yok) |
| `tests/test_belge.py` | Durum artık `indexed` de olabilir (küçük güncelleme) |

### Çalıştırma ve demo
**Hızlı deneme (indirme yok):** `.env` içinde `EMBEDDING_BACKEND=hash`
**Asıl kullanım (anlamsal arama):**
```bat
pip install -r requirements.txt
:: .env: EMBEDDING_BACKEND=local
```
İlk belge yüklemesinde çok dilli model internetten indirilir (yüzlerce MB, birkaç dakika sürebilir) ve sonraki çalıştırmalarda önbellekten gelir.
```bat
curl -X POST http://127.0.0.1:8000/search -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d "{\"query\":\"embedding nedir\",\"top_k\":3}"
```
Gösterilecek: yüklenen belgenin `status: indexed` olması; farklı sorulara farklı parçaların, skorlarıyla birlikte gelmesi; başka kullanıcının belgelerinin görünmemesi.

Testler: `pytest tests/test_vektor.py`

### Kendi yapacakların
1. Kosinüs benzerliğini **numpy kullanmadan** (saf Python döngüsüyle) kendin yaz; `vector_search` sonucuyla aynı sıralamayı verdiğini göster.
2. Aynı 5 soruyu hem `hash` hem `local` backend ile dene; ilk sonucun doğru parça olup olmadığını bir tabloya yaz (gözlemin = sözlü malzemesi).
3. Belgede **olan** 5 ve **olmayan** 5 soru için en yüksek skoru not et. Bu sayılar Hafta 10'da "belgede cevap yok" eşiğini (`MIN_SCORE`) seçmek için gerekecek.
4. `docs/ai-kullanim-gunlugu/ai-kullanim-gunlugu.md` boş alanlarını doldur.

### Kontrol listesi
- [x] Gömme ve Vektör Arama çalışıyor
- [x] Doğrulama/iş kuralları uygulanıyor (boş sorgu, `top_k` sınırı, yalnız kendi belgeleri)
- [x] Önceki modüllerle tutarlı (yükleme → parça → vektör → arama)

## Kod açıklaması

### Büyük resim
`Belge → parçalar (Hafta 6) → her parça için vektör → SQLite'ta sakla`; soru gelince `soru → vektör → en benzer parça vektörleri`.

### Embedding nedir?
Bir metni, anlamını temsil eden sayı dizisine (vektör) çeviren modeldir. Anlamca yakın metinlerin vektörleri uzayda yakındır. "Araba" ile "otomobil"
farklı kelimelerdir ama vektörleri yakındır; klasik kelime aramasının yakalayamadığı budur.

### `embedder.py`
- **`LocalEmbedder`**: `sentence-transformers` kütüphanesiyle çok dilli (Türkçe dahil) yerel bir model yükler (`paraphrase-multilingual-MiniLM-L12-v2`). İnternet yalnızca ilk indirmede gerekir, API anahtarı/ücret yok.
  Model tembel yüklenir (ilk kullanımda) ve `get_embedder()` ile tek örnek paylaşılır. `normalize_embeddings=True` → vektör uzunluğu 1.
- **`HashingEmbedder`** (yedek): kelimeleri, kelime çiftlerini ve harf 4-gramlarını `crc32` ile sabit boyutlu vektöre dağıtır ("hashing trick").
  **Anlamsal değil biçimsel** benzerlik yakalar (ortak kelime/kök). Testler ve hızlı deneme için; gerçek kalite için `local` kullanılır. (Python'un `hash()` fonksiyonu her çalıştırmada değiştiği için `zlib.crc32` seçildi.)
- `tr_lower`: Türkçe'de `I → ı`, `İ → i`; standart `.lower()` bunu yanlış yapar.
- **Önemli:** Vektör kaydedilirken `embedder.name` de saklanır; arama yalnızca **aynı modelle** üretilmiş vektörleri karşılaştırır (farklı modelin vektörleri aynı uzayda değildir).

### `db/embeddings.py`
Vektör `numpy float32` dizisinin ham baytları (`tobytes()`) olarak `embeddings.vector` BLOB'una yazılır, `np.frombuffer` ile geri okunur.
384 boyutlu bir vektör ≈ 1.5 KB. `chunk_id UNIQUE` → bir parçanın tek vektörü (1-1).

### `vector_search.search`
1. Sorgu boşsa / `top_k` 1–50 dışındaysa `ValueError`.
2. Kullanıcının vektörleri SQL ile çekilir (`WHERE d.user_id = ? AND e.model = ?`) → **başkasının belgesi aramaya hiç girmez**.
3. Vektörler tek bir matrise dizilir; `scores = matris @ soru_vektörü`. Vektörler normalize olduğu için bu nokta çarpımı **kosinüs benzerliğidir** (−1..1; büyük = benzer).
4. `argpartition` ile en iyi k bulunur, `argsort` ile sıralanır (tüm diziyi sıralamaktan ucuz).

### `indexing.index_document`
Önce tüm yeni vektörler üretilir; ancak hepsi başarılıysa eskiler silinip yenileri yazılır. Üretim yarıda patlarsa eski vektörler bozulmaz (testle kanıtlandı).
`documents._try_index`: embedding hatası olursa belge `failed` + açıklayıcı hata alır ama **parçalar korunur**; sorun giderilince `POST /documents/{id}/reindex` ile yeniden denenir.

### Sözlü sınav soruları ve cevap iskeleti
**1) Gömmeyi nasıl ürettin?** Her parçayı yerel çok dilli bir sentence-transformers modeline verip 384 boyutlu, birim uzunlukta vektör aldım; yükleme sırasında otomatik, model değişince `reindex` ile. Test/hızlı deneme için indirme gerektirmeyen hash tabanlı yedek var.
**2) Benzerliği nasıl ölçtün?** Kosinüs benzerliği: vektörler normalize olduğundan soru vektörü ile parça matrisinin nokta çarpımı yeterli. Skora göre azalan sıralayıp en iyi `top_k`'yı döndürüyorum.
**3) Bu modülün verisini nasıl modelledim?** `embeddings` tablosu: `chunk_id` (UNIQUE, 1-1), `vector` (BLOB), `dim`, `model`. Model adını saklamak, farklı modellerin vektörlerinin karışmasını önler.
**4) Hangi iş kuralını neden koydum?** Aramada yalnızca kullanıcının kendi belgeleri (gizlilik); `top_k` ≤ 50 (kaynak tüketimi); boş sorgu reddi; model eşleşmesi; embedding hatasında parçaların korunması.
**5) Diğer modüllerle entegrasyon?** Hafta 6'daki yükleme hattının sonuna eklendi (`chunked → indexed`); uçlar Hafta 5'teki token kontrolüne bağlı; Hafta 10'da RAG, `search` sonucunu LLM'e bağlam olarak verecek.

### Sık yapılan hatalar
Farklı modellerin vektörlerini karşılaştırmak · normalize etmemek · her aramada tüm belgeleri yeniden vektörleştirmek (burada vektörler bir kez üretilip saklanıyor) · başkasının belgelerini aramaya katmak.

### Dürüst not
Bu hafta kodunu burada hash yedeğiyle test ettim; `local` (sentence-transformers) modelini bu ortamda çalıştıramadım (internet/paket yok). Kendi bilgisayarında ilk çalıştırmada model indirme ve süre konusunda dikkatli ol; sorun olursa `EMBEDDING_BACKEND=hash` ile devam edebilirsin.
