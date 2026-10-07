# Değişiklik günlüğü

Biçim: [Keep a Changelog](https://keepachangelog.com/tr-TR/1.1.0/). Tarihler 2026.

## [1.0.0] — final (henüz yayımlanmadı)
- *(Final öncesi son değişiklikler buraya; bkz. `docs/gelistirme/13-final.md`.)*

## [0.20.0] — 2026-10-07 · Ana sayfa "stüdyo" tasarımı (frontend)
### Değişti
- Ana sayfa, kullanıcının gösterdiği örnekteki (Keychron K4 tanıtım sitesi) yapıya göre yeniden tasarlandı:
  gri stüdyo degradesi, şeffaf üst bar (noktalı menü, altı çizili "Giriş yap"), solda `001 / 005` sayacı,
  köşelerde "Kaynak kod" ve "Kaydır", büyük harfli Montserrat başlıklar. Tek vurgu rengi turuncu, yalnızca 3B sahnede.
- **3B stüdyo** (`public/studio.js`, Three.js 0.186.1, `public/vendor/three/`): klavye gibi bir "belge" — tepsi +
  60 tuş, her tuş bir parça. Açılışta tuşlar yılan gibi akıp yerine oturur; kaydırdıkça 5 sahne: toplanmış belge →
  parçalara ayrılır → anlam vektörü (yükseklik) → soruya en yakın 3 parça turuncu → `[1] [2] [3]` kaynaklı yanıt.
  Tuş konumları her karede `sahne(p) + açılış(intro)` fonksiyonuyla hesaplanır; GSAP yalnızca iki sayıyı değiştirir.
- Eski SVG "Nasıl çalışır" sahnesi ve hero kaldırıldı (stüdyo aynı 4 adımı anlatıyor); canlı sohbet örneği kaldı.
- Animasyon kapalıyken, WebGL ya da GSAP yoksa: sahneler alt alta, 3B nesne tek kare (ya da hiç) gösterilir.
  Giriş yapınca uygulamanın normal üst barı ve renkleri geri gelir.

## [0.19.0] — 2026-10-07 · Animasyonlu ana sayfa (frontend)
### Eklendi
- Ana sayfa yeniden tasarlandı (siyah-beyaz kalır), animasyonlar **GSAP 3.15** + ScrollTrigger + SplitText ile
  (`public/home.js`; kütüphane `public/vendor/`, internetsiz de çalışır):
  - Başlıklar satır satır maskenin altından açılır.
  - **Canlı örnek:** soru yazılır, belge taranır, ilgili madde işaretlenir, yanıt `[1]` ile o maddeye bağlanır;
    üçüncü örnekte belgede bilgi yoktur ve asistan uydurmaz.
  - **Nasıl çalışır:** geniş ekranda bölüm sabitlenir, kaydırdıkça sahne ilerler (yükle → parçala → anlam
    uzayında noktalar → soruya en yakın üç parça → `[1] [2] [3]` kaynaklı yanıt). Dar ekranda sabitleme yok.
- Üst barda **Animasyonları kapat/aç** düğmesi (tercih tarayıcıda hatırlanır). Kapatınca `gsap.matchMedia().revert()`
  her şeyi HTML'deki animasyonsuz hâline döndürür; giriş yapınca ana sayfa animasyonları durur.
- Yazı tipleri: başlıklar Archivo (dar), belge örnekleri Source Serif 4.
### Düzeltildi (geliştirirken bulundu)
- Kaydırmaya bağlı zaman çizelgesi geri alınınca SVG sahnesinde gizleme stilleri kalıyordu (animasyon kapatılınca
  sahne boş görünüyordu) → `stop()` SVG'deki satır içi stilleri siler.

## [0.18.2] — 2026-10-07 · Ürün adı: Belge Tabanlı Soru Asistanı
### Değişti
- Arayüzde, e-postalarda, PDF raporunda, API başlığında ve belgelerde "P55" yerine **Belge Tabanlı Soru Asistanı**.
  Depo adları (`P55-RAG-Assistant-…`) ve ders formları (`docs/raporlar/`, AI günlüğü, vize raporu) değişmedi:
  P55 dersin verdiği proje numarası.
- Kişisel API anahtarı öneki `p55_` → `bsa_`. **Eski `p55_` anahtarları süresi dolana kadar çalışır**
  (`api_tokens.LEGACY_PREFIXES`, test: `test_eski_p55_onekli_anahtar_calismaya_devam_eder`).
- Yerel veritabanı dosyası `data/p55.db` → `data/asistan.db` (`.env`'de `DATABASE_URL` elle yazılıysa o satır da değişmeli).
- Test ortam değişkeni `P55_TEST_PG_URL` → `TEST_PG_URL`; günlük (logger) adı `p55.mailer` → `asistan.mailer`;
  genel sohbet istemi `genel-v1` → `genel-v2` (yalnızca kendini tanıttığı ad değişti).
- Frontend: JS ad alanı `P55` → `App`, `P55_CONFIG` → `APP_CONFIG`, tarayıcı anahtarları `p55_token`/`p55_theme` →
  `asistan_token`/`asistan_theme` (yayından sonra herkes bir kez yeniden giriş yapar, tema bir kez sistem ayarına döner).

## [0.18.1] — 2026-10-04 · API anahtarı bildirimi ve yönetici denetimi
### Eklendi
- Anahtar oluşturulunca hesap sahibine **bildirim e-postası** (ad, ilk 12 karakter, tarihler; anahtarın kendisi yok):
  parolası ele geçirilip anahtar üretilirse sahibi haberdar olur.
- **Yönetici:** `GET /admin/tokens` (tüm anahtarlar, sahibiyle; anahtarın kendisi/özeti yok) ve
  `DELETE /admin/tokens/{id}` (iptal; sahibine e-posta). Yönetim sekmesinde "API anahtarları" tablosu.
  Yönetici anahtar **üretemez**: hesaba yalnızca anahtarı oluşturan sahibi girebilir.
### Değişti
- E-posta gönderme yardımcısı `api/auth._deliver` → ortak `api/deps.deliver_email` (yönetici ucu da kullanıyor).

## [0.18.0] — 2026-10-04 · kişisel API anahtarları
### Eklendi
- **Kişisel API anahtarı (3. parti uygulamalar için):** Hesabım → "API anahtarları"ndan ad + geçerlilik (7/30/90/365 gün)
  seçilerek `p55_…` anahtarı üretilir; Postman, betik ya da bot `Authorization: Bearer p55_…` ile API'ye bağlanır.
  Veritabanında yalnızca SHA-256 özeti (`api_tokens`, migration `006` / PostgreSQL `003`); anahtar bir kez gösterilir,
  sekmeden çıkınca ekrandan silinir. Liste: ad, ilk 12 karakter, son kullanım, bitiş; tek tek silinebilir.
- `GET/POST /auth/tokens`, `DELETE /auth/tokens/{id}`; `MAX_API_TOKENS_PER_USER` (10).
### Değişti
- Hesap yönetimi (ad/parola değiştirme, hesap silme, anahtar işlemleri) ve yönetici uçları yalnızca giriş oturumuyla
  (`require_session`); API anahtarıyla 403.
- `.env.example` ve `baslat.bat` depodan kaldırıldı (geliştirici kararı). `.env` şablonu artık
  `scripts/env_olustur.py` içinde; ayarların tam listesi README'de. Kurulum komutlarla anlatılıyor.

## [0.17.0] — 2026-10-03 · büyük belge ve genel sohbet
### Eklendi
- **Parça parça indeksleme:** bir istekte en fazla `INDEX_BUDGET_SECONDS` (Vercel'de 60 sn) indekslenir; belge `chunked`
  kalır ve `POST /documents/{id}/index-next` kaldığı yerden devam eder ("bu modelle vektörü olmayan parçalar").
  Arayüz gerçek yüzdeyi gösterir ("%40 (800 / 2000 parça)"); yarıda kalan belgede **Devam et**. Bulutta parça sınırı
  2000 → 20000. Model değişince eski vektörler silinmeden yenileriyle değiştirilir; embedding yarıda koparsa o ana
  kadarkiler korunur.
- **Genel sohbet (`GENERAL_CHAT=1`):** belgelerde yanıt yoksa (no_context / no_info) selamlaşma ve genel sorulara
  modelin genel bilgisiyle kısa yanıt; durum `general`, kaynaksız, `grounded=False`, arayüzde kesik çizgili balon ve
  "belgelerinden değil" notu. Raporda ayrı sayılır, kaynağa dayalı oranına girmez. İstem `genel-v1`.
### Düzeltildi
- **CSV indir bozuktu:** arayüz dosyayı `res.text()` ile okuyunca UTF-8 BOM'u siliniyordu → Excel Türkçe karakterleri
  bozuk gösteriyordu; virgül ayraç Türkçe Excel'de satırı tek hücreye yığıyordu. Şimdi dosya blob olarak indirilir (BOM
  korunur), ayraç `;`, ondalık virgül, oranlar yüzde, etiketler Türkçe, dosya adında tarih.

- **Rapor PDF olarak indirilir** (`GET /reports/usage.pdf`, reportlab, Türkçe yazı tipi Vera): CSV Excel'in bölgesel
  ayarına göre hâlâ sorunlu açılıyordu; arayüzdeki "CSV indir" yerine "PDF indir". CSV ucu API'de kalır.

### Sınır (değişmedi)
- Dosya başına 50 MB: Supabase ücretsiz planının sınırı (kodla aşılamaz).

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
