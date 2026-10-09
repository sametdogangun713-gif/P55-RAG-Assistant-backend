# Adım 12 — Dokümantasyon, arayüz iyileştirme ve dağıtım (Supabase + Vercel)

> Ders planındaki karşılığı: **Hafta 14** — "Dokümantasyon, kullanılabilirlik ve dağıtım hazırlığı".

## Ne yapıldı

### Amaç
Projeyi başka birinin kurup çalıştırabileceği, belgelenmiş ve buluta taşınabilir hâle getirmek; arayüzü kullanılabilir ve erişilebilir yapmak.

### Bu adımda eklenen / değişen
| Konu | Dosyalar | Ne işe yarıyor |
|---|---|---|
| Büyük dosya | `services/documents.py` (`_save_stream`), `main.py` (413 ön kontrolü), `GET /documents/limits` | Dosya belleğe alınmadan 1 MB bloklarla diske yazılır; sınırı aşan istek gövdesi okunmadan reddedilir; arayüz sınırı sunucudan okur |
| Arayüz | frontend `index.html`, `style.css`, `app.js` | Ana sayfa (proje tanıtımı), sade tema, açık/koyu (sistem ayarı ya da düğme), masaüstü + mobil düzen, erişilebilir sekmeler, "hareketi azalt" desteği, gerçek yükleme yüzdesi |
| Şifremi unuttum | `migrations/004_password_reset.sql` (005 ile `email_codes` oldu), `db/email_codes.py`, `services/email_codes.py`, `services/password_reset.py`, `services/mailer.py`, `api/auth.py` | 6 haneli tek kullanımlık kod, e-postayla (SMTP); kodun kendisi değil HMAC özeti saklanır |
| Kayıt + e-posta doğrulama | `migrations/005_name_and_email_verification.sql` (PG `002`), `services/email_verification.py`, `services/auth.py` (`sign_up`), `api/auth.py` | Ayrı kayıt ekranı, ad soyad, 6 haneli doğrulama kodu; doğrulanmamış hesap giriş yapamaz |
| **İki depo** | `P55-RAG-Assistant-backend`, `P55-RAG-Assistant-frontend` | Arayüz ayrı bir statik site; backend yalnızca API. Arayüz backend adresini `public/config/config.js`'ten okur |
| **CORS** | `main.py`, `ALLOWED_ORIGINS` | Tarayıcı yalnızca izinli arayüz adresinden backend'e istek atabilir |
| **PostgreSQL** | `db/database.py` (`PgConnection`), `migrations/postgres/001_init.sql`, depo modüllerinde taşınabilir SQL | Aynı kod yerelde SQLite, bulutta Supabase PostgreSQL ile çalışır |
| **pgvector** | `db/embeddings.py` (`nearest`), `services/vector_search.py` | Bulutta benzerlik SQL'de hesaplanır (`<=>`) |
| **Bulut embedding** | `services/embedder.py` (`HFEmbedder`, 2026-10-07'den beri `GeminiEmbedder`), `scripts/gemini_dene.py` | Vercel'e torch/model sığmaz; HF'nin ücretsiz kredisi bitince (402) Gemini'ye geçildi |
| **Dosya deposu** | `services/storage.py`, `POST /documents/upload-url`, `POST /documents/complete`, frontend `docs.js` | Tarayıcı dosyayı Supabase Storage'a doğrudan yükler (Vercel isteği ≤ 4,5 MB) |
| Vercel | `vercel.json` (iki depoda), `.python-version`, `.vercelignore`, `requirements*.txt` ayrımı | Bölge Frankfurt, istek ≤ 300 sn; sunucu paketi torch'suz (~120 MB) |
| Kurulum | `scripts/supabase_kurulum.py`, `scripts/env_olustur.py` | Tek komutla tablolar + kova; `.env` + `SECRET_KEY` otomatik |
| Belgeler | `README.md` (iki depo), `docs/teknik-dokumantasyon/teknik-dokumantasyon.md`, `docs/dagitim/dagitim.md`, `docs/yol-haritasi/yol-haritasi.md`, `CHANGELOG.md` | Kurulum, tüm API uçları, bulut adımları, ortam değişkenleri tablosu |
| Testler | `tests/test_buyuk_yukleme.py`, `test_kurulum.py`, `test_sifre_sifirlama.py`, `test_bulut.py`, frontend `tests/test_arayuz.py` | Bulut kodu sahte Supabase/HF sunucularıyla; tüm testler PostgreSQL'e karşı da |

### Çalıştırma ve demo
Yerel: backend `uvicorn app.main:app` (API, http://127.0.0.1:8000/docs) + frontend `python -m http.server 5500 --directory public` (http://localhost:5500).
Bulut: [`../dagitim.md`](../../dagitim/dagitim.md).
Testler: `pytest` (SQLite) · `set TEST_PG_URL=… && pytest` (PostgreSQL) · frontend: `python -m unittest discover -s tests`.

### Kendi yapacakların
1. **Temiz ortamda kurulum:** README'yi hiç bilmeyen biri gibi takip et (başka bir klasöre `git clone`, README'deki kurulum komutları). Takıldığın her yeri README'ye ekle.
2. **Buluta kendin dağıt:** [`../dagitim.md`](../../dagitim/dagitim.md) 1–4. adımlar ve §5 kontrol listesi; her maddenin ekran görüntüsü. Anahtarları kendin gir.
3. **Kullanılabilirlik:** arayüzde seni rahatsız eden bir şeyi bul ve düzelt (ör. bir hata mesajını daha anlaşılır yap, bir düğmeye klavye kısayolu ekle). Ne değiştirdiğini ve neden aşağıdaki "Deneyim" bölümüne yaz.
4. **Erişilebilirlik:** klavyeyle (yalnızca Tab/Enter) giriş → yükleme → arama yapmayı dene; takıldığın yeri not et.
5. `ai-kullanim-gunlugu.md` → Adım 12 "kendi" alanları.

### Kontrol listesi
- [x] Sunucu paketleri (`requirements.txt`) temiz bir sanal ortama kuruldu, uygulama açıldı (2026-10-03)
- [ ] README'nin tamamı başka bir bilgisayarda/temiz klasörde baştan sona denenmedi (görev 1)
- [x] Gizli anahtar depoda yok (`.gitignore`, `.vercelignore`, arayüz testinde anahtar taraması)
- [x] Ortam değişkenleri tablosu (README + `dagitim.md`)
- [ ] Gerçek bulut dağıtımı (Supabase + Vercel) — hesaplar sende
- [ ] Temiz ortamda senin kurulum denemen

## Kod açıklaması

### Ortam değişkenleri neden?
Aynı kod üç yerde çalışıyor: senin bilgisayarın, testler, bulut. Farklı olan yalnızca **ayarlar**: hangi veritabanı
(`DATABASE_URL`), embedding nerede (`EMBEDDING_BACKEND`), dosya nerede (`STORAGE_BACKEND`), hangi anahtar. Ayarları kodda
tutsaydım her ortam için kodu değiştirmem ve anahtarları depoya koymam gerekirdi. `.env` git'e girmez; Vercel'de aynı
değerler panelden girilir.

### Bir kod, iki veritabanı
```python
def get_connection(db_path=None):
    if db_path is None and config.is_postgres():
        raw = psycopg.connect(config.DATABASE_URL, prepare_threshold=None, ...)
        return PgConnection(raw)          # sqlite3.Connection gibi davranır
    conn = sqlite3.connect(path, ...)
```
Depo modülleri iki veritabanında da geçerli SQL yazar (`RETURNING id`, `ON CONFLICT`, `substr`). Farkları `PgConnection`
kapatır: `?` → `%s`, satırlar hem `row[0]` hem `row["email"]` ile okunur, `with conn:` hata yoksa commit eder.
`prepare_threshold=None`: Supabase'in havuzlayıcısı (port 6543) bir isteğin bağlantısını sonraki istekte başkasına verir;
"hazır sorgu" bir bağlantıya bağlı olduğu için kapatılmazsa rastgele hatalar çıkar.

### pgvector
```sql
SELECT …, 1 - (e.vector <=> ?::vector) AS score … ORDER BY e.vector <=> ?::vector LIMIT ?
```
`<=>` kosinüs **uzaklığıdır** (0 = aynı yön). `1 - uzaklık` = kosinüs benzerliği; yerelde numpy ile hesapladığımız sayının
aynısı (test: `test_pgvector_ve_numpy_ayni_sonucu_verir`). Fark: SQLite'ta tüm vektörleri Python'a çekip çarpıyoruz,
PostgreSQL'de hesap veritabanında yapılıyor ve yalnızca en iyi `k` satır ağdan geliyor.

### İmzalı yükleme adresi (neden dosya backend'den geçmiyor?)
Vercel bir istekte en fazla 4,5 MB kabul eder. Backend dosyayı almak yerine Supabase'ten **tek kullanımlık, yalnızca o
yola yazma izni veren** bir adres alır ve tarayıcıya verir. Tarayıcı dosyayı oraya `PUT` eder, sonra backend'e "yükledim"
der. Backend dosyayı depodan okur, **gerçek baytlarla** tür ve boyut kontrolünü yeniden yapar (tarayıcının söylediği boyuta
güvenmez), sonra ayrıştırır. Yol `kullanıcı-no/rastgele.pdf` biçimindedir; backend başka bir kullanıcının klasöründeki
yolu reddeder. Supabase'in gizli anahtarı yalnızca backend'dedir; oturum token'ımız Supabase'e gönderilmez.

### CORS
Tarayıcı, sayfanın geldiği adresten (`p55-rag-assistant-frontend.vercel.app`) başka bir adrese (`p55-rag-assistant-backend.vercel.app`)
JavaScript ile istek atmadan önce sunucuya sorar (OPTIONS, "preflight"). Backend yalnızca `ALLOWED_ORIGINS`'teki adreslere
"evet" der. Bu, başka bir sitenin kullanıcının tarayıcısı üzerinden API'mizi kullanmasını zorlaştırır.

### Sunucusuz (serverless) ortamın getirdikleri
- Disk geçici → veritabanı ve dosyalar dışarıda (Supabase).
- Her istek ayrı bir makinede olabilir → bellekteki şeyler (başarısız giriş sayacı) örnekler arasında paylaşılmaz (bilinen sınır).
- Yanıttan sonra işlev durdurulabilir → e-posta yanıttan önce gönderilir (`SEND_EMAIL_INLINE`).
- Aynı anda iki örnek açılabilir → migration'lar `pg_advisory_xact_lock` kilidiyle tek seferde uygulanır.

### Sözlü sınav soruları ve cevap iskeleti
**1) README'de hangi bölümler olmalı?** Ne yaptığı, hızlı başlangıç, adım adım kurulum (komutlarla), gereken anahtarlar ve nereye yazılacağı, testlerin nasıl çalıştırılacağı, ayarlar tablosu, sık sorunlar, klasör yapısı, güvenlik, bilinen sınırlar. Benim README'm iki depoyu ve iki çalışma biçimini (yerel / bulut) de anlatıyor.
**2) Ortam değişkenlerini neden kullanıyorsun?** Gizli değerler koda/depoya girmesin; aynı kod farklı ortamlarda (yerel, test, bulut) farklı ayarlarla çalışsın. Örnek: `DATABASE_URL` yerelde SQLite dosyası, Vercel'de Supabase adresi — kod aynı.
**3) Projeni başka biri nasıl çalıştırır?** Python 3.10+ → iki depoyu indir → backend: sanal ortam, `pip install -r requirements-local.txt`, `python -m scripts.env_olustur` (`.env` + `SECRET_KEY`), `uvicorn app.main:app` → frontend: `python -m http.server 5500 --directory public`. Bulut için `dagitim.md`.
**4) Hangi kullanılabilirlik iyileştirmesini yaptın?** Gerçek yükleme yüzdesi; dosya seçilene kadar pasif "Yükle" düğmesi; sınırı aşan dosyayı göndermeden uyarma; şifremi unuttum; koyu/açık tema; mobil düzen; klavye ve ekran okuyucu için ARIA; "hareketi azalt". *(Kendi yaptığın iyileştirmeyi buraya ekle.)*
**5) Dağıtımda karşılaşabileceğin sorun?** Vercel'in 4,5 MB istek ve 300 sn süre sınırı (çözüm: doğrudan depoya yükleme, parça sınırı); diskin kalıcı olmaması (Supabase); CORS hatası (`ALLOWED_ORIGINS`); havuzlayıcıda "prepared statement" hatası (`prepare_threshold=None`); Supabase ücretsiz projenin 1 hafta sonra durması; embedding modelinin pakete sığmaması (Hugging Face).

### Deneyim (kendi gözlemini yaz)
- Temiz ortamda kurulumda takıldığım yer:
- Kendi yaptığım kullanılabilirlik iyileştirmesi ve nedeni:
- Buluta dağıtırken karşılaştığım sorun ve çözümü:

### Dürüst not
Bulut kodu **gerçek Supabase / Hugging Face / Vercel hesaplarıyla henüz denenmedi** (hesaplar geliştiricide). Doğrulananlar
(2026-10-03): tüm testler SQLite'ta ve yerel PostgreSQL 16 + pgvector'de geçti; Supabase Storage ve Hugging Face istek
biçimleri sahte sunucularla test edildi (adres, başlık, gövde); tarayıcıda frontend (5500) + backend (8000, PostgreSQL)
ayrı adreslerde kayıt → giriş → yükleme → arama → rapor çalıştı, konsol temiz; sunucu paketi (torch'suz) ≈ 120 MB.
Postgres testleri gerçek bir hata buldu: ikili/bozuk bir `.txt` yüklenince NUL karakteri yüzünden 500 hatası (düzeltildi,
[`../duzeltilen-hatalar.md`](../../duzeltilen-hatalar/duzeltilen-hatalar.md)).
