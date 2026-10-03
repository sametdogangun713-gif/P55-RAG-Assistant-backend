# Adım 4 — Belge yükleme, ayrıştırma ve parçalama

> Ders planındaki karşılığı: **Hafta 6**. Bu belge eski `hafta-06/README.md` ve `hafta-06/aciklama.md` dosyalarının birleşimidir.

## Ne yapıldı

### Amaç
Belge yükleme, metin ayrıştırma ve parçalama (chunking) modülünü geliştirmek.

### Bu hafta eklenen / değişen dosyalar
| Dosya | Ne işe yarıyor |
|---|---|
| `app/services/parser.py` | TXT / PDF / DOCX dosyasından metin çıkarır (sayfa numarasıyla) |
| `app/services/chunker.py` | Metni cümle sınırlarını koruyarak, örtüşen parçalara böler |
| `app/services/documents.py` | Yükleme iş kuralları, sahiplik kontrolü, silme |
| `app/api/documents.py` | `POST /documents`, `GET /documents`, `GET /documents/{id}`, `GET /documents/{id}/chunks`, `DELETE /documents/{id}` |
| `app/core/config.py`, `.env.example` | `MAX_UPLOAD_MB`, `CHUNK_SIZE`, `CHUNK_OVERLAP` |
| `requirements*.txt` | python-multipart, pypdf, python-docx (+ reportlab testler için) |

### Çalıştırma ve demo
```bat
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Önce `POST /auth/login` ile token al (Hafta 5), sonra:
```bat
curl -X POST http://127.0.0.1:8000/documents -H "Authorization: Bearer TOKEN" -F "file=@ornek.txt"
curl http://127.0.0.1:8000/documents -H "Authorization: Bearer TOKEN"
curl "http://127.0.0.1:8000/documents/1/chunks?limit=5" -H "Authorization: Bearer TOKEN"
```
Gösterilecek: yüklenen belge → `status: chunked`, parça sayısı, parçaların içeriği; `.exe` yüklemenin 400, başkasının belgesinin 404 vermesi.

Testler: `pytest tests/test_belge.py`

### Kendi yapacakların
1. `chunker.split_text` yerine kendi basit yöntemini yaz (örn. sabit karakter penceresi) ve aynı belgede parça sayısı/kalitesini karşılaştır. Hangisini neden seçtiğini yaz.
2. Yeni bir iş kuralı ekle: **kullanıcı başına en fazla 20 belge** (aşılırsa 400). Servis fonksiyonuna ve teste ekle.
3. Kendi belgenle (sentetik/kişisel veri içermeyen) dene; farklı `CHUNK_SIZE` değerlerinde parça sayısını not al.
4. `docs/ai-kullanim-gunlugu.md` boş alanlarını doldur.

### Kontrol listesi
- [x] Belge Yükleme ve Ayrıştırma çalışıyor
- [x] Doğrulama / iş kuralları uygulanıyor (tür, boyut, içerik-uzantı uyumu)
- [x] Sahiplik kontrolü var (başkasının belgesi 404)
- [x] Önceki modüllerle tutarlı (token şart, veri DB'de)

## Kod açıklaması

### Yükleme akışı (`services/documents.upload_document`)
1. `sanitize_filename`: `../../x.txt` → `x.txt` (yol bileşenleri ve kontrol karakterleri atılır).
2. İş kuralları: uzantı beyaz listede (`.txt .pdf .docx`) · dosya boş değil · boyut ≤ `MAX_UPLOAD_MB` · içerik uzantıyla uyumlu
   (PDF `%PDF-` ile, DOCX zip imzası `PK` ile başlar → "virus.exe"yi "a.pdf" diye yükleme hilesi geçmez).
3. Diske `uuid + uzantı` adıyla yazılır; kullanıcının verdiği ad yalnızca etiket olarak DB'de tutulur.
4. `documents` satırı açılır (`uploaded`), `parser` metni çıkarır, `chunker` parçalar, parçalar DB'ye yazılır → durum `chunked`.
5. Metin çıkmazsa (taranmış PDF) ya da dosya bozuksa durum `failed` + açıklayıcı `error`; sunucu hatası (500) fırlatılmaz.

### `parser.py`
- **TXT:** önce UTF-8, olmazsa `cp1254` (eski Türkçe Windows kodlaması) denenir → Türkçe karakterler bozulmaz.
- **PDF:** `pypdf` her sayfanın metnini çıkarır, `(sayfa_no, metin)` döner. Parola korumalı veya bozuk PDF → `ParseError`. Tek sayfa bozuksa o sayfa boş sayılır.
- **DOCX:** `python-docx` paragrafları ve tablo hücrelerini okur (tablolar paragraflardan sonra eklenir; orijinal sıra tam korunmaz — bilinen sınır).

### `chunker.py` (en önemli algoritma)
Amaç: embedding modeli kısa metinlerde iyi çalışır ve arama sonucunda "ilgili küçük parça" döndürmek isteriz.
- Metin **paragraf → cümle** birimlerine ayrılır (`(?<=[.!?…])\s+` ile). Cümleler bölünmez, bu yüzden anlam bütünlüğü korunur.
- Cümleler `chunk_size` (600 karakter) dolana kadar birleştirilir.
- **Örtüşme (overlap, ~100 karakter):** yeni parça, öncekinin son cümlelerinden başlar. Böylece iki parçanın sınırına denk gelen bilgi kaybolmaz.
- Tek başına 600'den uzun bir "cümle" (noktalamasız dev metin) kelime sınırından `_hard_split` ile kesilir.
- Her sayfa ayrı parçalanır → parçanın `page_no` değeri doğru kalır (kaynak gösterirken kullanılacak). Sınır: sayfayı bölen bir cümle iki parçaya ayrılır.

**Parça boyutu neden 600?** Çok küçük (örn. 100) parça bağlam taşımaz; çok büyük (örn. 3000) parça birçok konuyu karıştırır, embedding "bulanıklaşır" ve LLM'e gereksiz metin gider.
Yerel çok dilli embedding modeli (Hafta 7) yaklaşık 128–256 token görür; 600 Türkçe karakter bu sınıra sığar. Değer `.env`'den değiştirilebilir.

### Veri modeli
`documents` (kullanıcıya bağlı, `status`/`error` ile durum) → `chunks` (belgeye bağlı, `chunk_index`, `page_no`). Silinince parçalar CASCADE ile gider.

### Sözlü sınav soruları ve cevap iskeleti
**1) Belgeyi nasıl parçaladın?** Metni paragraf/cümle birimlerine ayırıp 600 karaktere kadar birleştirdim, parçalar arası ~100 karakter örtüşme bıraktım; sayfa numarasını korudum.
**2) Parça boyutunu neye göre seçtin?** Embedding modelinin görebildiği uzunluk ve "tek konu" ilkesi: küçük = bağlamsız, büyük = bulanık vektör. `CHUNK_SIZE` ayarlanabilir; deneyerek (parça sayısı, arama kalitesi) belirlenir.
**3) Bu modülün verisini nasıl modelledin?** `documents` 1-N `chunks`; durum alanı (`uploaded/chunked/indexed/failed`) işlem hattının neresinde olduğunu gösterir; `stored_name` ile gerçek dosya adı ayrıdır.
**4) Hangi iş kuralını neden koydum?** Tür beyaz listesi ve içerik-uzantı uyumu (güvenlik), boyut sınırı (kaynak tüketimi), UUID dosya adı (yol saldırısı), 404 ile sahiplik (başkasının belgesinin varlığı bile sızmasın).
**5) Diğer modüllerle entegrasyon?** Uç noktalar `get_current_user` ile korunur (Hafta 5); belge `user_id` ile kullanıcıya bağlanır (Hafta 4); parçalar Hafta 7'de embedding'e, Hafta 10'da kaynak gösterimine girdi olur.

### Sık yapılan hatalar
Doğrulamayı atlamak · erişim/sahiplik kontrolünü unutmak · ilişkili kayıtları (dosya + parçalar) birlikte silmemek · kullanıcının verdiği dosya adını doğrudan diske yazmak.
