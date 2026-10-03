# Değişiklik günlüğü

Biçim: [Keep a Changelog](https://keepachangelog.com/tr-TR/1.1.0/). Tarihler 2026.

## [1.0.0] — final (henüz yayımlanmadı)
- *(Final öncesi son değişiklikler buraya; bkz. `docs/gelistirme/13-final.md`.)*

## [0.16.0] — 2026-10-03 · sohbet kalitesi ve sade tema
### Düzeltildi
- **Canlı sitede sohbet, belgede yazan sorulara "bilgi bulamadım" diyordu.** Kök neden: Hugging Face MiniLM'i 128 token'da
  kesiyor, Türkçe 600 karakterlik parçanın ikinci yarısı vektöre girmiyordu. Bulutta embedding modeli **BAAI/bge-m3**
  (8192 token); `hf` için `MIN_SCORE` varsayılanı 0,40. Ölçüm: `docs/istem-deneyleri.md` → "Bulut kalitesi".
- İstem `rag-v2`: kaynakta yanıt (kısmen ya da başka kelimelerle) varsa verilir; `BILGI_YOK` yalnızca kaynakların hiçbiri
  ilgili değilse. `GROQ_REASONING_EFFORT` varsayılanı `medium` (low çok sık "bilgi yok" diyordu).
- Bulutta önerilen `MAX_CHUNKS_PER_DOCUMENT` 3000 → 2000 (bge-m3 ~10 parça/sn, Vercel sınırı 300 sn).
### Değişti
- Arayüz (frontend deposu): sinematik sahne, imleç, paralaks ve kayan açılışlar **kaldırıldı** (`fx.js`, `cinema.js`,
  `vendor/`); yerine keskin siyah-beyaz (monokrom) tema: köşesiz, ince çizgiler, Inter + JetBrains Mono, açık/koyu (seçim yoksa işletim sistemi ayarı). Her hazır
  belgede "Yeniden indeksle" (model değişince eski belgeler aranabilir olsun). Düzeltilen hata: `hidden` nitelikli
  düğmeler CSS yüzünden görünür kalıyordu (giriş sonrası "Giriş yap").

## [0.15.0] — 2026-10-03 · kayıt ve e-posta doğrulama
### Eklendi
- Kayıt ekranı girişten ayrı: **ad soyad**, e-posta, parola + parola tekrarı.
- **E-posta doğrulama:** kayıtta 6 haneli kod (30 dk); doğrulanmamış hesap giriş yapamaz (403). `POST /auth/verify-email` (doğru kodda doğrudan giriş), `POST /auth/resend-verification`.
- `/health` hangi veritabanının kullanıldığını söyler (`"database": "postgres" | "sqlite"`).
- Ayarlar: `REQUIRE_EMAIL_VERIFICATION`, `VERIFY_CODE_MINUTES`.
### Değişti
- `password_resets` tablosu `email_codes` oldu (`purpose`: `verify` / `reset`); kod mantığı `services/email_codes.py`'de ortak. Migration: SQLite `005`, PostgreSQL `002`. Bu migration'dan önceki hesaplar doğrulanmış sayılır.
- Üretimde SMTP ayarı yoksa kayıt da 503 döner (kod ulaştırılamayacak hesap açılmaz).
- Parola sıfırlama, doğrulanmamış hesabı da doğrulanmış yapar (koda e-postadan ulaşıldı).
- Yönetim sekmesinde ad soyad ve "doğrulanmadı" bilgisi.
### Eklendi (aynı gün, devam)
- **Hesabım:** `PATCH /auth/me` (ad), `POST /auth/change-password`, `DELETE /auth/me` (hesap + belgeler + dosyalar); parola isteyen işlemler mevcut parolayı ister, son yönetici kendini silemez. `services/account.py`.
- **Sohbet yeniden adlandırma:** `PATCH /conversations/{id}`.
- Arayüz (frontend deposu): ana sayfada Three.js ile sinematik 3B sahne (`cinema.js`, `vendor/three.min.js`); üst barda "Animasyonlar" düğmesi (işletim sisteminin "hareketi azalt" ayarını ezer); Hesabım sekmesi; belgelerde Türkçe harf duyarsız süzme, sıralama ve özet; sohbet listesinde satır içi yeniden adlandırma; ana sayfa metinleri bulut mimarisine göre güncellendi.

## [0.14.0] — 2026-10-03 · dağıtım hazırlığı
### Eklendi
- **İki depo:** arayüz `P55-RAG-Assistant-frontend`'e taşındı; backend yalnızca API (`GET /` artık JSON).
- **PostgreSQL (Supabase) desteği:** `PgConnection` sarmalayıcısı, `migrations/postgres/001_init.sql` (RLS açık), migration kilidi (`pg_advisory_xact_lock`).
- **pgvector** ile SQL içinde benzerlik araması.
- **Hugging Face embedding** (`EMBEDDING_BACKEND=hf`, aynı çok dilli model), `scripts/hf_dene.py`.
- **Supabase Storage** ile yükleme: `POST /documents/upload-url`, `POST /documents/complete`; arayüz `upload_mode`'a göre seçer.
- **CORS** (`ALLOWED_ORIGINS`), Vercel ayarları (`vercel.json`, `.python-version`, `.vercelignore`), `scripts/supabase_kurulum.py`.
- Şifremi unuttum (e-postayla 6 haneli kod), ana sayfa, koyu/açık tema, 500 MB'a kadar akışlı yükleme (yerel).
- Belgeler: `docs/teknik-dokumantasyon.md`, `docs/dagitim.md`, `docs/yol-haritasi.md`; haftalık belgeler `docs/` altında birleşti.
- Testler: `tests/test_bulut.py`; tüm testler `P55_TEST_PG_URL` ile PostgreSQL'e karşı da koşabiliyor.
### Değişti
- `requirements.txt` sunucu için (torch'suz); yerel model `requirements-local.txt`'te.
- Testler `hafta-XX/` yerine `tests/` altında.
- Repo SQL'i iki veritabanında çalışacak biçimde: `RETURNING id`, `ON CONFLICT`, `substr(...)`.
### Düzeltildi
- İkili/bozuk metin dosyasında NUL karakteri PostgreSQL'de 500 hatasına yol açıyordu; ayrıştırıcı NUL'ları atıyor.
- Supabase yeni gizli anahtarları (`sb_secret_…`) `apikey` başlığıyla gönderiliyor (Bearer olarak reddedilir).

## [0.13.0] — test ve hata ayıklama
Sınır durumu testleri; 6 gerçek hata düzeltildi (uzun dosya adında uzantı kaybı, `verify_password(None)`, sınırsız başarısız giriş sayacı, üretimde zayıf `SECRET_KEY`, DOCX sıkıştırma bombası, sınırsız arama sorgusu). Ayrıntı: `docs/duzeltilen-hatalar.md`.

## [0.12.0] — rapor ve yönetim
Kullanım/kaynak raporu, günlük grafik, CSV (formül enjeksiyonu önlemli), yönetici paneli.

## [0.11.0] — sohbet geçmişi
Sohbetler, takip sorusunu bağımsız soruya çevirme, uzun geçmişte özetleme, yanıt kalitesi alanları.

## [0.10.0] — RAG
Kaynaklı yanıt, `MIN_SCORE` eşiği, `[n]` alıntı doğrulama, `BILGI_YOK` kuralı, prompt injection'a karşı istem.

## [0.9.0] — LLM istemcisi
Claude ve Groq istemcileri (urllib), yeniden deneme, zaman aşımı, anlaşılır hatalar.

## [0.1.0] — vize (`v0.1-vize`)
Kurulum, katmanlı mimari, SQLite şeması ve migration'lar, kimlik doğrulama, belge yükleme/ayrıştırma/parçalama, embedding ve vektör arama, web arayüzü.
