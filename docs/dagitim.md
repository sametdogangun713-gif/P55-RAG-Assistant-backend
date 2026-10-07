# Dağıtım: Supabase + Hugging Face + Vercel

Bu belge projeyi buluta adım adım taşır. Sıra önemli: **önce Supabase, sonra Hugging Face, sonra backend, en son frontend.**

```mermaid
flowchart LR
    U[Tarayıcı] -->|HTML/CSS/JS| FE[Vercel<br/>P55-RAG-Assistant-frontend]
    U -->|API istekleri + JWT| BE[Vercel<br/>P55-RAG-Assistant-backend<br/>FastAPI, fra1]
    U -->|dosya, imzalı adresle PUT| ST[(Supabase Storage<br/>gizli kova)]
    BE --> DB[(Supabase PostgreSQL<br/>+ pgvector)]
    BE --> ST
    BE --> HF[Hugging Face<br/>embedding]
    BE --> LLM[Groq / Claude<br/>yanıt üretimi]
```

> **Durum (2026-10-03):** Kod ve ayar dosyaları hazır, testleri yerel PostgreSQL 16 + pgvector ile ve tarayıcıda yerel
> sunucularla doğrulandı. **Gerçek Supabase, Hugging Face ve Vercel hesaplarıyla henüz denenmedi** (hesaplar ve anahtarlar
> geliştiricinin kendisinde). İlk gerçek dağıtımda bu belgedeki kontrol listesini adım adım işaretle.

## 0. Neden bu kadar değişiklik gerekti?
Yerel sürüm "bir bilgisayar, bir disk" varsayıyordu. Vercel'de bu varsayımların hepsi bozulur:

| Yerelde | Vercel'de sorun | Çözüm |
|---|---|---|
| SQLite dosyası | Disk kalıcı değil, her istek başka bir makinede olabilir | Supabase PostgreSQL |
| Vektörler Python'da karşılaştırılır | Her aramada tüm vektörleri ağdan çekmek yavaş | pgvector: benzerlik SQL'de (`<=>`) |
| Embedding modeli bilgisayarda (torch, ~1,4 GB bellek) | Paket sınırı 500 MB, bellek 2 GB, her soğuk başlangıçta model yüklenir | Aynı model Hugging Face sunucusunda |
| 500 MB dosya sunucuya gönderilir | Bir istek en fazla **4,5 MB** | Tarayıcı dosyayı Supabase Storage'a doğrudan yükler |
| Arayüz ve API aynı adreste | İki ayrı Vercel projesi, iki adres | `config.js` (API adresi) + CORS (`ALLOWED_ORIGINS`) |
| E-posta yanıttan sonra gönderilir | İşlev yanıttan sonra durdurulabilir | `SEND_EMAIL_INLINE=1` (Vercel'de otomatik) |

Ücretsiz plan sınırları (2026-10, resmi sayfalardan): **Vercel Hobby** — istek gövdesi 4,5 MB, işlev süresi en fazla 300 sn,
bellek 2 GB, Python paketi 500 MB. **Supabase Free** — veritabanı 500 MB, dosya deposu 1 GB, dosya başına 50 MB,
**1 hafta kullanılmayan proje durdurulur**, en fazla 2 aktif proje.

## 1. Supabase (veritabanı + dosya deposu)
1. https://supabase.com → GitHub hesabınla giriş → **New project**.
   - Name: `p55-rag` · **Region: Central EU (Frankfurt)** (KVKK: veri Avrupa'da kalsın; Vercel bölgemiz de Frankfurt)
   - **Database password:** güçlü bir parola üret ve parola yöneticine kaydet. Yalnızca harf ve rakam kullanırsan adrese yazarken sorun çıkmaz. Bu parolayı kimseyle paylaşma, sohbete yapıştırma.
2. Proje açılınca üstteki **Connect** düğmesi → **Transaction pooler** → adresi kopyala:
   `postgresql://postgres.<proje-kodu>:[YOUR-PASSWORD]@aws-…pooler.supabase.com:6543/postgres`
   `[YOUR-PASSWORD]` yerine parolanı yaz. (Port **6543** = havuzlayıcı; Vercel gibi çok sayıda kısa bağlantı açan ortamlar için doğru seçim.)
3. **Project Settings → API Keys:** "Secret key" (`sb_secret_…`) oluştur/kopyala. (Eski projelerde "Legacy API Keys → service_role" de çalışır.)
   **Project Settings → Data API:** Project URL'yi kopyala (`https://<proje-kodu>.supabase.co`).
4. Tabloları ve dosya kovasını kur. `P55-RAG-Assistant-backend\.env` dosyasında **geçici olarak** şu satırları değiştir:
   ```
   DATABASE_URL=postgresql://postgres.<proje-kodu>:<parola>@aws-…pooler.supabase.com:6543/postgres
   STORAGE_BACKEND=supabase
   SUPABASE_URL=https://<proje-kodu>.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=sb_secret_…
   MAX_UPLOAD_MB=50
   ```
   Sonra:
   ```bat
   venv\Scripts\activate
   python -m scripts.supabase_kurulum
   python -m scripts.create_admin
   ```
   Beklenen çıktı: `Migration: 001_init, 002_name_and_email_verification` ve `Dosya kovası 'belgeler': oluşturuldu (gizli)`. Supabase panelinde
   **Table Editor**'da (şema: `public`) 8 tablo (hepsinde "RLS enabled"; `email_codes` dahil, `schema_migrations` ile 9), **Database → Schema Visualizer**'da ilişki diyagramı, **Storage**'da gizli `belgeler` kovası görünmeli.
   `create_admin` bulut veritabanında yönetici hesabını açar.
5. Yerel çalışmaya dönmek için `.env`'deki bu satırları eski hâline getir (`DATABASE_URL=sqlite:///./data/asistan.db`,
   `STORAGE_BACKEND=local`, `MAX_UPLOAD_MB=500`). Bulut değerleri artık yalnızca Vercel'de duracak.

> `create extension vector` hatası alırsan: Supabase → **Database → Extensions → vector → Enable**, sonra 4. adımı tekrarla.

## 2a. Google Gemini (embedding, önerilen)
Hugging Face'in ücretsiz aylık kredisi büyük bir PDF'te bitti (2026-10-07, hata `402`). Gemini'nin ücretsiz katmanı kart istemez.
1. https://aistudio.google.com → Google hesabıyla giriş → **Get API key → Create API key** → `AIza…` anahtarını kopyala.
2. Yerelde: `.env` → `GEMINI_API_KEY=AIza…` (anahtarı sohbete/ekrana yazma), sonra dene:
   ```bat
   python -m scripts.gemini_dene
   ```
   Beklenen: `boyut 768`; belgede olan sorular ~0,7+, olmayanlar ~0,5–0,6 (ölçüm: `docs/istem-deneyleri.md`).
3. Vercel (backend) → ortam değişkenleri: `EMBEDDING_BACKEND=gemini`, `GEMINI_API_KEY=AIza…` (gizli) → **Redeploy**.
4. Model değişince eski vektörler kullanılmaz: Belgelerim'de her belge için **Yeniden indeksle**.
5. Sınırlar: ücretsiz katmanda dakika ve gün başına sınır var. Sınıra takılınca kod Google'ın söylediği kadar bekler;
   yine dolarsa indeksleme o ana kadarkini kaydeder ve "Devam et" ile kalan yerden sürer. Ücretsiz katmanda Google
   gönderilen metni ürün geliştirmede kullanabilir: **gerçek kişisel veri içeren belge yükleme** (KVKK).

## 2. Hugging Face (embedding, eski)
1. https://huggingface.co → hesap aç → **Settings → Access Tokens → Create new token** → "Fine-grained" →
   **"Make calls to Inference Providers"** kutusunu işaretle → oluştur, `hf_…` anahtarını kopyala.
2. Yerelde: `.env` → `HF_TOKEN=hf_…` ve `EMBEDDING_BACKEND=hf`.
   Bulutta yereldeki MiniLM yerine **bge-m3** kullanılır: Hugging Face MiniLM'i 128 token'da kesiyordu ve Türkçe 600 karakterlik
   parçanın ikinci yarısı aranamıyordu. bge-m3 8192 token alır, Türkçede doğru parçayı daha iyi bulur; eşiği `0.40` (ölçüm: `docs/istem-deneyleri.md`).
   Bedeli hız: ~10 parça/sn. Model değişince eski belgeler aramada görünmez → Belgelerim'de **Yeniden indeksle**.
3. Ücretsiz hesabın aylık küçük bir kullanım kredisi var; kullanımı **Settings → Billing**'den izle.

## 3. Vercel – backend
1. https://vercel.com → GitHub ile giriş → **Add New → Project** → `P55-RAG-Assistant-backend` deposunu seç → **Import**.
   Framework otomatik **FastAPI** olarak tanınır (`app/main.py` içindeki `app`). Root Directory: `./`.
2. **Environment Variables** (Deploy'a basmadan önce, hepsi "Production"):

   | Değişken | Değer | Gizli mi? |
   |---|---|---|
   | `APP_ENV` | `production` | |
   | `SECRET_KEY` | **yeni** 64 karakter: `python -c "import secrets; print(secrets.token_hex(32))"` (yereldekinden farklı olsun) | **evet** |
   | `DATABASE_URL` | 1.2'deki Transaction pooler adresi (parolalı) | **evet** |
   | `ALLOWED_ORIGINS` | frontend adresin, ör. `https://p55-rag-assistant-frontend.vercel.app` (4. adımdan sonra kesinleşir) | |
   | `EMBEDDING_BACKEND` | `gemini` (eskisi `hf`) | |
   | `GEMINI_API_KEY` | `AIza…` | **evet** |
   | `STORAGE_BACKEND` | `supabase` | |
   | `SUPABASE_URL` | `https://<proje-kodu>.supabase.co` | |
   | `SUPABASE_SERVICE_ROLE_KEY` | `sb_secret_…` | **evet** |
   | `SUPABASE_BUCKET` | `belgeler` | |
   | `MAX_UPLOAD_MB` | `50` | |
   | `MAX_CHUNKS_PER_DOCUMENT` | `20000` (indeksleme 60 sn'lik isteklere bölünür, 300 sn sınırı sorun olmaz) | |
   | `LLM_PROVIDER` | `groq` | |
   | `GROQ_API_KEY` | `gsk_…` | **evet** |
   | `GROQ_MODEL` | `openai/gpt-oss-120b` | |
   | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | **gerekli**: `smtp.gmail.com`, `587`, Gmail adresin, Gmail **uygulama şifresi** (16 harf, boşluksuz), Gmail adresin. Boşsa üretimde kayıt (doğrulama kodu) ve "Şifremi unuttum" 503 döner | `SMTP_PASSWORD` **evet** |

   Yazılmayanlar varsayılanı kullanır (`app/core/config.py`, liste README'de). `UPLOAD_DIR` yazma: Vercel'de otomatik `/tmp/uploads`.
3. **Deploy**. Bitince adres: `https://p55-rag-assistant-backend.vercel.app` (proje adına göre değişir). Dene:
   - `…/health` → `{"status":"ok","database":"postgres"}` (`"sqlite"` ise `DATABASE_URL` Vercel'de tanımlı değil)
   - `…/docs` → Swagger sayfası
   - `vercel.json`: bölge **fra1** (Frankfurt, Supabase'e yakın), en uzun istek 300 sn.
4. Ortam değişkenini sonradan değiştirirsen **Deployments → … → Redeploy** gerekir (değişkenler yalnızca yeni dağıtımda okunur).

## 4. Vercel – frontend
1. `P55-RAG-Assistant-frontend\public\config.js` dosyasında bulut adresini 3. adımda aldığın backend adresiyle değiştir:
   ```js
   : "https://p55-rag-assistant-backend.vercel.app",
   ```
   Commit + push. (Bu dosyada gizli bilgi yoktur; olmamalıdır.)
2. Vercel → **Add New → Project** → `P55-RAG-Assistant-frontend` → Framework Preset: **Other** → Deploy.
   `vercel.json` sitenin `public/` klasöründen sunulmasını ve güvenlik başlıklarını ayarlar; derleme adımı yoktur.
3. Çıkan adresi (ör. `https://p55-rag-assistant-frontend.vercel.app`) backend'in `ALLOWED_ORIGINS` değişkenine yaz → backend'i **Redeploy**.

## 5. Uçtan uca kontrol listesi
- [ ] `https://<backend>/health` → ok
- [ ] Frontend açılıyor, tarayıcı konsolunda (F12) kırmızı hata yok
- [ ] Kayıt → giriş çalışıyor (CORS hatası yok)
- [ ] 1–2 MB'lık bir PDF yükle → "Belge hazır". Supabase **Storage → belgeler** içinde `<kullanıcı-no>/<rastgele>.pdf` görünüyor
- [ ] Arama sekmesinde belgedeki bir konuyu ara → doğru parça, makul skor
- [ ] Sohbet: belgede olan bir soru → `[1]` kaynaklı yanıt; belgede olmayan bir soru → "bilgi bulamadım"
- [ ] Belgeyi sil → Storage'dan da silindi
- [ ] Rapor sekmesi sayıları gösteriyor; yönetici hesabıyla Yönetim sekmesi açılıyor
- [ ] 50 MB'tan büyük dosya → gönderilmeden "Dosya çok büyük" uyarısı
- [ ] GitHub'da iki depoda da `.env` yok; `git grep -n "sb_secret_\|gsk_\|hf_"` boş

## 6. Sık karşılaşılan sorunlar
| Belirti | Nedeni / çözüm |
|---|---|
| Tarayıcı konsolunda "blocked by CORS policy" | Frontend adresi backend'in `ALLOWED_ORIGINS`'inde yok ya da sonunda `/` var. Düzelt → backend'i Redeploy |
| Arayüz "Sunucuya ulaşılamadı" | `config.js`'teki backend adresi yanlış ya da backend çöktü (Vercel → backend → **Logs**) |
| Backend açılışta `SECRET_KEY zayıf` | `APP_ENV=production` iken `SECRET_KEY` boş/kısa. 64 karakterlik değer gir |
| `password authentication failed` | `DATABASE_URL`'deki parola yanlış ya da `[YOUR-PASSWORD]` değiştirilmemiş |
| `prepared statement … already exists` | Doğrudan bağlantı (5432) yerine pooler kullanılıyorsa sorun olmaz; kod `prepare_threshold=None` ile bunu önler. Hâlâ görülürse "Session pooler" adresini dene |
| Yükleme "Dosya deposu isteği reddedildi (403)" | `SUPABASE_SERVICE_ROLE_KEY` yanlış (publishable/anon anahtarı girilmiş olabilir) |
| "Hugging Face anahtarı geçersiz" | `HF_TOKEN` yanlış ya da "Inference Providers" izni verilmemiş |
| "Hugging Face'in aylık ücretsiz kullanım hakkı doldu (402)" | Ücretsiz kredi bitti. `EMBEDDING_BACKEND=gemini` + `GEMINI_API_KEY` (2a. adım), sonra **Yeniden indeksle** |
| "Gemini'nin dakikalık/günlük kullanım sınırı (429)" | Ücretsiz katman sınırı. Kaydedilen parçalar korunur; bir dakika (ya da ertesi gün) sonra **Devam et** |
| "Gemini API anahtarı geçersiz" | `GEMINI_API_KEY` yanlış kopyalanmış; AI Studio'da yeni anahtar üret |
| Büyük belgede `504 FUNCTION_INVOCATION_TIMEOUT` | Yükleme isteği (indirme + ayrıştırma + parçalama + ilk 60 sn indeksleme) 300 sn'yi aştı. `INDEX_BUDGET_SECONDS`'ı düşür (ör. 30); belge "indeksleniyor" kaldıysa Belgelerim → **Devam et** |
| Uygulama açılmıyor, Supabase "Paused" | Ücretsiz proje 1 hafta kullanılmayınca durur: Supabase paneli → **Restore project** (demodan önce kontrol et!) |

## 7. Güvenlik notları
- Gizli değerler **yalnızca** Vercel ortam değişkenlerinde ve yerel `.env`'de. Hiçbirini koda, `vercel.json`'a, `config.js`'e,
  ekran görüntüsüne, sohbete koyma. Sızarsa: ilgili panelden **iptal et, yenisini üret**, Vercel'de güncelle, Redeploy.
- `SUPABASE_SERVICE_ROLE_KEY` veritabanına ve depoya **tam erişim** verir; tarayıcıya asla gönderilmez. Tarayıcı dosyayı
  yalnızca backend'in ürettiği tek kullanımlık imzalı adrese yükler; oturum token'ı Supabase'e gitmez.
- Supabase tablolarında **Row Level Security** açık ve politika yok: Supabase'in otomatik REST API'si bu tablolara erişemez.
  Uygulamamız tablo sahibi rolüyle bağlandığı için etkilenmez.
- Depo yolu `kullanıcı-no/rastgele-ad.uzantı` biçimindedir; backend bir kullanıcının başkasının klasöründeki dosyayı işletmesine izin vermez.

## 8. Yerelde PostgreSQL ile deneme (isteğe bağlı)
Testlerin PostgreSQL'e karşı da geçtiğini görmek için bir PostgreSQL (pgvector'lü) sunucusu gerekir. Örnek (Docker varsa):
```bat
docker run -d --name asistan-pg -e POSTGRES_PASSWORD=yerel -p 5432:5432 pgvector/pgvector:pg16
set TEST_PG_URL=postgresql://postgres:yerel@localhost:5432/postgres
pytest
```
Bu projede 2026-10-03'te Docker yerine `pgserver` Python paketinin içindeki PostgreSQL 16 + pgvector kullanıldı (yalnızca test için, geçici klasörde).
