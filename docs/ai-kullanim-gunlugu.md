# AI Kullanım Günlüğü

> Ders kuralı: yapay zekâ "AI Pair Programmer"dır. Her kaydın **"Kendi yaptığım değişiklik / doğrulama"** alanını Samet DOĞANGÜN doldurur; boş alanlar henüz yapılmamış işlerdir.

> **08.10.2026 notu:** "Kendi yaptığım değişiklik / doğrulama" alanları, Claude Code'un oturum kayıtlarından çıkardığı "geliştiricinin kararları, bulduğu hatalar ve kendi yaptığı işler" listesinin Samet DOĞANGÜN tarafından doğru olarak onaylanmasının ardından, bu listeye dayanarak yazılmıştır. Listede yer almayan bir iş kendi işim olarak yazılmamıştır; yapılmayan işler açıkça "yapmadım" diye belirtilmiştir. Form 8 tablosundaki "Açıklar mı? (E/H)" sütunu yalnızca geliştiricinin kendi beyanıdır ve bu yüzden boş (💬) bırakılmıştır.

> Kayıtlardaki `pytest hafta-XX` komutları eski klasör düzenine aittir (kaydın yazıldığı an). Testler artık `tests/` klasöründe; eşleme `docs/README.md` içinde.

## Form 8 — Yapay Zekâ Kullanım Günlüğü tablosu (ders paketi biçimi)

| | | | |
|---|---|---|---|
| **Öğrenci** | Samet DOĞANGÜN | **Numara** | 211161024 |
| **Proje (Kod/Ad)** | P55 – Belge Tabanlı Soru-Cevap Asistanı (RAG) | **Son güncelleme** | 08.10.2026 |

**İlke (ders paketi):** Öğrenci yapay zekâdan aldığı her anlamlı yardımı bu günlüğe işler. "Açıklar mı?" sütunu **E**
olmayan hiçbir kod parçası teslim edilemez. Her satırın ayrıntısı (istem, çıktı, gerekçe) aşağıdaki "Adım" kayıtlarında.
💬 sütunlarını **yalnızca öğrenci** doldurur: kendi değişikliğini/doğrulamasını yazar ve kodu açıklayabiliyorsa **E** koyar.
Her hafta yeni satırlar eklenir. (≤ 02.10: proje dosyalarının devralındığı 02.10.2026'dan önceki Claude sohbeti.)

| Tarih | Araç | Amaç/Görev | İstem (özet) | Öğrencinin Değişikliği/Doğrulaması | Açıklar mı? (E/H) |
|---|---|---|---|---|---|
| ≤ 02.10 | Claude | Mimari, ER (Adım 1) | Kurulum, katmanlı klasör yapısı, ER diyagramı, mimari şema | Teknoloji yığınını (Python + FastAPI, SQLite, ücretsiz yerel embedding, web arayüzü) ve klasör düzenini ben seçtim | 💬 |
| 02.10 | Claude Code | Ortam kurulumu (Adım 1) | Python/Git kur, testleri gerçek paketlerle çalıştır | Kurulumu kendi bilgisayarımda onayladım; 176 test geçti, 1 atlandı | 💬 |
| ≤ 02.10 | Claude | Veritabanı (Adım 2) | SQLite şeması, migration, CRUD, sentetik veri | 12 test kendi bilgisayarımda geçti (yabancı anahtar ve CASCADE dahil); veri yalnızca sentetik | 💬 |
| ≤ 02.10 | Claude | Kimlik doğrulama (Adım 3) | Kayıt/giriş, parola özetleme, token, roller | 19 test geçti; gerçek sunucuda 401 / 403 / 409 davranışları görüldü | 💬 |
| ≤ 02.10 | Claude | Belge işleme (Adım 4) | Yükleme, TXT/PDF/DOCX ayrıştırma, parçalama | 24 test geçti; TXT, PDF ve DOCX gerçek yüklemede indekslendi, `.exe` reddedildi | 💬 |
| ≤ 02.10 | Claude | Embedding (Adım 5) | Parçaları vektörleştirme, vektör arama, yerel model | Ücretli API yerine yerel ücretsiz modeli ben seçtim; Türkçe aramada doğru belge ilk sırada geldi | 💬 |
| ≤ 02.10 | Claude | Entegrasyon, arayüz (Adım 6) | Modülleri bağlama, web arayüzü, vize hazırlığı | Arayüz tarayıcıda denendi (konsol temiz); uçtan uca HTTP testi geçti | 💬 |
| ≤ 02.10 | Claude | LLM istemcisi (Adım 7) | Claude API istemcisi, zaman aşımı/yeniden deneme | API anahtarının yalnızca `.env` dosyasında tutulmasını sağladım; depoda anahtar yok | 💬 |
| 03.10 | Claude Code | Groq desteği (Adım 7) | Ücretsiz katmanlı Groq, sağlayıcı `.env`'den seçilsin | Groq'u ücretsiz olduğu için ben seçtim; sohbete yapıştırılıp sızan ilk anahtarı iptal edip yenisini `.env`'e kendim yazdım | 💬 |
| ≤ 02.10 | Claude | RAG (Adım 8) | Kaynaklı yanıt, halüsinasyon önleme, istem tasarımı | Gerçek Groq ile kaynaklı yanıtı ve belgede olmayan soruya "bilgi bulamadım" davranışını arayüzde gördüm | 💬 |
| ≤ 02.10 | Claude | Sohbet geçmişi (Adım 9) | Kalıcı geçmiş, özetleme, takip sorusunu yeniden yazma | Sohbet arayüzünü tarayıcıda açtım; sohbet oluşturma ve listeleme çalıştı | 💬 |
| ≤ 02.10 | Claude | Rapor, yönetim (Adım 10) | Kullanım raporu, toplulaştırma sorguları, yönetici paneli | CSV raporun Excel'de bozuk açıldığını ben fark ettim; PDF rapora geçme kararı benim (Hata 10) | 💬 |
| ≤ 02.10 | Claude | Test (Adım 11) | Sınır durumlarını test et, bulunan hataları düzelt | Testler kendi bilgisayarımda çalıştırıldı ve geçti | 💬 |
| 02.10 | Claude Code | Gerçek ortamda doğrulama (Adım 11) | Testleri gerçek FastAPI ile, tarayıcıda dene, kapsamı ölç | 03.10'da 191 testten 190'ı geçti, 1 atlandı; kapsam %95 | 💬 |
| 03.10 | Claude Code | Büyük dosya, tema, şifremi unuttum (Adım 12) | 500 MB yükleme, yeni tema, e-postayla parola sıfırlama | Sıfırlama kodunun e-postayla gönderilmesi ve "en fazla 500 MB" yazısının kalması benim kararım | 💬 |
| 03.10 | Claude Code | İki depo + bulut (Adım 12) | Frontend/backend ayrı depo, Supabase + Vercel + HF | İki depo, Supabase ve Vercel kararı benim; hesapları açtım, Vercel değişkenlerini girdim, yöneticiyi `create_admin` ile açtım | 💬 |
| 03.10 | Claude Code | Kayıt ekranı, e-posta doğrulama (Adım 12) | Ayrı kayıt ekranı, ad soyad, e-posta kodu | SMTP ayarlarını Vercel'e girdim; canlıda gerçek doğrulama e-postası bana ulaştı | 💬 |
| 03.10 | Claude Code | Hesabım, arayüz (Adım 12) | Profil/hesap ayarları, belge/sohbet kullanılabilirliği | Animasyonların bende görünmediğini bildirdim (neden: Windows "Animasyon efektleri" kapalı); sahneyi sonra kaldırttım | 💬 |
| 03.10 | Claude Code | Sohbet kalitesi, tema (Adım 12) | Chatbot kötü yanıt veriyor; sade siyah-beyaz tema | Kötü yanıtları canlıda fark ettim; Vercel'de `GROQ_REASONING_EFFORT=medium` yaptım, belgeleri yeniden indeksledim; indigo temayı reddedip siyah-beyazı seçtim | 💬 |
| 03.10 | Claude Code | Büyük belge, genel sohbet (Adım 12) | Büyük dosyalar parça parça; selamlaşma/genel soru | Parça sınırının kaldırılması ve etiketli genel sohbet benim seçimim; Vercel'de `MAX_CHUNKS_PER_DOCUMENT=20000` yaptım | 💬 |
| 04.10 | Claude Code | Kişisel API anahtarı (Adım 12) | 3. parti uygulamalar için kullanıcıya özel token | Üç seçenek arasından kişisel API anahtarını ben seçtim; kendi betiğimle ayrıca denemedim | 💬 |
| 04.10 | Claude Code | Ders formları (raporlar) | Ders paketindeki rapor şablonlarını depoya ekle | Öğrenci numaramı verdim; 💬 öz değerlendirme alanlarını ve risk puanlarını henüz doldurmadım | 💬 |
| 04.10 | Claude Code | Teslim kontrolü, gerekçeler (Adım 1) | Haftalık teslimler GitHub'da mı; gerekçe bölümlerini doldur | Gerekçe metinlerindeki kararlar benim; metinleri Claude Code yazdı, kendi cümlelerimle yeniden yazmadım | 💬 |
| 04.10 | Claude Code | API anahtarı bildirimi, yönetici denetimi (Adım 12) | Anahtar oluşunca e-posta; yönetici anahtarları görsün | İlk isteğim (habersiz yönetici anahtarı) güvenlik ve KVKK gerekçesiyle uygulanmadı; "yönetici yalnızca görsün ve iptal etsin" seçeneğini ben seçtim | 💬 |
| 07.10 | Claude Code | Ad değişikliği (Adım 12) | Arayüzde "P55" yerine "Belge Tabanlı Soru Asistanı" | Yeni adı ve depo / ders formu adlarının P55 olarak kalmasını ben seçtim | 💬 |
| 07.10 | Claude Code | Animasyonlu ana sayfa (Adım 12) | Örnek videodaki gibi animasyonlu ana sayfa; GSAP, ardından Keychron tarzı 3B sahne | Skill kurulumunu onayladım; siyah-beyazın kalmasını, GSAP'ı ve Keychron tarzını ben seçtim; sonra kaydırmalı 5 sahneyi kaldırtıp tek açılış animasyonu istedim | 💬 |
| 07.10 | Claude Code | Hugging Face 402 → Gemini (Adım 12) | Canlıda belge yüklenince 402 hatası | Hatayı canlıda ben buldum; Gemini'yi seçtim, anahtarı aldım, Vercel'de `EMBEDDING_BACKEND` ayarını düzelttim (Hata 9) | 💬 |
| 08.10 | Claude Code | Teslim kontrolü (Adım 13) | P55 gereksinimleri karşılanıyor mu; sözlü sorular; eksikler | Tabloyu inceledim, yaptıklarımın listesini onayladım; "kendi yapacakların" kod görevlerini ayrıca yapmadım | 💬 |

## Adım 1 — Kurulum, mimari ve ER diyagramı (Hafta 3)

> Ders kuralı: her anlamlı yardım için araç, istem, çıktı ve **senin** değişiklik/doğrulaman yazılır.
> Aşağıdaki "kendi" alanlarını teslimden önce doldur; boş bırakma.

### Kayıt 1
- **Araç:** Claude
- **İstem (özet):** P55 (RAG) projesinin Hafta 3 kapsamı: kurulum, katmanlı klasör yapısı, GitHub depo dosyaları, ER diyagramı ve mimari şema.
- **Aldığım çıktı (özet):** FastAPI iskeleti, `.gitignore`, `.env.example`, ER diyagramı taslağı (Mermaid), katmanlı mimari şeması.
- **Kendi yaptığım değişiklik / doğrulama:** Doğrulama (kendi bilgisayarımda — Windows 11, Python 3.12 — Claude Code ile birlikte çalıştırıldı): `pytest hafta-03` → 6 test geçti (2026-10-03). Gerçek sunucuda `/health` → `{"status": "ok"}` döndü (2026-10-02, 39 isteklik HTTP denemesinin parçası). Teknoloji seçimlerini ben yaptım: Python + FastAPI, SQLite (saf SQL), yerel ücretsiz embedding, basit web arayüzü, ortak `app/` + haftalık `hafta-XX/` klasör düzeni. Ders planındaki "öğrencinin kendi geliştireceği bölümler" görevlerini bu adımda ayrıca yapmadım (durum: `docs/raporlar/teslim-kontrol-listesi.md`).
- **Neden bu çözümü kullandım:** Katmanlı yapı (`api → services → db`) her katmanı ayrı test etmeyi ve sözlüde tek tek anlatmayı kolaylaştırıyor. SQLite kurulum gerektirmiyor (tek dosya), ders projesinin ölçeğine yetiyor. FastAPI otomatik Swagger belgesi veriyor; demo ve test için pratik.

### Kayıt 2 (geliştirme ortamının kurulumu)
- **Araç:** Claude Code
- **İstem (özet):** Projeyi kendi bilgisayarımda çalıştırmak için ortamı kur; testleri gerçek paketlerle çalıştır.
- **Aldığım çıktı (özet):** Bilgisayarımda `python` komutu yoktu (yalnızca Visual Studio'nun Python 3.9'u vardı). Python 3.12.10 ve Git 2.55 `winget` ile kuruldu, `venv` sanal ortamı ve `.env` (rastgele `SECRET_KEY`) oluşturuldu.
- **Kendi yaptığım değişiklik / doğrulama:** Kurulumu kendi bilgisayarımda onayladım; `pytest` ile tüm testlerin geçtiği görüldü (2026-10-02: 176 geçti, 1 atlandı).

### Kayıt 3 (gerekçe bölümleri ve teslim kontrolü — 2026-10-04)
- **Araç:** Claude Code
- **İstem (özet):** "Ders dosyasında P55 için her hafta teslim edilmesi gereken her şey GitHub'da mı kontrol et; kendi gerekçem bölümünü doldur."
- **Aldığım çıktı (özet):** Ders paketindeki P55 haftalık planının (hafta 3–15) "Teslim Edilecek Çıktılar" maddeleri iki depoyla karşılaştırıldı. Eksikler: `v0.1-vize` etiketi atılmamıştı (vize raporunda yazıyordu; bu kayıtla iki depoda atıldı), haftalık ilerleme raporları ve ekran görüntüleri henüz depoda yok, final etiketi ve sunum (hafta 15) bekliyor. `mimari.md` → "Gerekçem", `er-diyagrami.md` → "Kendi gerekçem" ve proje öneri formundaki "Seçimlerimin gerekçesi" metinleri, benim verdiğim teknoloji kararlarına (SQLite → Supabase, iki depo, ücretsiz servisler) göre Claude Code tarafından yazıldı. Ardından güncel arayüzün 10 ekran görüntüsü, geçici bir veritabanında sentetik veriyle (Edge + Playwright betiği) alınıp `docs/ekran-goruntuleri/`'ne eklendi; sohbet yanıtları gerçek Groq API'sinden geldi. 02.10'daki 2 eski görüntü `ilk-surum/` altında.
- **Kendi yaptığım değişiklik / doğrulama:** Gerekçe bölümlerinde anlatılan kararların tamamı benimdir: başlangıçta Python + FastAPI, SQLite ve yerel ücretsiz embedding'i; daha sonra bilgisayarımın sunucu olması fikrinden vazgeçerek iki ayrı GitHub deposunu, Supabase'i ve Vercel'i seçtim. Metinler bu kararlara göre Claude Code tarafından yazıldı; kendi cümlelerimle yeniden yazmadım. Ekran görüntüleri sentetik veriyle alındı.
- **Neden bu çözümü kullandım:** _(kendi cümlelerinle)_

## Adım 2 — Veritabanı şeması, migration ve CRUD (Hafta 4)

> "Kendi" alanlarını teslimden önce doldur.

### Kayıt 1
- **Araç:** Claude
- **İstem (özet):** SQLite şeması (migration), ilişkiler/kısıtlar/indeksler, sentetik seed verisi ve CRUD veri erişim fonksiyonları.
- **Aldığım çıktı (özet):** `001_init.sql`, migration çalıştırıcı, `users/documents/chunks` CRUD modülleri, seed betiği, testler.
- **Kendi yaptığım değişiklik / doğrulama:** Doğrulama (kendi bilgisayarımda — Windows 11, Python 3.12 — Claude Code ile birlikte çalıştırıldı): `pytest hafta-04` → 12 test geçti (migration, CRUD, yabancı anahtar ve CASCADE silme). Sentetik verinin tamamı `@example.com` adresli. Ders planındaki "öğrencinin kendi geliştireceği bölümler" görevlerini bu adımda ayrıca yapmadım (durum: `docs/raporlar/teslim-kontrol-listesi.md`).
- **Neden bu çözümü kullandım:** Saf SQL: tabloların, kısıtların ve sorguların ne yaptığını doğrudan görüyor ve açıklayabiliyorum (ORM bunu gizlerdi). Migration: şema değişiklikleri numaralı dosyalarla sırayla uygulanıyor; nitekim sonraki haftalarda `002` (mesaj kalitesi) ve `003` (sohbet özeti) eski veriyi bozmadan eklendi.

## Adım 3 — Kimlik doğrulama ve roller (Hafta 5)

> "Kendi" alanlarını teslimden önce doldur. Güvenlik kodunu açıklayamıyorsan puanlanmaz: önce `aciklama.md` oku, sonra kendi değişikliğini yap.

### Kayıt 1
- **Araç:** Claude
- **İstem (özet):** Kayıt/giriş akışı, parola hash'leme, token yönetimi ve rol tabanlı erişim (kullanıcı/yönetici); güvenli desenler ve yaygın açıklar.
- **Aldığım çıktı (özet):** scrypt+tuz ile hash, JWT, `get_current_user`/`require_admin`, başarısız giriş kilidi, güvenlik notu, testler.
- **Kendi yaptığım değişiklik / doğrulama:** Doğrulama (kendi bilgisayarımda — Windows 11, Python 3.12 — Claude Code ile birlikte çalıştırıldı): `pytest hafta-05` → 19 test geçti. Gerçek sunucuda (2026-10-02): token yok / bozuk token → 401, normal kullanıcının yönetici ucuna erişimi → 403, zayıf parola → 400, tekrar kayıt → 409. Ders planındaki "öğrencinin kendi geliştireceği bölümler" görevlerini bu adımda ayrıca yapmadım (durum: `docs/raporlar/teslim-kontrol-listesi.md`).
- **Neden bu çözümü kullandım:** scrypt: Python'un standart kütüphanesinde var (ek paket yok), tuzlu ve bilerek yavaş/bellek yoğun; kaba kuvvet denemelerini pahalılaştırıyor. JWT: sunucuda oturum tablosu tutmadan imzalı, süreli token; rolü her istekte veritabanından okuduğum için rol değişikliği hemen geçerli oluyor.

## Adım 4 — Belge yükleme, ayrıştırma ve parçalama (Hafta 6)

> "Kendi" alanlarını teslimden önce doldur. Chunking algoritmasını açıklayabilmen şart: `aciklama.md`'yi oku, sonra kendi yöntemini yaz.

### Kayıt 1
- **Araç:** Claude
- **İstem (özet):** Belge yükleme, TXT/PDF/DOCX metin ayrıştırma ve cümle sınırlı, örtüşmeli parçalama modülü; doğrulama ve sahiplik kuralları.
- **Aldığım çıktı (özet):** `parser.py`, `chunker.py`, `documents.py` servisi, belge API uçları, testler.
- **Kendi yaptığım değişiklik / doğrulama:** Doğrulama (kendi bilgisayarımda — Windows 11, Python 3.12 — Claude Code ile birlikte çalıştırıldı): `pytest hafta-06` → 24 test geçti. Gerçek sunucuda TXT, PDF ve DOCX yüklemeleri `indexed` oldu, `.exe` 400 ile reddedildi. Ders planındaki "öğrencinin kendi geliştireceği bölümler" görevlerini bu adımda ayrıca yapmadım (durum: `docs/raporlar/teslim-kontrol-listesi.md`).
- **Neden bu çözümü kullandım:** Parçalar cümle sınırlarına göre bölünüyor ve ardışık parçalar örtüşüyor (600 / 100 karakter): bir bilgi iki parçanın sınırına denk gelse de kaybolmuyor. 600 karakter (≈149 token) yerel embedding modelinin 256 token sınırına sığıyor. Dosya uzantısı içerikle (`%PDF-`, `PK`) karşılaştırılıyor; diske kullanıcının verdiği ad değil rastgele ad yazılıyor (yol saldırısı olmaz).

## Adım 5 — Embedding ve vektör arama (Hafta 7)

> "Kendi" alanlarını teslimden önce doldur. Embedding ve kosinüs benzerliğini kendi cümlenle anlatabilmelisin.

### Kayıt 1
- **Araç:** Claude
- **İstem (özet):** Parçaları embedding'e çeviren, vektörleri SQLite'ta saklayan ve benzerlik arama yapan modül; yerel ücretsiz embedding.
- **Aldığım çıktı (özet):** `embedder.py`, `embeddings.py`, `indexing.py`, `vector_search.py`, `/search` ve `/reindex` uçları, testler.
- **Kendi yaptığım değişiklik / doğrulama:** Doğrulama (kendi bilgisayarımda — Windows 11, Python 3.12 — Claude Code ile birlikte çalıştırıldı): `pytest hafta-07` → 20 test geçti, 1 atlandı (sentence-transformers kurulu olduğu için "paket yok" testi kendini atlıyor; beklenen). Gerçek modelle Türkçe aramada doğru belge ilk sırada geldi; belgede olan/olmayan 10 soruluk skor ölçümü `hafta-13/TEST_RAPORU.md` §6'da (olan ≥ 0,430, olmayan ≤ 0,270). Bu bilgisayarda yerel model ≈ 43 parça/sn vektörleştiriyor. Ders planındaki "öğrencinin kendi geliştireceği bölümler" görevlerini bu adımda ayrıca yapmadım (durum: `docs/raporlar/teslim-kontrol-listesi.md`).
- **Neden bu çözümü kullandım:** Yerel embedding: ücretsiz, internete ve API anahtarına bağlı değil, belgeler dışarı gönderilmiyor (gizlilik); çok dilli model Türkçeyi anlıyor. Kosinüs benzerliği: vektörlerin yönünü karşılaştırıyor, metin uzunluğundan etkilenmiyor; vektörler normalize olduğu için tek bir matris çarpımıyla hızlı hesaplanıyor.

## Adım 6 — Entegrasyon ve web arayüzü (vize) (Hafta 8)

> Ders kuralı: her anlamlı yardım için araç, istem, çıktı ve **kendi** değişiklik/doğrulama yazılır. Ayrıntılı kayıtlar her haftanın `ai-log.md` dosyasındadır.
> Vizede açıklayamadığın kod puanlanmaz: aşağıdaki "kendi" sütununu doldurmadan teslim etme.

| Hafta | Araç | İstem (özet) | Çıktı (özet) | Kendi değişiklik / doğrulamam |
|---|---|---|---|---|
| 3 | Claude | Mimari, klasör yapısı, ER diyagramı | Katmanlı iskelet, ER taslağı | Teknoloji ve klasör düzeni kararlarını ben verdim; ortam kuruldu, 6 test geçti, `/health` gerçek sunucuda çalıştı |
| 4 | Claude | SQLite şeması, CRUD, sentetik veri | Migration, CRUD modülleri, seed | 12 test geçti (FK/CASCADE dahil); veri yalnızca sentetik |
| 5 | Claude | Güvenli kimlik doğrulama, roller | scrypt, JWT, `require_admin` | 19 test geçti; gerçek sunucuda 401/403/409 davranışları görüldü |
| 6 | Claude | Belge yükleme, ayrıştırma, chunking | parser, chunker, yükleme kuralları | 24 test geçti; TXT/PDF/DOCX gerçek yükleme `indexed`, `.exe` reddedildi |
| 7 | Claude | Embedding, vektör arama | embedder, vektör saklama, arama | Ücretli API yerine yerel ücretsiz modeli seçtim; 21 test; gerçek modelle Türkçe aramada doğru belge ilk sırada |
| 8 | Claude | Entegrasyon, arayüz, vize hazırlığı | Web arayüzü, uçtan uca test, belgeler | Arayüz tarayıcıda denendi (konsol temiz); `TestClient` ile gerçek HTTP testi geçti |

### Genel notlar
- Yapay zekâ çıktılarını çalıştırarak ve testlerle doğruladım: Tüm testler kendi bilgisayarımda gerçek FastAPI/pytest ile çalıştırıldı (2026-10-02: 176 geçti, 1 atlandı). Gerçek sunucuya 39 istekle kayıt → giriş → yükleme → arama → rapor → yönetim akışı denendi; arayüzün tüm sekmeleri tarayıcıda açıldı, konsolda hata yoktu.
- Yapay zekâ çıktısında düzelttiğim / reddettiğim bir şey: Gerçek ortamda bir test kırıldı (önceki ortamın sahte FastAPI'sinde var olan `Response.content`, gerçek Starlette'te `Response.body`); düzeltildi. Ücretli bir embedding API'si yerine yerel ücretsiz modeli tercih ettim.
- KVKK: Yapay zekâ araçlarına gerçek kişisel veri girmedim; yalnızca sentetik veri kullandım. ✅

## Adım 7 — Harici LLM API istemcisi (Hafta 9)

> "Kendi" alanlarını teslimden önce doldur. Hata yönetimi akışını (hangi hatada yeniden dener, hangisinde dener etmez) açıklayabilmelisin.

### Kayıt 1
- **Araç:** Claude
- **İstem (özet):** Claude Messages API'sine REST ile bağlanan, zaman aşımı/yeniden deneme/hata yönetimi olan istemci; API anahtarının güvenli saklanması; arama hızının ölçülmesi.
- **Aldığım çıktı (özet):** `llm_client.py`, hata eşleme, `/admin/llm-test`, benchmark betiği, yerel sahte sunucuyla testler.
- **Kendi yaptığım değişiklik / doğrulama:** Doğrulama (kendi bilgisayarımda — Windows 11, Python 3.12 — Claude Code ile birlikte çalıştırıldı): `pytest hafta-09` → 28 test geçti (Claude + Groq istemcileri, yerel sahte sunucuya karşı). Anahtar yalnızca `.env` dosyasında; `.env` `.gitignore`'da. Ders planındaki "öğrencinin kendi geliştireceği bölümler" görevlerini bu adımda ayrıca yapmadım (durum: `docs/raporlar/teslim-kontrol-listesi.md`).
- **Neden bu çözümü kullandım:** urllib: ek bağımlılık yok ve HTTP isteğinin her parçası (adres, başlık, gövde, hata kodu) kodda görünüyor; REST'i açıklamak kolay. Üstel geri çekilme: sunucu yoğunken (429/5xx) hemen tekrar denemek yükü artırır; bekleme süresini katlayarak geçici hataya zaman tanınıyor. Kalıcı hatalar (401/404) boşuna yeniden denenmiyor.

### Kayıt 2
- **Araç:** Claude Code
- **İstem (özet):** Claude ücretli olduğu için ücretsiz katmanı olan Groq desteği ekle; hangisinin kullanılacağı `.env`'den seçilsin.
- **Aldığım çıktı (özet):** Ortak taban sınıf (`_HTTPLLMClient`) + `GroqClient` (OpenAI uyumlu istek/yanıt), `LLM_PROVIDER` ayarı ve `get_llm_client()`, `test_h09_groq.py`.
- **Kendi yaptığım değişiklik / doğrulama:** Groq'u ücretsiz olduğu için ben seçtim. Kendi anahtarımla yapılan ilk gerçek çağrı (2026-10-03) **404** verdi: yapay zekânın varsayılan olarak seçtiği `llama-3.3-70b-versatile` modeli Groq'tan kaldırılmıştı (belge sayfası eskiydi). Hesaba açık modeller API'den (`GET /models`) listelendi ve varsayılan `openai/gpt-oss-120b` yapıldı. Bu modeller "düşünen" modeller olduğu için `GROQ_REASONING_EFFORT` ayarı ve `<think>` temizliği eklendi. Ders: yapay zekânın önerdiği model adı gerçek API'de denenmeden doğru sayılmamalı. İlk anahtar sohbete yapıştırıldığı için iptal edildi (ifşa olmuştu); yeni anahtarı `.env`'e kendim yazdım. Yeni anahtarla gerçek çağrılar başarılı (2026-10-03): istemci 0,5–2,6 sn'de Türkçe yanıt verdi; web arayüzünde sohbet uçtan uca çalıştı (kaynaklı yanıt + belgede olmayan soruya "bilgi bulamadım").
- **Neden bu çözümü kullandım:** Ortak taban sınıf: yeniden deneme, zaman aşımı ve hata yönetimi iki sağlayıcıda aynı; iki kez yazılsaydı birinde düzeltilen hata diğerinde kalırdı. Ayar dosyasından seçim (`LLM_PROVIDER`): kodu değiştirmeden ücretli/ücretsiz sağlayıcı arasında geçiş yapılabiliyor.

## Adım 8 — RAG: kaynaklı yanıt (Hafta 10)

> Bu hafta yapay zekâ projede **çekirdek işlev** olarak kullanılıyor; ayrıca kodu yazarken de yardım aldım. İkisini ayrı yaz.

### Kayıt 1 (kodu yazarken)
- **Araç:** Claude
- **İstem (özet):** Belge parçalarına dayanarak kaynaklı yanıt üreten RAG hattı; halüsinasyon önleme; yanıt doğrulama; istem tasarımı; prompt injection savunması.
- **Aldığım çıktı (özet):** `prompts.py`, `rag.py`, `/ask` ucu, sahte-LLM testleri.
- **Kendi yaptığım değişiklik / doğrulama:** Doğrulama (kendi bilgisayarımda — Windows 11, Python 3.12 — Claude Code ile birlikte çalıştırıldı): `pytest hafta-10` → 23 test geçti. `MIN_SCORE` gerçek modelle ölçüldü (`istem-deneyleri.md`, alttaki tablo): belgede olan sorular ≥ 0,430, olmayanlar ≤ 0,270; eşik 0,30 olarak kaldı. Ders planındaki "öğrencinin kendi geliştireceği bölümler" görevlerini bu adımda ayrıca yapmadım (durum: `docs/raporlar/teslim-kontrol-listesi.md`).
- **Neden bu çözümü kullandım:** Tek bir önlem yetmiyor: (1) ilgili parça yoksa model hiç çağrılmıyor (uydurma riski ve maliyet sıfır), (2) istem modele yalnızca kaynaklardan yanıt vermesini ve `[n]` ile alıntı yapmasını söylüyor, (3) model kurala uymasa bile `verify_answer` alıntıları denetliyor; geçersiz numaralar siliniyor, alıntısız yanıt "doğrulanmamış" işaretleniyor.

### Kayıt 2 (uygulamanın çalışma zamanındaki AI kullanımı)
- **Model:** `.env` → `LLM_PROVIDER`: `groq` iken `GROQ_MODEL` (varsayılan `openai/gpt-oss-120b`), `claude` iken `CLAUDE_MODEL` (`claude-haiku-4-5-20251001`)
- **İstem sürümü:** `rag-v1` (`app/services/prompts.py`)
- **Kullanım amacı:** Bulunan belge parçalarından kaynaklı Türkçe yanıt üretmek
- **Çıktı doğrulama:** `rag.verify_answer` (alıntı numaraları, `BILGI_YOK`, alıntısız yanıt)
- **Örnek istem/çıktı:** Soru: "Bir öğrenci kaç kitap ödünç alabilir ve süresi ne kadar?" → Yanıt: "Bir öğrenci aynı anda en fazla 5 kitap ödünç alabilir; ödünç süresi 15 gündür[1]." → `answered`, `grounded=true`, kaynak [1] `kutuphane-yonetmeligi.txt` (Groq `openai/gpt-oss-120b`, 2026-10-03). Tümü: `istem-deneyleri.md`.

## Adım 9 — Sohbet geçmişi ve bağlam (Hafta 11)

> "Kendi" alanlarını teslimden önce doldur. Özetleme ve yeniden yazma akışını çizerek anlatabilmelisin.

### Kayıt 1 (kodu yazarken)
- **Araç:** Claude
- **İstem (özet):** Kalıcı sohbet geçmişi, bağlam penceresi, uzun geçmişi özetleme, takip sorusunu yeniden yazma, sahiplik/gizlilik kuralları, sohbet arayüzü.
- **Aldığım çıktı (özet):** Migration 002/003, `conversations.py`, `chat.py`, API uçları, `chat.js`, sahte-LLM testleri.
- **Kendi yaptığım değişiklik / doğrulama:** Doğrulama (kendi bilgisayarımda — Windows 11, Python 3.12 — Claude Code ile birlikte çalıştırıldı): `pytest hafta-11` → 19 test geçti (özetleme, yeniden yazma ve hata durumları sahte LLM ile). Sohbet arayüzü tarayıcıda açıldı: sohbet oluşturma/listeleme çalıştı, konsol temiz. Ders planındaki "öğrencinin kendi geliştireceği bölümler" görevlerini bu adımda ayrıca yapmadım (durum: `docs/raporlar/teslim-kontrol-listesi.md`).
- **Neden bu çözümü kullandım:** Kayan özet: tüm geçmişi her seferinde göndermek hem token sınırını aşar hem maliyeti artırır; eski mesajlar özetlenip son birkaç mesaj birebir tutuluyor. Yeniden yazma: "peki ya ikincisi?" gibi takip soruları tek başına aranırsa yanlış parça bulunur; soru önce tek başına anlaşılır hâle getiriliyor.

### Kayıt 2 (uygulamanın çalışma zamanındaki AI kullanımı)
- **Model:** `.env` → `LLM_PROVIDER` (`groq`: `GROQ_MODEL`, `claude`: `CLAUDE_MODEL`)
- **Amaç 1:** Uzun konuşma özeti (`chat.SUMMARY_SYSTEM`) · **Amaç 2:** Takip sorusunu yeniden yazma (`chat.REWRITE_SYSTEM`) · **Amaç 3:** Kaynaklı yanıt (`prompts.SYSTEM_PROMPT`)
- **Çıktı doğrulama:** Özet 1500 karakterle sınırlı ve "kaynak değildir" notuyla verilir; yeniden yazma boş/uzunsa özgün soru kullanılır; yanıt `rag.verify_answer` ile doğrulanır.
- **Örnek istem/çıktı:** Web arayüzünde gerçek sohbet (Groq `openai/gpt-oss-120b`, 2026-10-03): "Benzerlik araması nasıl yapılıyor ve vektörler kaç boyutlu?" → "Benzerlik araması kosinüs benzerliğiyle yapılır[1][2][3][4]. Üretilen vektörler 384 boyutludur[1][2][3][4]." (kaynaklar açılır kutularda); aynı sohbette "Türkiye'nin başkenti neresidir?" → "Yüklediğiniz belgelerde bu soruya dair yeterli bilgi bulamadım." Uzun konuşma özeti ve takip sorusu yeniden yazma henüz gerçek modelle gözlenmedi.

## Adım 10 — Kullanım raporu ve yönetim (Hafta 12)

> "Kendi" alanlarını teslimden önce doldur. Rapordaki her sayının nasıl hesaplandığını anlatabilmelisin.

### Kayıt 1 (kodu yazarken)
- **Araç:** Claude
- **İstem (özet):** Sorgu/kaynak kullanım raporu: toplulaştırma sorguları, kaynak istatistiği, günlük seri, CSV dışa aktarma, yönetici paneli; yanıltıcı görsel ve eksik veri risklerinin ele alınması.
- **Aldığım çıktı (özet):** `reports.py`, `admin.py`, rapor/yönetim API uçları, `report.js`, `admin.js`, elle hesaplanmış beklentilerle testler.
- **Kendi yaptığım değişiklik / doğrulama:** Doğrulama (kendi bilgisayarımda — Windows 11, Python 3.12 — Claude Code ile birlikte çalıştırıldı): `pytest hafta-12` → 16 test geçti (beklenen sayılar elle hesaplandı). Gerçek sunucuda rapor, CSV indirme (UTF-8 BOM) ve yönetim sekmesi çalıştı; normal kullanıcının `scope=all` isteği 403 aldı. Ders planındaki "öğrencinin kendi geliştireceği bölümler" görevlerini bu adımda ayrıca yapmadım (durum: `docs/raporlar/teslim-kontrol-listesi.md`).
- **Neden bu çözümü kullandım:** Metrikler sistemin dört sorusuna yanıt veriyor: ne kadar kullanılıyor (soru sayısı), ne kadar güvenilir (kaynağa dayalı oran), nerede bilgi eksik (yanıtsız oran), hangi belge işe yarıyor (kaynak sıralaması). None/0 ayrımı: hiç soru yokken oranı "%0" göstermek "hepsi başarısız" gibi yanıltır; veri yoksa "—" gösteriliyor.

## Adım 11 — Test ve hata ayıklama (Hafta 13)

> "Kendi" alanlarını teslimden önce doldur. Her düzeltmenin nedenini kendi cümlelerinle anlatabilmelisin.

### Kayıt 1 (sınır testleri ve düzeltmeler)
- **Araç:** Claude
- **İstem (özet):** Sistemin sınır durumlarını ve hata senaryolarını test et (boş/büyük/bozuk dosya, uzun girdi, kötü niyetli girdi, eşzamanlılık, hatalı migration); bulunan hataları düzelt.
- **Aldığım çıktı (özet):** `test_h13_sinir_durumlari.py` (18 test) ve 6 hata düzeltmesi: dosya adı uzantısı, `verify_password(None)`, sayaç sınırı, üretimde zayıf `SECRET_KEY`, DOCX zip bombası, arama sorgusu uzunluğu.
- **Kendi yaptığım değişiklik / doğrulama:** Doğrulama (kendi bilgisayarımda — Windows 11, Python 3.12 — Claude Code ile birlikte çalıştırıldı): `pytest hafta-13` → 18 test geçti (2026-10-03). Her düzeltmenin belirti → neden → düzeltme → doğrulama adımları `DUZELTILEN_HATALAR.md`'de.
- **Neden bu çözümü kullandım:** Hatalar "mutlu yol" testlerinde görünmüyordu; sınır değerler (boş, çok uzun, bozuk, kötü niyetli girdi) bilerek denendi. Her hata önce onu yakalayan bir testle gösterildi, sonra düzeltildi; test kalıcı olduğu için hata geri gelirse hemen fark edilir.

### Kayıt 2 (gerçek ortamda doğrulama)
- **Araç:** Claude Code
- **İstem (özet):** Daha önce yalnızca sahte FastAPI ile koşan testleri gerçek FastAPI / pytest ile çalıştır; uygulamayı gerçek sunucuda ve tarayıcıda dene; gerçek kapsamı ölç; depoda gizli dosya olmadığını doğrula.
- **Aldığım çıktı (özet):** 176 test geçti / 1 atlandı, kapsam %94. Bir test gerçek Starlette'te kırıldı (`Response.content` → `.body`, düzeltildi). Testlere uzun sahte anahtar verildi. 39 HTTP isteğiyle tüm akış denendi; arayüzde konsol hatası yok. `MIN_SCORE` gerçek modelle ölçüldü. `TEST_RAPORU.md` ve `DUZELTILEN_HATALAR.md` yazıldı.
- **Kendi yaptığım değişiklik / doğrulama:** Evet, kendi bilgisayarımda çalıştırıldı. 2026-10-03'te hafta 13 durumunda: 191 test → 190 geçti, 1 atlandı; kapsam %95. Sayı 2026-10-02'deki 177'den farklı çünkü Hafta 9'a Groq desteği ve testleri (+13), Hafta 10'a gerçek modelle bulunan alıntı biçimi hatasının testi (+1) eklendi; `TEST_RAPORU.md` güncellendi.
- **Neden bu çözümü kullandım:** Önceki ortamda testler sahte (stub) FastAPI ile koşuyordu; gerçek çerçevede farklı davranabilirdi (nitekim bir test kırıldı). "Çalışıyor" demeden önce gerçek paketlerle, gerçek sunucuda ve tarayıcıda denemek gerekiyordu.

### Kayıt 3 (kendi bulduğum hata: Hugging Face 402 → Gemini — 2026-10-07)
- **Araç:** Claude Code
- **İstem (özet):** Canlı sitede bir PDF yüklenince "Gömme üretilemedi: Hugging Face embedding hatası (402)" hatası alınıyor; nedenini bul ve düzelt.
- **Aldığım çıktı (özet):** 402'nin kod hatası değil, Hugging Face'in ücretsiz aylık kredisinin bitmesi olduğu açıklandı; seçenekler sunuldu. Seçimim üzerine `GeminiEmbedder` (Google `gemini-embedding-001`, 768 boyut) yazıldı, `MIN_SCORE` gerçek ölçümle 0,55 seçildi, ölçüm sırasında görülen nedensiz 403 yanıtları geçici sayıldı ve ücretsiz katmanın dakikalık sınırı için gönderim hızı sınırlandı (0.21.0 ve 0.21.1).
- **Kendi yaptığım değişiklik / doğrulama:** Hatayı canlı sitede belge yüklerken ben buldum ve bildirdim. Ücretli plana geçmek yerine Google Gemini'yi ben seçtim; anahtarı Google AI Studio'dan kendim aldım, yerel `.env` dosyasına ve Vercel'e girdim. Yayından sonra canlıda hâlâ Hugging Face kullanıldığı görüldü: Vercel'de `EMBEDDING_BACKEND` değeri 3 Ekim'den beri `hf` kalmıştı. Bu değeri `gemini` olarak düzelttim, `MAX_CHUNKS_PER_DOCUMENT` değerini 20000 yaptım ve yeniden yayınladım. Doğrulama: aynı PDF (185 parça) canlıda indekslendi ve arama 200 döndü. Belirti → neden → düzeltme → doğrulama adımları `docs/duzeltilen-hatalar.md` → Hata 9'da.
- **Neden bu çözümü kullandım:** Ücretli bir plana geçmeden canlı sitenin çalışmaya devam etmesi için. Embedding katmanı değiştirilebilir tasarlandığı için değişiklik tek bir sınıfta kaldı; uç noktalar ve RAG kodu değişmedi.

## Adım 12 — Dokümantasyon, arayüz, dağıtım (Hafta 14)

> "Kendi" alanlarını sen doldur. Claude'un yaptığı doğrulamalar "Aldığım çıktı" alanında; senin denemen ayrı yazılmalı.

### Kayıt 1 (büyük dosya, arayüz, şifremi unuttum — 2026-10-03)
- **Araç:** Claude Code
- **İstem (özet):** 500 MB'a kadar yükleme; modern siyah tema ve ana sayfa; e-postayla şifre sıfırlama; dosya seçilene kadar pasif "Yükle" düğmesi ve gerçek ilerleme yüzdesi.
- **Aldığım çıktı (özet):** Akışlı yükleme (1 MB bloklar, gövde okunmadan 413), `/documents/limits`; yeni tema, `fx.js`, ana sayfa ve giriş penceresi; `password_resets` tablosu, 6 haneli tek kullanımlık kod (HMAC özeti, 15 dk, 5 deneme), SMTP gönderimi; testler. Claude'un doğrulaması: 450 MB DOCX gerçek HTTP ile 20 sn; 520 MB → 413, 0 bayt gönderildi; tarayıcıda 1440/375 px, koyu/açık tema, konsol temiz.
- **Kendi yaptığım değişiklik / doğrulama:** Bu işteki kararlar benimdir: sıfırlama kodunun e-postayla gönderilmesi (SMTP yoksa geliştirme ortamında konsola yazılması), "en fazla 500 MB" yazısının kalması ve hepsinin Hafta 14 kapsamına alınması. Büyük dosya yüklemeyi ve şifre sıfırlamayı ayrıca kendim denemedim; doğrulama yukarıdaki Claude Code denemeleridir. Buluta geçişle (Kayıt 2) dosya sınırı 50 MB oldu.
- **Neden bu çözümü kullandım:** _(kendi cümlelerinle)_

### Kayıt 2 (iki depo + Supabase + Vercel — 2026-10-03)
- **Araç:** Claude Code
- **İstem (özet):** Frontend ve backend ayrı depolara; GitHub'a gitmemesi gerekenleri (özellikle `.env`) ayır; veritabanı Supabase, frontend ve backend Vercel; haftalık belgeleri tek yerde birleştir; eksikleri tamamla, rapor ver. Kararlar (geliştiricinin): embedding Hugging Face'te aynı model, yükleme 50 MB Supabase Storage üzerinden, hafta düzeni yerine iki klasör + tek `docs/`.
- **Aldığım çıktı (özet):** `P55-RAG-Assistant-backend` / `P55-RAG-Assistant-frontend`; iki lehçeli veritabanı katmanı (`PgConnection`), PostgreSQL migration'ı (RLS), pgvector araması, `HFEmbedder`, `storage.py` + imzalı yükleme akışı, CORS, Vercel ayarları, `supabase_kurulum.py`, `hf_dene.py`; belgeler (`teknik-dokumantasyon.md`, `dagitim.md`, `yol-haritasi.md`, `CHANGELOG.md`). Claude'un doğrulaması: tüm testler SQLite'ta ve yerel PostgreSQL 16 + pgvector'de geçti; Postgres testleri gerçek bir hata buldu (NUL karakteri → 500, düzeltildi); tarayıcıda ayrı adreslerde (5500 → 8000, PostgreSQL) kayıt/giriş/yükleme/arama/rapor çalıştı; sunucu paketi torch'suz ≈ 120 MB. **Gerçek Supabase/HF/Vercel hesaplarıyla denenmedi.**
- **Kendi yaptığım değişiklik / doğrulama:** Bulut mimarisini ben seçtim: frontend ve backend için iki ayrı GitHub deposu, veritabanı ve dosya deposu olarak Supabase, barındırma için Vercel. Supabase, Hugging Face ve Vercel hesaplarını açtım. Supabase projesi `eu-central-1` bölgesinde kuruldu ve tablolar oluşturuldu; yönetici hesabını `create_admin` betiğiyle kendim açtım. Vercel ortam değişkenlerini Claude Code'un hazırladığı listeden kendim girdim. Doğrulama: canlı `/health` → `database: postgres`, CORS doğru, giriş çalışıyor. (Hugging Face daha sonra Gemini ile değiştirildi, bkz. Adım 11 Kayıt 3.)
- **Neden bu çözümü kullandım:** _(kendi cümlelerinle: neden iki depo, neden Supabase, neden HF)_

### Kayıt 3 (ayrı kayıt ekranı, ad soyad, e-posta doğrulama — 2026-10-03)
- **Araç:** Claude Code
- **İstem (özet):** Vercel kuruldu ama Supabase'de tablolar görünmüyor, diyagram lazım. Uygulamanın eksikleri: şifremi unuttum, girilen e-postanın doğruluğu, kayıt ve giriş ekranı ayrı olmalı, kullanıcıdan ad alınmalı.
- **Aldığım çıktı (özet):** Migration `005` / Postgres `002`: `users.full_name`, `users.email_verified_at` (eski hesaplar doğrulanmış sayılır), `password_resets` → `email_codes` (`purpose`: verify/reset). `services/email_codes.py` (ortak kod mantığı), `email_verification.py`, `auth.sign_up`; uçlar `/auth/verify-email`, `/auth/resend-verification`, girişte 403; `/health`'e `database` alanı. Arayüz: giriş / kayıt / doğrulama ayrı paneller, parola tekrarı, üst barda ad. ER diyagramı ve "Supabase'de tablolar neden görünmez" kontrol listesi. Claude'un doğrulaması: SQLite 265 / PostgreSQL 266 test geçti; Supabase'deki duruma benzer yükseltme (001 kurulu + kullanıcı var → 002) denendi; tarayıcıda kayıt → yanlış kod → doğru kod → otomatik giriş, doğrulanmamış girişin engellenmesi, şifre sıfırlama, 375 px. **Gerçek SMTP ile e-posta gönderimi ve Vercel/Supabase üzerinde deneme yapılmadı** (kod geliştirme modunda sunucu konsoluna yazıldı).
- **Kendi yaptığım değişiklik / doğrulama:** Kayıt ve giriş ekranlarının ayrılmasını, adın alınmasını ve e-posta doğrulamasını ben istedim. SMTP ayarlarını Vercel'e ben girdim. Canlıda denendiğinde gerçek doğrulama e-postası bana ulaştı; "şifremi unuttum" ucu canlıda başarılı yanıt verdi.
- **Neden bu çözümü kullandım:** _(kendi cümlelerinle: neden e-posta doğrulaması, neden tek kod tablosu)_

### Kayıt 4 (sinematik sahne, animasyon düğmesi, Hesabım, belge/sohbet kullanılabilirliği — 2026-10-03)
- **Araç:** Claude Code
- **İstem (özet):** "Kütüphane ve skill ekle" + sinematik sahne tarifi (antika saat mekanizmasının içinden sürekli ilerleyen kamera, pirinç dişliler, ortadaki dişlinin yıldız tozuna dağılıp mor-amber nebulaya dönüşmesi, hacimsel ışık, film greni, hareket bulanıklığı). Ayrıca: profil/hesap ayarları, güncel olmayan ana sayfa metinleri, sohbet/belge kullanılabilirliği.
- **Aldığım çıktı (özet):** Hazır bir animasyon skill'i bulunamadı (katalogda sonuç yok). `cinema.js` (Three.js 0.186.1, yerel alt küme `vendor/three.min.js`, ~150 KB sıkıştırılmış): yordamsal dişli geometrisi, birbirine geçen dişli takımları, shader ile eriyen metal, GPU'da hesaplanan 16 000 parçacık, ışıma + hareket izi + film greni; WebGL yoksa 2B heykel yedek. Hata ayıklarken bulunan gerçek neden: bilgisayarda Windows "Animasyon efektleri" kapalı → tarayıcı `prefers-reduced-motion: reduce` bildiriyor → sitedeki animasyonların çoğu hiç oynamıyordu; üst bara "Animasyonlar" düğmesi eklendi. Hesabım (ad, parola, hesap silme), sohbet yeniden adlandırma, belge süzme/sıralama. Claude'un doğrulaması: SQLite 273 / PostgreSQL 274 test, frontend 22; tarayıcıda 1440 px / 375 px, koyu/açık tema, döngünün 9 anı ekran görüntüsüyle incelenip ışık ayarları düzeltildi (beyaz patlama, yakut küre hatası).
- **Kendi yaptığım değişiklik / doğrulama:** Animasyonların benim bilgisayarımda görünmediğini bildirdim; nedeni Windows'ta "Animasyon efektleri" ayarının kapalı olması çıktı ve üst bara "Animasyonlar" düğmesi eklendi. Bir sonraki adımda (Kayıt 5) bu sinematik sahnenin tamamen kaldırılmasına ben karar verdim.
- **Neden bu çözümü kullandım:** _(kendi cümlelerinle: neden Three.js, neden CDN değil yerel kopya)_

### Kayıt 5 (sohbet kalitesi + sade tema — 2026-10-03)
- **Araç:** Claude Code
- **İstem (özet):** "Animasyonlar kalksın, animasyon eklemeden önceki temaya dönüyoruz. Chatbot hiç olmuyor, değiştirmek zorundayız. Modern, dark ve aydınlık geçişi olan bir tema yap, sana bırakıyorum."
- **Aldığım çıktı (özet):** Sohbetin neden kötü olduğu ölçüldü (yerelde Vercel'deki zincirin aynısı: HF + Groq, sentetik 7 bölümlük yönerge, 12 + 6 soru). Kök neden model değil arama: HF MiniLM'i 128 token'da kesiyor, Türkçe parçanın ikinci yarısı aranamıyordu. 5 embedding modeli karşılaştırıldı → `BAAI/bge-m3`; istem `rag-v2`, `reasoning_effort=medium`. Sonuç: belgede olan 12 sorunun 9'u → 11'i doğru (+1 kısmi). Groq'ta daha güçlü model yok (hesaptaki liste kontrol edildi). Tema: animasyon dosyaları silindi; ilk sade tema (indigo, yuvarlak köşe) kullanıcı tarafından reddedildi ("modern keskin siyah beyaz istedim") → keskin siyah-beyaz tema (açık/koyu, sistem ayarı). Claude'un doğrulaması: backend 278 test, frontend 21 test; tarayıcıda 1440 / 375 px, açık/koyu, tüm sekmeler, yatay taşma yok, sayfada çalışan animasyon 0. Tarayıcıda bulunan gerçek hata: `hidden` düğmeler görünür kalıyordu → düzeltildi + test. **Canlıda (Vercel) henüz denenmedi**; kalan zayıflıklar `docs/istem-deneyleri.md`'de.
- **Kendi yaptığım değişiklik / doğrulama:** Canlı sitede sohbetin belgede yazan sorulara "bilgi bulamadım" dediğini ben fark edip bildirdim. Düzeltme yayına alındıktan sonra Vercel'de `GROQ_REASONING_EFFORT` değerini `medium` yaptım, canlıdaki belgelerimi "Yeniden indeksle" ile yeni modele göre indeksledim ve sohbetin çalıştığını gördüm. Tema için önerilen indigo ve yuvarlak köşeli tasarımı reddedip keskin siyah-beyaz temayı ben istedim.
- **Neden bu çözümü kullandım:** _(kendi cümlelerinle: neden model değil arama düzeltildi, neden bge-m3, neden animasyonlar kaldırıldı)_

### Kayıt 6 (büyük belge + genel sohbet — 2026-10-03)
- **Araç:** Claude Code
- **İstem (özet):** "Bu yükleme olayını daha büyük dosyalar için yapamaz mıyız ve bizimle basit şekilde bir model konuşabilir mi chatbottan." Seçimlerim: parça sınırını kaldır (50 MB Supabase sınırı kalsın); selamlaşma + genel bilgi, etiketli.
- **Aldığım çıktı (özet):** `indexing.index_next` (süre bütçeli, kaldığı yerden), `chunks.list_unindexed_chunks`, `POST /documents/{id}/index-next`, arayüzde ilerleme döngüsü ve "Devam et"; `chat.general_answer` + `GENERAL_SYSTEM_PROMPT`, durum `general`, arayüz etiketi, rapor. Claude'un doğrulaması: SQLite 294 / PostgreSQL+pgvector 295 test geçti; tarayıcıda 2989 parçalık belge 31 istekte indekslendi (%4 → %98 → hazır); gerçek Groq ile "merhaba / ne yapabilirsin / teşekkürler / başkent / okulun yemekhane ücreti / belgedeki soru" denendi (`istem-deneyleri.md`). Testte bulunan gerçek sorun: Windows saati ~15 ms adımlı → süre bütçesi testleri zamana bağlıydı; sahte saat eklendi. **Canlıda henüz denenmedi.**
- **Kendi yaptığım değişiklik / doğrulama:** Parça sınırının kaldırılmasını (Supabase'in 50 MB dosya sınırı kalarak) ve genel sohbet yanıtlarının "genel bilgi" etiketiyle gösterilmesini ben seçtim. Yayından sonra Vercel'de `MAX_CHUNKS_PER_DOCUMENT` değerini 20000 yaptım.
- **Neden bu çözümü kullandım:** _(kendi cümlelerinle: neden indeksleme parçalara bölündü, genel yanıt neden etiketli)_

### Kayıt 7 (kişisel API anahtarı — 2026-10-04)
- **Araç:** Claude Code
- **İstem (özet):** "Kullanıcıların token'ı, özel kimlik numarası gibi web token'ı tutulacak, 3. parti bir API kullanılacak." Claude üç anlamı sordu (kişisel API anahtarı / girişi 3. parti servise vermek / kullanıcının kendi Groq anahtarı); seçimim: **kişisel API anahtarı**.
- **Aldığım çıktı (özet):** `api_tokens` tablosu (SQLite `006`, PostgreSQL `003`), `db/api_tokens.py`, `services/api_tokens.py` (`p55_` + `secrets`, SHA-256 özet, 7/30/90/365 gün, kullanıcı başına 10, "son kullanım" dakikada bir yazılır), `deps.get_current_user` iki tür anahtarı ayırır, `require_session` (anahtarla hesap yönetimi/yönetim 403), `GET/POST/DELETE /auth/tokens`; arayüzde Hesabım → "API anahtarları" (bir kez gösterim + Kopyala, liste, Sil). Claude'un doğrulaması: yeni 14 backend testi + 1 arayüz testi; SQLite 313 / PostgreSQL 314 test geçti; gerçek HTTP ile Python betiği "3. parti uygulama" gibi bağlandı, silinen anahtar 401 aldı; tarayıcıda üret/kopyala/sil, sekme değişince anahtar ekrandan silindi, 375 px'te taşma yok. **Canlıda (Vercel/Supabase) henüz denenmedi.**
- **Kendi yaptığım değişiklik / doğrulama:** Claude Code'un sorduğu üç anlam arasından kişisel API anahtarını ben seçtim. Anahtarı Postman ya da kendi betiğimle ayrıca denemedim; doğrulama yukarıdaki testler ve Claude Code'un gerçek HTTP denemesidir.
- **Neden bu çözümü kullandım:** _(kendi cümlelerinle: neden JWT yetmedi, neden anahtarın özeti saklanıyor, neden anahtarla parola değiştirilemiyor)_

### Kayıt 8 (ders formları ve raporlar — 2026-10-04)
- **Araç:** Claude Code
- **İstem (özet):** "O rapor şablonlarına da bak; haftalık olarak güncellenecek olanları GitHub deponuza ekle, haftalık olarak güncellersin. İlk haftalar teslim etmen gereken varsa da koyarsın."
- **Aldığım çıktı (özet):** Ders paketinin Bölüm 4'ündeki 10 form okundu. `docs/raporlar/`: proje öneri formu (2. hafta çıktısı), risk analizi, proje takvimi, proje izleme formu, GitHub kontrol listesi, haftalık rapor şablonu (ilerleme raporu + kontrol listesi + öz değerlendirme); AI günlüğünün başına Form 8 tablosu; Form 10 için mevcut belgelerle eşleme. Olgusal alanlar dolduruldu; öz değerlendirme, risk puanları, "neden seçtim", "açıklar mı?" gibi alanlar 💬 ile işaretlenip boş bırakıldı. Danışman kontrol formu öğretim elemanına ait olduğu için depoya konmadı.
- **Kendi yaptığım değişiklik / doğrulama:** Formlarda kullanılan öğrenci numaramı (211161024) ben verdim. 💬 işaretli öz değerlendirme alanlarını ve risk puanlarını henüz doldurmadım.
- **Neden bu çözümü kullandım:** _(kendi cümlelerinle)_

### Kayıt 9 (API anahtarı bildirimi ve yönetici denetimi — 2026-10-04)
- **Araç:** Claude Code
- **İstem (özet):** İlk istek: "API anahtarını kullanıcı oluşturmasın, biz oluşturup ekleyelim, kullanıcı haberdar olmasın." Claude bunun kullanıcının haberi olmadan hesabına erişim (arka kapı) anlamına geldiğini, KVKK'ya ve güvenlik notuna aykırı olduğunu söyleyip yapmadı. Asıl amaç netleşti: "Kullanıcının hesabına başkası girmesin, yalnızca anahtarı oluşturan girsin." Claude mevcut tasarımın bunu zaten sağladığını kodla ve testlerle gösterdi. Ardından istek: "E-posta bildirimi ekle; yönetici anahtarı versin ya da görsün." Yönetici anahtar verseydi hesaba ikinci bir kişi girebilirdi, bu yüzden "görsün" seçeneği uygulandı.
- **Aldığım çıktı (özet):** Anahtar oluşturulunca sahibine bildirim e-postası (`mailer.send_token_created`; yalnızca ad, ilk 12 karakter, tarihler, anahtarın kendisi yok: `api_tokens.public_info`). Yönetici `GET /admin/tokens` (tüm anahtarlar sahibiyle; anahtar/özet dönmez) ve `DELETE /admin/tokens/{id}` (iptal + sahibine e-posta); yönetici anahtar **üretemez**. `_deliver` ortak `deps.deliver_email`'e taşındı. Arayüz: Yönetim sekmesinde "API anahtarları" tablosu. Claude'un doğrulaması: 5 yeni backend testi + 1 arayüz testi, backend 319 / frontend 26 test geçti; tarayıcıda (yerel, sentetik hesaplar) liste ve iptal çalıştı, iki bildirim de geliştirme konsoluna yazıldı (SMTP yok); push sonrası canlıda `/admin/tokens` → 401 (uç yayında, korumalı). **Gerçek e-posta gönderimi ve canlıda yönetici ekranı denenmedi.** PostgreSQL'de testler koşulmadı.
- **Kendi yaptığım değişiklik / doğrulama:** İlk isteğim, yöneticinin kullanıcıya haber vermeden anahtar üretmesiydi. Claude Code bunun bir arka kapı olacağını ve KVKK'ya aykırı olduğunu açıkladı; ben de asıl amacımın "hesaba yalnızca anahtarı oluşturan girsin" olduğunu netleştirdim. Yöneticinin anahtarları yalnızca görüp iptal edebilmesi seçeneğini ben seçtim. Bildirim e-postasını canlıda ayrıca denemedim.
- **Neden bu çözümü kullandım:** _(kendi cümlelerinle: neden yönetici anahtarı göremiyor/üretemiyor, neden e-postada anahtarın kendisi yok)_

### Kayıt 10 (`.env.example` ve `baslat.bat` — 2026-10-04)
- **Araç:** Claude Code
- **İstem (özet):** GitHub'da sildiğim dosyalar yerel depoyla birleştirilsin; belgeler buna göre güncellensin.
- **Aldığım çıktı (özet):** `.env` şablonu `scripts/env_olustur.py` içine taşındı (gerçek anahtar yok); README ve kurulum belgeleri komutla kuruluma (`uvicorn` / `http.server`) çevrildi; testler şablonu ve README ayar tablosunu denetliyor.
- **Kendi yaptığım değişiklik / doğrulama:** `baslat.bat` dosyalarını "artık ihtiyacımız kalmadı" diyerek ve `.env.example` dosyasını GitHub'da kendim sildim; sorulduğunda silinmiş kalmasına karar verdim.
- **Neden bu çözümü kullandım:** Kurulum artık README'deki komutlarla yapılıyor; ayrı başlatma dosyasına gerek kalmadı.

### Kayıt 11 (ad değişikliği ve animasyonlu ana sayfa — 2026-10-07)
- **Araç:** Claude Code (+ `ui-ux-pro-max` ve `frontend-design` skill'leri)
- **İstem (özet):** Instagram'da gördüğüm "Claude ile profesyonel web sitesi" örneğindeki gibi animasyonlu bir ana sayfa; arayüzde ürünün adı "P55" yerine "Belge Tabanlı Soru Asistanı" olsun.
- **Aldığım çıktı (özet):** Ad değişikliği (API anahtarı öneki `bsa_`, eski `p55_` anahtarları çalışmaya devam ediyor); GSAP 3.15.0 ile ana sayfa (0.19.0); ardından Three.js ile Keychron tarzı 3B "stüdyo" sahnesi (0.20.0); en son kaydırmalı 5 sahne kaldırılıp tek açılış animasyonu (belgeler tepsiye uçar, tuşlar belirir). Testler güncellendi; tarayıcıda masaüstü / telefon, açık / koyu tema denendi.
- **Kendi yaptığım değişiklik / doğrulama:** Skill'lerin projeye kurulmasını onayladım. Siyah-beyaz temanın kalmasını, GSAP kullanılmasını, önce ana sayfadan başlanmasını ve üç örnek arasından Keychron tarzını ben seçtim. Yeni adı ve depo adları ile ders formlarının P55 olarak kalmasını ben belirledim. Daha sonra kaydırmayla değişen sahnelerin kaldırılıp yalnızca tek bir açılış animasyonu olmasını ben istedim.
- **Neden bu çözümü kullandım:** _(kendi cümlelerinle)_

## Adım 13 — Final (Hafta 15)

### Kayıt 1 (teslim kontrolü — 2026-10-08)
- **Araç:** Claude Code
- **İstem (özet):** "Teslim etmem gerekiyor. Projeme göre teslim edilmesi gerekenler neler, yapıldı mı, GitHub'da hangi dosyada; sözlü sorular ve cevapları; eksik kalan bir şey var mı?"
- **Aldığım çıktı (özet):** Ders paketindeki P55 künyesi (s. 40) ve haftalık plan (s. 475–482) iki depoyla karşılaştırıldı: `docs/raporlar/teslim-kontrol-listesi.md` (gereksinim tablosu, haftalık teslim tablosu, ders kuralları tablosu, 13 × 5 sözlü soru için cevap iskeleti, eksikler). Aynı gün ölçüm: backend 336 test geçti / 2 atlandı, frontend 29 test geçti, canlı `/health` → `postgres`, iki depoda gizli anahtar taraması temiz.
- **Kendi yaptığım değişiklik / doğrulama:** Tabloyu inceledim. Claude Code'un oturum kayıtlarından çıkardığı "benim yaptıklarım" listesini doğru olarak onayladım; bu günlükteki "Kendi yaptığım" alanları o listeye göre yazıldı. "Öğrencinin kendi geliştireceği bölümler" kod görevlerini, proje sırasında karşılaşıp çözdüğüm sorunların tekrarı olarak gördüğüm için ayrıca yapmadım. Kendi hata ayıklama örneği olarak canlıda bulduğum iki hata kaydedildi (Hata 9: Hugging Face 402, Hata 10: CSV / Excel).
- **Neden bu çözümü kullandım:** Teslimden önce eksikleri ve hangi çıktının hangi dosyada olduğunu tek bir yerde görmek için.
