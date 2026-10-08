# Düzeltilen Hatalar

Her hata için: **belirti → neden → nasıl bulundu → düzeltme → doğrulama**. Hataların hepsi sınır durumu testleri (`test_sinir_durumlari.py`) yazılırken ortaya çıktı: önce hatayı gösteren (kırmızı) test yazıldı, sonra kod düzeltildi ve test yeşile döndü.

---

## Hata 1 - Uzun dosya adı kırpılırken uzantı kayboluyordu
- **Belirti:** 150 karakterden uzun adlı geçerli bir `.txt` dosyası "desteklenmeyen tür" diye reddediliyordu.
- **Neden:** `sanitize_filename` adı `base[:150]` ile kesiyordu. 200 karakterlik `aaaa...a.txt` adından geriye `.txt` içermeyen 150 karakter kalıyor, uzantı kontrolü de başarısız oluyordu.
- **Nasıl bulundu:** `test_cok_uzun_dosya_adi_uzantisini_kaybetmez` (200 karakter + `.txt`).
- **Düzeltme** (`app/services/documents.py`): Ad kök ve uzantı olarak ayrılıyor; kök kısaltılıyor, uzantı korunuyor (uzantı en fazla 20 karakter).
  ```python
  stem, ext = os.path.splitext(base)
  ext = ext[:20]
  base = stem[:150 - len(ext)] + ext
  ```
- **Doğrulama:** Ad `.txt` ile bitiyor, uzunluk ≤ 150, belge indeksleniyor.

## Hata 2 - `verify_password(None)` çöküyordu
- **Belirti:** Saklanan hash `None` ya da metin dışı bir değer olduğunda `AttributeError` fırlıyor, giriş isteği 500 ile çöküyordu.
- **Neden:** `stored.split("$")` bir `try` bloğu içindeydi, ama `except` yalnızca `(ValueError, TypeError)` yakalıyordu. Bozuk biçimli **metinler** `ValueError` verdiği için yakalanıyordu. `None` ya da sayı gelince ise `None.split` **`AttributeError`** fırlatıyor; bu tür listede olmadığı için hata yakalanmadan dışarı kaçıyordu.
- **Nasıl bulundu:** `test_verify_password_beklenmedik_girdilerde_cokmez` (`None`, `""`, `"scrypt"`, yanlış alan sayısı, `123`).
- **Düzeltme** (`app/core/security.py`): Başa `if not isinstance(stored, str): return False` eklendi.
- **Doğrulama:** Beş kötü girdinin hepsi `False` döndürüyor, istisna yok.

## Hata 3 - Başarısız giriş sayacı sınırsız büyüyordu (bellek)
- **Belirti:** Her farklı e-posta adresiyle yapılan başarısız giriş, bellekteki `_failed` sözlüğüne yeni bir kayıt ekliyordu. Rastgele e-postalarla binlerce istek atan biri sunucunun belleğini doldurabilirdi.
- **Neden:** Kayıtlar yalnızca **başarılı** girişte siliniyordu. Hiç var olmayan e-postalar için silinme hiç gerçekleşmiyordu.
- **Nasıl bulundu:** `test_basarisiz_giris_sayaci_sinirsiz_buyumez` (sınır 50'ye düşürülüp 200 farklı e-postayla deneniyor).
- **Düzeltme** (`app/services/auth.py`): `MAX_TRACKED_EMAILS = 5000` ve `_purge_failed()` eklendi. Sınır aşılınca önce süresi dolan kayıtlar, yine de fazla varsa **en eski** kayıtlar siliniyor.
- **Doğrulama:** Sözlük 50'yi aşmıyor; en yeni kayıt (`hedef199`) duruyor, en eskisi (`hedef0`) silinmiş.
- **Kalan sınır:** Sayaç hâlâ bellekte; sunucu yeniden başlayınca sıfırlanır (bilinen sınır).

## Hata 4 - Varsayılan / zayıf `SECRET_KEY` üretimde engellenmiyordu
- **Belirti:** `.env` içinde `SECRET_KEY` unutulursa uygulama sessizce `degistir-bunu` anahtarıyla çalışıyordu. Bu anahtar depoda herkese açık olduğundan, herkes geçerli bir **yönetici token'ı üretebilirdi**.
- **Neden:** Anahtarın gücü hiç denetlenmiyordu.
- **Nasıl bulundu:** Güvenlik sınırlarını gözden geçirirken; `test_varsayilan_gizli_anahtar_uretimde_reddedilir`.
- **Düzeltme** (`app/core/config.py`, `app/main.py`, `.env.example`): `APP_ENV` ayarı ve `check_secret_key()` eklendi. Uygulama açılırken (`lifespan`) çağrılıyor:
  - `APP_ENV=production` ve anahtar varsayılan ya da 32 karakterden kısa → `RuntimeError`, **uygulama başlamaz**.
  - Geliştirmede yalnızca uyarı verir (öğrencinin işini engellemez).
- **Doğrulama:** Test dört durumu da sınıyor (üretim + varsayılan, üretim + kısa, üretim + güçlü, geliştirme + varsayılan).

## Hata 5 - DOCX sıkıştırma (zip) bombası kontrolü yoktu
- **Belirti:** Birkaç KB'lık bir DOCX, açıldığında yüzlerce MB'a çıkabilir. Yükleme boyut sınırı (10 MB) sıkıştırılmış boyuta bakıyor, bu yüzden böyle bir dosyayı yakalayamıyordu; sunucu belleği dolabilirdi.
- **Neden:** DOCX aslında bir zip arşividir. Açılmış boyut denetlenmiyordu.
- **Nasıl bulundu:** `test_docx_zip_bombasi_reddedilir` (3 MB sıfır → sıkıştırılınca 100 KB'tan küçük; sınır testte 1 MB).
- **Düzeltme** (`app/services/parser.py`): python-docx'e vermeden önce zip içindeki dosyaların açılmış toplam boyutu (`file_size`) toplanıyor. `MAX_DOCX_UNCOMPRESSED_MB` (varsayılan 50) aşılırsa `ParseError` fırlatılıyor. Ayrıca `except ParseError: raise` eklendi; aksi halde bu anlamlı mesaj genel "DOCX okunamadı" mesajına dönüşüyordu.
- **Doğrulama:** Belge `failed` oluyor, hata mesajında "büyük" geçiyor.

## Hata 6 - `/search` sorgu uzunluğu sınırsızdı
- **Belirti:** `/ask` soruyu 1000 karakterle sınırlıyordu, ama `/search` sınırlamıyordu. Çok uzun bir sorgu embedding modeline gidip gereksiz işlem yüküne yol açıyordu.
- **Neden:** Sınır yalnızca RAG katmanına eklenmişti, arama servisine eklenmemişti.
- **Nasıl bulundu:** `test_asiri_uzun_sorgu_reddedilir` (servis ve API düzeyinde).
- **Düzeltme** (`app/services/vector_search.py`): `len(query) > config.MAX_QUESTION_CHARS` ise `ValueError`; API bunu 400'e çeviriyor.
- **Doğrulama:** Test yeşil; gerçek sunucuda 5000 karakterlik sorgu → `400 "Sorgu en fazla 1000 karakter olabilir"`.

---

## Gerçek ortama geçince bulunan sorunlar
Önceki geliştirme ortamında internet yoktu; testler sahte (stub) FastAPI ile koşuyordu. Gerçek paketler kurulunca:

### 7 - Test, sahte kütüphanenin alan adını kullanıyordu
- **Belirti:** `tests/test_rapor.py::test_csv_ucu_baslik_ve_icerik` → `AttributeError: 'Response' object has no attribute 'content'`.
- **Neden:** Sahte `Response` sınıfında alanın adı `.content`'ti; gerçek Starlette'te `.body`. **Uygulama kodu doğruydu**, hatalı olan testti.
- **Düzeltme:** Test `resp.body` kullanacak şekilde değiştirildi.
- **Ders:** Sahte (stub) kütüphaneyle geçen test, gerçek kütüphaneyle geçeceğini garanti etmez. Testler gerçek bağımlılıklarla da çalıştırılmalı.

### 8 - Testler kısa gizli anahtar yüzünden 24 uyarı veriyordu
- **Belirti:** PyJWT `InsecureKeyLengthWarning` (anahtar 13 bayt, önerilen ≥ 32).
- **Neden:** Testler `.env` olmadan varsayılan `degistir-bunu` anahtarıyla çalışıyordu.
- **Düzeltme:** `tests/__init__.py` testlere 32 karakterden uzun, açıkça sahte bir anahtar veriyor. Böylece testler `.env`'deki gerçek anahtardan da bağımsız.

---

### Gerçek LLM ile bulunan - Model alıntıyı `【1】` biçiminde yazıyordu
- **Belirti** (2026-10-03, Groq `gpt-oss-120b`, tarayıcıda gerçek sohbet): doğru ve kaynaklı yanıt "Bu yanıt kaynaklarla doğrulanamadı" uyarısıyla gösterildi.
- **Neden:** `rag.verify_answer` yalnızca `[1]` biçimini arıyordu; model `【1】` (tam genişlikli köşeli parantez) yazıyordu.
- **Düzeltme** (`app/services/rag.py`, Hafta 10 kodu): `【n】`, `［n］`, `【n†…】` doğrulamadan önce `[n]`'e çevriliyor.
- **Doğrulama:** `test_rag.py::test_tam_genislikli_alinti_parantezleri_taninir` önce kırmızı, sonra yeşil; tarayıcıda aynı soru tekrar soruldu, yanıt kaynaklı ve uyarısız gösterildi.

### PostgreSQL testleriyle bulunan - İkili/bozuk metin dosyası bulutta 500 hatası veriyordu
- **Belirti** (2026-10-03, testler yerel PostgreSQL 16'ya karşı ilk kez koşulunca): `test_ikili_cop_veri_txt_olarak_cokmez` SQLite'ta geçiyor, PostgreSQL'de `psycopg.DataError: PostgreSQL text fields cannot contain NUL (0x00) bytes` ile düşüyordu. Bulutta (Supabase) bu, kullanıcıya 500 hatası demekti.
- **Neden:** SQLite metin sütununa NUL karakterini (`\x00`) kabul ediyor, PostgreSQL etmiyor. İkili veri `.txt` olarak yüklenince çözülen metinde NUL kalıyordu.
- **Nasıl bulundu:** Aynı test takımının iki veritabanında da koşabilmesi sağlandı (`TEST_PG_URL`); yalnızca bu test ve SQLite'a özgü bir şema testi farklı davrandı.
- **Düzeltme** (`app/services/parser.py`): `parse_file` her biçimden çıkan metindeki NUL karakterlerini atıyor (metin için anlamsızdırlar).
- **Doğrulama:** Test PostgreSQL'de kırmızıdan yeşile döndü; SQLite'ta yeşil kaldı. Tüm takım iki veritabanında da geçiyor.

---

## Canlı sitede geliştirici tarafından bulunan hatalar
Bu iki hatayı Samet DOĞANGÜN canlı siteyi kullanırken buldu ve bildirdi; düzeltme Claude Code ile birlikte yapıldı.

## Hata 9 - Canlıda belge yüklenince "Hugging Face embedding hatası (402)"
- **Belirti** (2026-10-07, canlı site): "1_2_Mikro Bölüm 1.pdf" yüklenince belge indekslenmedi, ekranda "Gömme üretilemedi: Hugging Face embedding hatası (402)" yazdı.
- **Nasıl bulundu:** Geliştirici canlı sitede belge yüklerken gördü ve bildirdi.
- **Neden:** HTTP 402 (*Payment Required*), Hugging Face Inference API'nin ücretsiz aylık kredisinin bittiğini gösteriyordu. Kodda bir yanlışlık yoktu; sorun servis sınırıydı. Ancak hata mesajı bu nedeni ve çözümü söylemiyordu.
- **Düzeltme:**
  1. Hata mesajı artık nedeni ve çözümü söylüyor.
  2. Geliştiricinin seçimiyle yeni embedding servisi eklendi: `GeminiEmbedder` (`app/services/embedder.py`; Google `gemini-embedding-001`, 768 boyut), `EMBEDDING_BACKEND=gemini`. `MIN_SCORE` gerçek ölçümle 0,55 seçildi (`docs/istem-deneyleri.md`).
  3. Ölçüm sırasında ikinci bir sorun bulundu: geçerli anahtarla isteklerin yaklaşık %12'si nedensiz `403 PERMISSION_DENIED` dönüyordu. Bu yanıt artık geçici sayılıyor ve 1–2 sn sonra yeniden deneniyor.
  4. Yayından sonra canlıda hâlâ Hugging Face kullanılıyordu: Vercel'de `EMBEDDING_BACKEND` değeri `hf` kalmıştı. Geliştirici bu değeri `gemini` olarak düzeltti ve yeniden yayınladı.
  5. Aynı PDF bu kez Gemini'nin dakikalık sınırına (429) takıldı. Ölçüm: ücretsiz katman toplu istekteki her metni ayrı sayıyor (64 + 64 metin → 429, 64 + 30 → başarılı). `GeminiEmbedder` artık son 60 sn'de gönderdiği metni sayıp sınırı aşmadan bekliyor (`GEMINI_TEXTS_PER_MINUTE=90`).
- **Doğrulama:** `tests/test_gemini.py` (sahte Gemini sunucusuna karşı; 403, 429 ve hız sınırı senaryoları). Canlıda aynı PDF (185 parça) indekslendi, `/search` 200 döndü.
- **Ders:** Ücretsiz servislerin sınırları da kod kadar önemli; hata mesajı kullanıcıya nedeni söylemeli; bir ortam değişkeni değiştirildiğinde canlıdaki değer ayrıca kontrol edilmeli.

## Hata 10 - CSV rapor Excel'de bozuk açılıyordu
- **Belirti** (2026-10-03): Rapor sekmesinden indirilen CSV dosyası Excel'de açılınca Türkçe karakterler bozuk görünüyor, her satır tek bir hücreye yığılıyordu.
- **Nasıl bulundu:** Geliştirici dosyayı kendi bilgisayarında Excel'de açınca fark etti.
- **Neden:** (1) Arayüz dosyayı `res.text()` ile okuyup yeniden oluşturuyordu; bu sırada UTF-8 BOM işareti siliniyor, Excel de dosyanın UTF-8 olduğunu anlayamıyordu. (2) Türkçe bölgesel ayarlı Excel liste ayracı olarak `;` bekliyor; `,` ile ayrılmış satır tek hücreye yığılıyordu.
- **İlk düzeltme:** Dosya blob olarak indiriliyor (BOM korunuyor), ayraç `;`, ondalık ayraç virgül, etiketler Türkçe.
- **Sonuç ve karar:** Excel'in bölgesel ayarlarına bağlı sorunlar sürdü. Geliştirici raporun PDF olarak indirilmesine karar verdi: `GET /reports/usage.pdf`, `app/services/report_pdf.py` (reportlab). Türkçe harfler için reportlab içindeki Vera yazı tipi kullanılıyor (varsayılan Helvetica Türkçe harfleri basamıyor). CSV ucu API'de kaldı; arayüzdeki düğme "PDF indir" oldu.
- **Doğrulama:** `tests/test_rapor_pdf.py`; örnek PDF görsel olarak incelendi (siyah zemin üzerinde siyah başlık ve grafik taşması bulunup düzeltildi); canlıda düğme ve uç yayında (girişsiz istek 401).
- **Ders:** Görünümü açıldığı programın ayarlarına bağlı bir biçim yerine, her yerde aynı görünen bir biçim (PDF) rapor için daha güvenilir.

## Açık kalanlar (bilinçli olarak bırakıldı)
| Sorun | Nerede | Not |
|---|---|---|
| Soru sayısı 0 iken grafik etiketi "en yüksek: 1" | frontend `public/report.js` | `Math.max(1, ...)` sıfıra bölmeyi önlüyor (doğru), ama aynı değer etikete de yazılıyor. Öğrencinin hata ayıklama örneği için ayrılmıştı; onun yerine canlıda bulunan Hata 9 ve 10 kaydedildi. Hâlâ açık. |
| Anahtar yokken son kullanıcıya teknik mesaj | `app/services/llm_client.py` / sohbet arayüzü | Adım 12 kullanılabilirlik iyileştirmesi adayı (senin görevin 3 için uygun). |
