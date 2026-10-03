# Değişiklik günlüğü

Biçim: [Keep a Changelog](https://keepachangelog.com/tr-TR/1.1.0/). Tarihler 2026.

## [1.0.0] — final (henüz yayımlanmadı)
- *(Final öncesi son değişiklikler buraya; bkz. `docs/gelistirme/13-final.md`.)*

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
