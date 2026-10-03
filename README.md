# P55 – Belge Tabanlı Soru-Cevap Asistanı (RAG) · Backend

Yüklenen belgelere dayanarak **kaynaklı** yanıt veren bir soru-cevap asistanının **sunucu (API) tarafı**.
Ders: Bilgisayar Uygulamaları I (Bingöl Üniversitesi, Bilgisayar Programcılığı) · Öğr. Gör. Mustafa NARİN
Geliştirici: Samet DOĞANGÜN

Proje iki depodan oluşur:

| Depo | İçerik | Bulutta |
|---|---|---|
| **P55-RAG-Assistant-backend** (bu depo) | FastAPI uygulaması, veritabanı, testler, **tüm belgeler** (`docs/`) | Vercel (Python) + Supabase (PostgreSQL, Storage) |
| [P55-RAG-Assistant-frontend](https://github.com/sametdogangun713-gif/P55-RAG-Assistant-frontend) | Web arayüzü (HTML/CSS/JS, derleme yok) | Vercel (statik site) |

## Ne yapar?
Uzun belgelerde aranan bilgiyi bulmak zaman alır. Bu uygulama belgeleri (TXT, PDF, DOCX) parçalara böler, her parçayı
anlamını temsil eden bir vektöre çevirir (embedding), soruya en yakın parçaları bulur ve yanıtı **yalnızca bu parçalara
dayanarak**, `[1]`, `[2]` gibi kaynak numaralarıyla üretir (RAG). Belgede bilgi yoksa uydurmak yerine "bilgi bulamadım" der.

| Özellik | Açıklama |
|---|---|
| Hesaplar | Kayıt / giriş (scrypt parola özeti, JWT oturum), kullanıcı ve yönetici rolleri, e-postayla şifre sıfırlama |
| Belgeler | TXT, PDF, DOCX yükleme, ayrıştırma, parçalama; her kullanıcı yalnızca kendi belgelerini görür |
| Arama | Türkçe anlamsal arama (çok dilli model; yerelde bilgisayarında, bulutta Hugging Face'te) |
| Sohbet | Kaynaklı yanıt, sohbet geçmişi, uzun sohbetlerde özetleme (Groq ya da Claude) |
| Rapor | Kullanım ve kaynak raporu, CSV dışa aktarma |
| Yönetim | Kullanıcılar, tüm belgeler, sistem raporu (yalnızca yönetici) |

## İki çalışma biçimi
| | Yerel (kendi bilgisayarın) | Bulut |
|---|---|---|
| Veritabanı | SQLite dosyası (`data/p55.db`) | Supabase PostgreSQL + pgvector |
| Dosyalar | Sunucu diski (`uploads/`), en fazla 500 MB | Supabase Storage (gizli kova), en fazla 50 MB |
| Embedding | `sentence-transformers` (yerel, ücretsiz) | Aynı model, Hugging Face Inference API |
| Kurulum | `baslat.bat` | [`docs/dagitim.md`](docs/dagitim.md) |

Hangisinin kullanılacağına kod değil **ayarlar** (`.env` / Vercel ortam değişkenleri) karar verir. Kod aynıdır.

## Hızlı başlangıç (Windows, yerel)
1. **Python 3.10 veya üstünü** kurun: https://www.python.org/downloads/ ("Add python.exe to PATH" kutusunu işaretleyin).
2. İki depoyu da indirin (yan yana iki klasör):
   ```bat
   git clone https://github.com/sametdogangun713-gif/P55-RAG-Assistant-backend.git
   git clone https://github.com/sametdogangun713-gif/P55-RAG-Assistant-frontend.git
   ```
3. `P55-RAG-Assistant-backend` klasöründeki **`baslat.bat`**'a çift tıklayın: sanal ortam ve paketler kurulur (ilk sefer birkaç dakika, internet gerekir), `.env` oluşturulur, API **http://127.0.0.1:8000** adresinde açılır.
4. `P55-RAG-Assistant-frontend` klasöründeki **`baslat.bat`**'a çift tıklayın: arayüz **http://localhost:5500** adresinde açılır.
5. **Kayıt ol** ile hesap açın (deneme için `ad@example.com` gibi uydurma bir e-posta yeterli), belge yükleyin, soru sorun.

Testler: **`testleri_calistir.bat`**.

> **İlk belge yüklemesi yavaştır:** embedding modeli (~470 MB) ilk seferde indirilir. Hızlı deneme için `.env` içinde
> `EMBEDDING_BACKEND=hash` yapabilirsiniz (indirme yok, ama arama anlamsal değil).

## Adım adım kurulum (komutlarla)
```bat
cd P55-RAG-Assistant-backend
py -3 -m venv venv
venv\Scripts\activate
pip install -r requirements-local.txt
python -m scripts.env_olustur
uvicorn app.main:app
```
- `requirements.txt` = sunucunun çalışması için gerekenler (Vercel yalnızca bunu kurar). `requirements-local.txt` = bunlar + yerel embedding modeli. `requirements-dev.txt` = bunlar + test araçları.
- `python -m scripts.env_olustur`, `.env.example`'ı `.env` olarak kopyalar ve rastgele bir `SECRET_KEY` üretir.
- API belgeleri (Swagger): http://127.0.0.1:8000/docs · Sağlık kontrolü: http://127.0.0.1:8000/health
- macOS / Linux: `python3 -m venv venv` ve `source venv/bin/activate`.

**Yönetici hesabı** (kayıt formuyla yönetici olunamaz; güvenlik gereği):
```bat
python -m scripts.create_admin
```

## Sohbet için API anahtarı
Kayıt, yükleme, arama, rapor ve yönetim **anahtarsız** çalışır. Sohbet yanıt üretmek için bir dil modeli API'si kullanır:
- **Groq (ücretsiz katman):** https://console.groq.com/keys → `.env`'de `LLM_PROVIDER=groq`, `GROQ_API_KEY=` satırına anahtar.
- **Claude (ücretli):** `LLM_PROVIDER=claude`, `ANTHROPIC_API_KEY=` satırına anahtar.

Anahtar yoksa sohbet çökmez, "GROQ_API_KEY ayarlı değil" mesajı gösterir.
**Anahtarı asla depoya, ekran görüntüsüne veya mesaja koymayın.** `.env` dosyası `.gitignore`'dadır, GitHub'a gitmez.

## Bulut (Supabase + Vercel)
Adım adım: **[`docs/dagitim.md`](docs/dagitim.md)**. Özet:
1. Supabase'te proje (Frankfurt) → `python -m scripts.supabase_kurulum` (tablolar + gizli dosya kovası).
2. Vercel'de bu depo → ortam değişkenleri (`DATABASE_URL`, `SECRET_KEY`, `HF_TOKEN`, `SUPABASE_*`, `GROQ_API_KEY`, `ALLOWED_ORIGINS` …).
3. Vercel'de frontend deposu → `public/config.js` içine backend adresi.

## Testler
```bat
pip install -r requirements-dev.txt
pytest
pytest --cov=app
```
Testler internet ve API anahtarı gerektirmez: embedding için hızlı yedek model, dil modeli / Hugging Face / Supabase Storage
için yerel sahte sunucular kullanılır. Varsayılan veritabanı bellekteki SQLite'tır. **Aynı testler PostgreSQL'e karşı da koşar:**
```bat
set P55_TEST_PG_URL=postgresql://kullanici@localhost:5432/veritabani
pytest
```
Son ölçüm ve ayrıntı: [`docs/test-raporu.md`](docs/test-raporu.md).

## Ayarlar (`.env`)
| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `SECRET_KEY` | (üretilir) | Oturum token'larını imzalar. En az 32 karakter. `APP_ENV=production` iken zayıfsa uygulama başlamaz |
| `APP_ENV` | `development` | `production` = sıkı güvenlik kontrolleri (bulutta mutlaka) |
| `DATABASE_URL` | `sqlite:///./data/p55.db` | SQLite dosyası **ya da** `postgresql://…` (Supabase, Transaction pooler, port 6543) |
| `ALLOWED_ORIGINS` | `http://localhost:5500,http://127.0.0.1:5500` | Backend'e istek atabilecek arayüz adresleri (CORS), virgülle |
| `UPLOAD_DIR` | `./uploads` (Vercel'de `/tmp/uploads`) | Yüklenen/geçici dosyaların klasörü |
| `MAX_UPLOAD_MB` | `500` | En büyük dosya. Bulutta **50** (Supabase ücretsiz plan sınırı) |
| `MAX_CHUNKS_PER_DOCUMENT` | `20000` | Belge başına en fazla parça. Bulutta **2000** önerilir (bge-m3 ~10 parça/sn, istek en fazla 300 sn) |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `600` / `100` | Parça uzunluğu / örtüşme (karakter) |
| `EMBEDDING_BACKEND` | `local` | `local` = bilgisayarında model, `hf` = Hugging Face'te bge-m3 (bulut), `hash` = hızlı yedek |
| `EMBEDDING_MODEL` | `local`: `paraphrase-multilingual-MiniLM-L12-v2`, `hf`: `BAAI/bge-m3` | Çok dilli model |
| `HF_TOKEN` | boş | Hugging Face anahtarı (`EMBEDDING_BACKEND=hf` iken). Yalnızca `.env` / Vercel paneli |
| `STORAGE_BACKEND` | `local` | `local` = sunucu diski, `supabase` = Supabase Storage (bulutta zorunlu) |
| `SUPABASE_URL` | boş | `https://<proje>.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | boş | Supabase gizli anahtarı (her şeye erişir!). Yalnızca backend'de |
| `SUPABASE_BUCKET` | `belgeler` | Dosya kovasının adı |
| `MIN_SCORE` | `local` 0.30, `hf` 0.40 | Bu benzerliğin altındaki parçalar "ilgisiz" sayılır |
| `LLM_PROVIDER` | `claude` | Yanıt üreten sağlayıcı: `claude` ya da `groq` |
| `GROQ_API_KEY` / `GROQ_MODEL` | boş / `openai/gpt-oss-120b` | Groq anahtarı ve modeli |
| `ANTHROPIC_API_KEY` / `CLAUDE_MODEL` | boş / `claude-haiku-4-5-20251001` | Claude anahtarı ve modeli |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Oturum süresi |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | boş / `587` | Kayıt doğrulama kodu ve "Şifremi unuttum" e-postası (Gmail: uygulama şifresi). Boşsa geliştirmede kod sunucu penceresine yazılır, üretimde kayıt/sıfırlama 503 |
| `REQUIRE_EMAIL_VERIFICATION` | `1` | Kayıt olan kişi e-postasına gelen kodu girmeden giriş yapamaz (`0`: hesap hemen açılır) |
| `VERIFY_CODE_MINUTES` | `30` | Doğrulama kodunun geçerlilik süresi |
| `SEND_EMAIL_INLINE` | Vercel'de `1` | E-postayı yanıttan önce gönder (Vercel işlevi yanıttan sonra durdurabilir) |

Tam liste: [`.env.example`](.env.example) · Bulut için hangi değerin nereye yazılacağı: [`docs/dagitim.md`](docs/dagitim.md).

## Sık karşılaşılan sorunlar
| Belirti | Çözüm |
|---|---|
| `python` tanınmıyor | `py -3` kullanın veya Python'u "Add to PATH" ile yeniden kurun |
| Arayüz "Sunucuya ulaşılamadı" diyor | Backend çalışıyor mu (`http://127.0.0.1:8000/health`)? Arayüzün adresi `ALLOWED_ORIGINS` içinde mi? |
| Port 8000 dolu | Diğer pencereyi kapatın, veya `set P55_PORT=8001` (o zaman frontend `public/config.js`'teki adresi de değiştirin) |
| `SECRET_KEY zayıf` uyarısı | `python -m scripts.env_olustur` (yeni `.env` için önce eskisini silin) |
| Sohbet "GROQ_API_KEY ayarlı değil" diyor | `.env` içine anahtarı yazın ve backend'i yeniden başlatın |
| Bulutta yükleme "Dosya deposu ayarlı değil" | Vercel'de `STORAGE_BACKEND=supabase`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` tanımlı mı? |

## Klasör yapısı
```
app/api        sunum katmanı (HTTP uç noktaları)
app/services   iş katmanı (ayrıştırma, parçalama, embedding, RAG, sohbet, rapor, dosya deposu)
app/db         veri katmanı (SQLite / PostgreSQL, migration dosyaları, CRUD)
app/core       ayarlar ve güvenlik (parola özeti, JWT)
scripts/       yönetici oluşturma, .env oluşturma, Supabase kurulumu, örnek veri
tests/         tüm otomatik testler
docs/          tüm belgeler: mimari, geliştirme adımları, AI günlüğü, test raporu, dağıtım
```
Mimari: `api → services → db` (tek yönlü bağımlılık). Ayrıntı: [`docs/mimari.md`](docs/mimari.md) ·
Teknik dokümantasyon (tüm uç noktalar): [`docs/teknik-dokumantasyon.md`](docs/teknik-dokumantasyon.md) ·
Belgelerin dizini: [`docs/README.md`](docs/README.md).

## Güvenlik ve gizlilik
Anahtarlar ve parolalar depoya yüklenmez; gizli değerler `.env`'de (yerel) ve Vercel ortam değişkenlerinde (bulut) tutulur.
Parolalar scrypt ile özetlenir. Supabase tablolarında Row Level Security açıktır (Supabase'in kendi REST API'sinden erişilemez).
Testlerde ve demoda yalnızca **sentetik** veri kullanılır. Ayrıntı: [`docs/guvenlik-notu.md`](docs/guvenlik-notu.md).

## Bilinen sınırlar
Başarısız giriş sayacı bellekte tutulur (yeniden başlatınca sıfırlanır; bulutta her sunucu örneğinin kendi sayacı var) ·
oturum iptali yok (token süresi kısa) · yükleme isteği vektörleştirme bitene kadar bekler (bulutta en fazla 300 sn) ·
bulutta dosya en fazla 50 MB · Supabase ücretsiz projesi 1 hafta kullanılmazsa durdurulur ·
"kaynağa dayalı" yanıt, yanıtın doğru olduğunu kanıtlamaz, yalnızca geçerli bir kaynak gösterdiğini söyler.

## İlerleme
Ders planındaki adımlar, durumları ve kalan işler: [`docs/yol-haritasi.md`](docs/yol-haritasi.md) · Değişiklikler: [`CHANGELOG.md`](CHANGELOG.md).
