# Test Raporu

## 0. Son durum (2026-10-04 — sürüm 0.18.1, SQLite + PostgreSQL)
Sayılar gerçek çalıştırmadan alındı (Windows 11, Python 3.12.10, FastAPI 0.142.2, pytest 9.1.1, pytest-cov 7.1.0).

| Takım | Veritabanı | Sonuç | Kapsam (`--cov=app`) |
|---|---|---|---|
| Backend `pytest` | SQLite (bellekte, varsayılan) | **319 geçti, 2 atlandı, 0 başarısız** | **%92** |
| Backend `pytest` + `TEST_PG_URL` | PostgreSQL 16.2 + pgvector (yerel, `pgserver` paketi) | **320 geçti, 1 atlandı, 0 başarısız** | **%95** |
| Frontend `python -m unittest discover -s tests` | — | **26 geçti** | — |

- 2026-10-03 → 10-04 arasında eklenen testler: e-posta doğrulama, Hesabım, arama kalitesi, parça parça indeksleme, genel
  sohbet, PDF rapor, kişisel API anahtarı (19: bildirim e-postası ve yönetici iptali dahil). Önceki ölçüm 240 / 241 / 16 idi.
- Canlı ortam (2026-10-04, giriş gerektirmeyen kontroller): `/health` → `database: postgres`; korumalı uçlar
  (`/auth/me`, `/documents`, `/reports/usage.pdf`, `/admin/users`, `/admin/tokens`) girişsiz 401; CORS yalnızca frontend
  adresine izin veriyor; frontend en son sürümü (`admin.js?v=36`) sunuyor.

- Atlananlar: `test_vektor.py` — sentence-transformers *kurulu değilken* verilen hatayı sınar, paket kurulu olduğu için atlanır.
  `test_bulut.py::PgVectorTests` — yalnızca PostgreSQL'de anlamlı; SQLite koşusunda atlanır.
- SQLite koşusunda kapsamın düşük görünmesinin nedeni: PostgreSQL'e özgü satırlar (`PgConnection`, pgvector araması) yalnızca PostgreSQL koşusunda çalışır. İkisinin birleşimi kodun neredeyse tamamını kapsar.
- Yeni testler (`tests/test_bulut.py`, 21): Hugging Face istek biçimi / yeniden deneme / anahtar sızmaması; Supabase Storage imzalı adres, yol sahipliği, gerçek boyut kontrolü, silme; HTTP üzerinden depo akışı; CORS; e-postanın yanıttan önce gönderilmesi; **pgvector ile numpy aynı sonucu veriyor**.
- PostgreSQL koşusu **gerçek bir hata** buldu (NUL karakteri → 500): [`duzeltilen-hatalar.md`](duzeltilen-hatalar.md).
- Elle deneme (2026-10-03): frontend `http://localhost:5500` + backend `http://127.0.0.1:8000` (PostgreSQL'e bağlı) ayrı adreslerde; tarayıcıda kayıt → giriş → yükleme → arama → rapor çalıştı, CORS ön istekleri (OPTIONS) 200, konsol temiz.
- **Test edilmeyen (otomatik testlerde):** gerçek Supabase / Hugging Face / Vercel. İstek biçimleri sahte sunucularla doğrulandı; canlıda elle denenenler [`dagitim.md`](dagitim.md) ve AI günlüğünde.

Aşağıdaki bölümler Hafta 13 (2026-10-02/03) ölçümüdür; tarihçe olarak korunuyor.

---

## Hafta 13 ölçümü (tarihçe)

> Ölçüm tarihi: **2026-10-02**; test sayısı ve toplam kapsam **2026-10-03**'te yeniden ölçüldü (Hafta 9'a Groq desteği eklendikten sonra). Sayılar gerçek çalıştırmadan alındı (uydurma/tahmini değer yok).
> Hafta 13 teslim edilirken testleri **yeniden çalıştır** ve değişen sayıları güncelle.

## 1. Ortam
| | |
|---|---|
| İşletim sistemi | Windows 11 Pro |
| Python | 3.12.10 (sanal ortam `venv`) |
| Çerçeveler | FastAPI 0.142.2, Starlette 1.7.0, pytest 9.1.1, pytest-cov 7.1.0 |
| Embedding (testlerde) | `hash` (`tests/__init__.py` ayarlar; hızlı, indirme yok) |
| Embedding (elle denemede) | `local` → `paraphrase-multilingual-MiniLM-L12-v2` |
| LLM API | Claude **denenmedi** (ücretli, anahtar yok). Groq: 2026-10-03'te gerçek çağrı `404` verdi (model kaldırılmış) → varsayılan model değiştirildi; başarılı çağrı yeni anahtarla yapılacak. Testler yerel sahte HTTP sunucusuna karşı koşar |

Çalıştırma:
```bat
venv\Scripts\activate
pytest
pytest --cov=app --cov-report=term-missing
```

## 2. Otomatik test sonuçları
**191 test → 190 geçti, 1 atlandı, 0 başarısız** (2026-10-03, hafta 13 durumu). İlk ölçüm (2026-10-02): 177 test → 176 geçti, 1 atlandı; fark Hafta 9'a eklenen Groq testlerinden (+13) ve gerçek modelle bulunan alıntı biçimi hatasının testinden (+1, Hafta 10).

| Dosya | Test | Ne sınıyor |
|---|---:|---|
| `tests/test_iskelet.py` | 6 | İskelet, `/health`, klasör yapısı |
| `tests/test_veritabani.py` | 12 | Migration, CRUD, yabancı anahtar / CASCADE |
| `tests/test_kimlik.py` | 19 | scrypt, JWT, roller, kilitleme |
| `tests/test_belge.py` | 24 | Yükleme doğrulama, ayrıştırma (TXT/PDF/DOCX), parçalama |
| `tests/test_vektor.py` | 21 | Embedding, kosinüs benzerliği, kullanıcı izolasyonu |
| `tests/test_uctan_uca.py` | 5 | Uçtan uca akış + **gerçek HTTP (`TestClient`)** + arayüzde `innerHTML` yasağı |
| `tests/test_llm.py` | 15 | Claude istemcisi: yeniden deneme, zaman aşımı, hata eşleme, anahtar sızmaması |
| `tests/test_groq.py` | 13 | Groq istemcisi: OpenAI uyumlu istek, sağlayıcı seçimi, düşünce (`<think>`) temizliği |
| `tests/test_rag.py` | 23 | Kaynaklı yanıt, `[n]` doğrulama, `BILGI_YOK`, eşik |
| `tests/test_sohbet.py` | 19 | Sohbet geçmişi, bağlam sınırı, özetleme |
| `tests/test_rapor.py` | 16 | Rapor sayıları (elle hesaplanmış beklenen değerler), CSV, yönetim |
| `tests/test_sinir_durumlari.py` | 18 | **Sınır durumları ve hata senaryoları** (aşağıda) |

**Atlanan test:** `tests/test_vektor.py:63`. Bu test sentence-transformers **kurulu değilken** anlaşılır bir hata verildiğini sınar; paket kurulu olduğu için kendini atlar. Beklenen davranış.

**Kalan uyarılar (2):** Biri Starlette'in kendi iç uyarısı (`httpx` → `httpx2`). Diğeri, "başka anahtarla imzalanmış token reddedilir" testinin bilerek kısa bir anahtar kullanmasından geliyor.

### Hafta 13 sınır testleri (18)
| Grup | Senaryo | Neden önemli |
|---|---|---|
| Parçalama | 2 MB'tan büyük metin 10 sn altında parçalanır, hiçbir parça sınırı aşmaz | Performans / sonsuz döngü riski |
| | Yalnızca noktalama, yalnızca boşluk | Boş parça üretmemeli |
| | Boş PDF sayfaları atlanır, sayfa numaraları korunur | Kaynak gösterimi doğru kalmalı |
| Yükleme | 200 karakterlik dosya adı → uzantı korunur | **Hata 1** |
| | Yalnızca boşluk içeren dosya → `failed` | Boş belge indekslenmemeli |
| | İkili (binary) çöp veri `.txt` diye → çökmez | Kötü girdi |
| | Emoji / Türkçe karakterli dosya adı | Unicode |
| | DOCX zip bombası → reddedilir | **Hata 5** |
| Güvenlik | `verify_password(None / bozuk biçim / sayı)` → `False` | **Hata 2** |
| | Süresi tam dolan token geçersiz | Sınır değer |
| | 200 farklı e-postayla başarısız giriş → sayaç sınırlı | **Hata 3** |
| | Üretimde varsayılan / kısa `SECRET_KEY` → başlatma reddedilir | **Hata 4** |
| Arama | 5000 karakterlik sorgu → 400 | **Hata 6** |
| | Embedding hatası → `EmbeddingError` (API'de 503) | Hata yönetimi |
| | Emoji + SQL enjeksiyonu + `<script>` içeren sorgu → çökmez | Kötü girdi |
| | Hiç belgesi olmayan kullanıcı → boş liste | Boş durum |
| Veritabanı | Hatalı migration → tamamen geri alınır, kaydedilmez | Bütünlük |
| | 8 iş parçacığı × 25 eşzamanlı yazma → kilitlenme yok, 200 kayıt | Eşzamanlılık |

## 3. Kod kapsamı (`pytest --cov=app`)
**Toplam: %95** (2026-10-03: 1366 satırın 75'i çalışmadı; `llm_client.py` %94). İlk ölçüm (2026-10-02): %94, 1317 satırın 76'sı; aşağıdaki dosya tablosu ilk ölçümdendir.

| Dosya | Kapsam | Not |
|---|---:|---|
| `api/admin.py`, `api/errors.py`, `core/config.py`, `core/security.py`, `main.py` | %100 | |
| `db/conversations.py`, `db/database.py`, `db/documents.py`, `db/embeddings.py` | %100 | |
| `services/chunker.py`, `services/prompts.py`, `services/rag.py`, `services/reports.py` | %100 | |
| `services/chat.py` | %99 | |
| `services/documents.py` | %98 | |
| `api/auth.py`, `api/deps.py` | %97 | |
| `api/ask.py`, `services/auth.py` | %96 | |
| `services/indexing.py` | %95 | |
| `db/users.py`, `services/vector_search.py` | %94 | |
| `services/parser.py` | %93 | |
| `services/llm_client.py` | %92 | Nadir ağ hataları dalları |
| `api/conversations.py` | %91 | |
| `api/reports.py`, `api/search.py` | %90 | |
| `services/admin.py` | %89 | |
| `api/documents.py` | %84 | Bazı hata dalları (ör. diske yazma hatası) |
| `db/chunks.py` | %76 | Sayfalama yardımcıları |
| `services/embedder.py` | **%65** | Gerçek model (`LocalEmbedder`) testlerde bilerek kullanılmıyor; aşağıda elle denendi |

> Önceki ölçüm (stdlib `trace`, sahte FastAPI ile) `parser.py`, `main.py`, `errors.py` dosyalarını %0 göstermişti. Gerçek ölçümde %93 / %100 / %100 çıktı. Eski sayı bir ölçüm hatasıydı.

## 4. Gerçek sunucuya karşı elle (HTTP) deneme
`uvicorn app.main:app` çalışırken bir betikle **39 istek** atıldı (sentetik `@example.com` hesapları, sentetik belgeler):

| Akış | Sonuç |
|---|---|
| Kayıt, tekrar kayıt (409), zayıf parola (400), yanlış parola (401), giriş, `/auth/me` | ✅ |
| Token yok / bozuk token → 401 | ✅ |
| TXT, PDF, DOCX yükleme → `indexed`; `.exe` → 400; var olmayan belge → 404 | ✅ |
| Belge listesi, detay, parçalar, yeniden indeksleme, silme | ✅ |
| Türkçe arama (3 soru, doğru belge ilk sırada); boş sorgu ve 5000 karakterlik sorgu → 400 | ✅ |
| `/ask`, sohbet mesajı, `/admin/llm-test` anahtar yokken → **503** ve Türkçe mesaj (çökme yok) | ✅ |
| Rapor (`me`), kullanıcının `scope=all` isteği → 403, CSV (UTF-8 BOM + `attachment`) | ✅ |
| Kullanıcı → yönetici ucu 403; yönetici → kullanıcılar, tüm belgeler, sistem raporu | ✅ |

**Gözlem:** İlk belge yüklemesi **211 sn** sürdü (embedding modeli ilk kez indirildi ve yüklendi); sonraki yüklemeler ≈0,4 sn. Demodan önce uygulama bir kez çalıştırılıp model indirilmiş olmalı.

## 5. Tarayıcıda arayüz denemesi
Belgelerim (arayüzden yükleme dahil), Sohbet, Arama, Rapor, Yönetim sekmeleri denendi. **Konsolda JavaScript hatası yok.** Tek konsol satırı, anahtar yokken sohbetin aldığı 503 yanıtının tarayıcı kaydı. Yönetim sekmesi yalnızca yönetici hesabında görünüyor.

Bulunan küçük sorunlar (henüz düzeltilmedi, bkz. `docs/duzeltilen-hatalar.md` → "Açık kalanlar"):
- Raporda soru sayısı 0 iken grafik etiketi "en yüksek: 1" gösteriyor.
- Anahtar yokken son kullanıcıya teknik mesaj ("`.env` dosyasına ekleyin") gösteriliyor.

## 6. Gerçek modelle arama eşiği (`MIN_SCORE`) ölçümü
Sentetik 3 belge (kütüphane yönetmeliği TXT, laboratuvar kuralları PDF, yemekhane TXT) üzerinde, her sorunun **en iyi** benzerlik skoru:

| Belgede cevabı VAR | Skor | Belgede cevabı YOK | Skor |
|---|---:|---|---:|
| Kütüphane pazar günü açık mı? | 0,591 | Mezuniyet töreni hangi tarihte? | 0,193 |
| Bir öğrenci kaç kitap ödünç alabilir? | 0,525 | Yurt ücreti ne kadar? | 0,270 |
| Gecikme bedeli ne kadar? | 0,431 | Erasmus başvurusu nasıl yapılır? | 0,153 |
| Yangın çıkarsa nerede toplanılır? | 0,430 | Futbol takımına nasıl katılırım? | 0,056 |
| Yemekhane saat kaçta açılıyor? | 0,588 | Python'da liste nasıl sıralanır? | 0,163 |

En düşük "var" skoru 0,430; en yüksek "yok" skoru 0,270. Varsayılan **0,30** bu örnekte iki grubu doğru ayırıyor, ama "yok" grubuna yakın ("yurt ücreti" ↔ "yemek ücreti" benzerliği). Örneklem küçük (10 soru) ve sentetik olduğu için eşik **değiştirilmedi**. Kendi belgelerinle tekrarlanmalı.

**Parça uzunluğu:** Model 128 token ile eğitilmiş; uygulama `max_seq_length` değerini 256'ya çekiyor (`embedder.py`). 600 karakter Türkçe metin ≈ 149 token, yani 256'ya sığıyor. Sonları farklı iki parçanın vektörleri farklı çıktı (benzerlik 0,93): parçanın sonu da vektöre giriyor.

## 7. Gerçek ortamda bulunan test hatası
`tests/test_rapor.py` testi, önceki sahte FastAPI'de var olan `Response.content` alanını kullanıyordu; gerçek Starlette'te bu alanın adı `Response.body`. Uç nokta doğruydu, test düzeltildi. Toplama (collection) veya import hatası çıkmadı.

## 8. Test edilmeyenler (dürüst liste)
- **Gerçek Claude API** (anahtar yok). İstemci, yerel sahte HTTP sunucusuyla test edildi.
- Yük / performans testi (çok kullanıcı, büyük belge koleksiyonu).
- Mobil ekran ve ekran okuyucu ile erişilebilirlik (Hafta 14).
- Docker / dağıtım (Hafta 14).
