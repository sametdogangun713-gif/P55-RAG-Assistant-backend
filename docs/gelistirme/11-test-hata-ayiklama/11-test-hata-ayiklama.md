# Adım 11 — Test ve hata ayıklama

> Ders planındaki karşılığı: **Hafta 13**. Bu belge eski `hafta-13/README.md` ve `hafta-13/aciklama.md` dosyalarının birleşimidir.

## Ne yapıldı

### Amaç
Sistemin sınır durumlarını ve hata senaryolarını test etmek, bulunan hataları ayıklayıp düzeltmek, test sonuçlarını raporlamak.

### Bu hafta eklenen / değişen dosyalar
| Dosya | Ne işe yarıyor |
|---|---|
| `tests/test_sinir_durumlari.py` | 18 sınır durumu / hata senaryosu testi |
| `app/services/documents.py` | Uzun dosya adında uzantıyı koruma (Hata 1) |
| `app/core/security.py` | `verify_password` metin dışı girdide çökmez (Hata 2) |
| `app/services/auth.py` | Başarısız giriş sayacına üst sınır (Hata 3) |
| `app/core/config.py`, `app/main.py` | `APP_ENV`, üretimde zayıf `SECRET_KEY` engeli (Hata 4), `MAX_DOCX_UNCOMPRESSED_MB` |
| `app/services/parser.py` | DOCX zip bombası kontrolü (Hata 5) |
| `app/services/vector_search.py` | Arama sorgusu uzunluk sınırı (Hata 6) |
| `tests/__init__.py` | Testlere uzun, sahte gizli anahtar (uyarıları giderir) |
| `docs/test-raporu/test-raporu.md` | Gerçek `pytest` ve kapsam sonuçları, HTTP ve tarayıcı denemesi |
| `docs/duzeltilen-hatalar/duzeltilen-hatalar.md` | Her hata: belirti, neden, nasıl bulundu, düzeltme, doğrulama |

### Çalıştırma
```bat
venv\Scripts\activate
pip install pytest-cov
pytest
pytest tests/test_sinir_durumlari.py -v
pytest --cov=app --cov-report=term-missing
```
Beklenen: **176 geçti, 1 atlandı**, kapsam **%94** (ölçüm: 2026-10-02).

Üretim kipini dene (zayıf anahtarla açılmamalı):
```bat
set APP_ENV=production
set SECRET_KEY=degistir-bunu
uvicorn app.main:app
```
→ `RuntimeError: SECRET_KEY zayıf...` ile başlamaz. Denemeden sonra aynı pencerede `set APP_ENV=development` yap ya da pencereyi kapat.

### Kendi yapacakların
1. **Kendi testlerini yaz** (en az 2–3 anlamlı test), `tests/test_benim.py` dosyasına. Fikirler:
   - Aynı belgeyi iki kez yükle: ne olmalı? Davranışı test et.
   - Başka kullanıcının sohbetine mesaj göndermeyi dene → 404 / 403 bekleniyor mu?
   - `top_k=0` veya `top_k=51` ile arama → 400.
   - Testi önce **kırmızı** gör, sonra neden geçtiğini/geçmediğini açıkla.
2. **Bir hatayı adım adım ayıkla ve raporla.** Hazır, gerçek bir aday: **Rapor sekmesinde hiç soru yokken grafik "en yüksek: 1" yazıyor.**
   - Yeniden üret: yeni kullanıcıyla giriş yap → Rapor → Göster.
   - Nedeni bul: frontend deposunda `public/report/report.js` içinde etiketin hangi değişkenden geldiğine bak. O değişken neden 1? Neden öyle yazılmış (sıfıra bölme)?
   - Düzelt: çubuk hesabını bozmadan etikette gerçek en büyük değeri göster.
   - Tarayıcıda doğrula (F12 → Console, hata yok).
   - `docs/duzeltilen-hatalar/duzeltilen-hatalar.md`'ye "Hata 9" olarak kendi cümlelerinle yaz (belirti → neden → düzeltme → doğrulama).
   - İstersen bunun yerine kendi bulduğun başka bir hatayı kullan.
3. Testleri ve kapsamı **kendi bilgisayarında** çalıştır; `docs/test-raporu/test-raporu.md`'deki sayılar seninkiyle aynı mı? Farklıysa güncelle.
4. bu belgenin "Kod açıklaması" bölümü → "Deneyim" ve `docs/ai-kullanim-gunlugu/ai-kullanim-gunlugu.md` boş alanlarını doldur.
5. Ekran görüntüsü: `pytest` çıktısı ve kapsam tablosu.

### Kontrol listesi
- [x] Tüm testler geçiyor (`pytest`)
- [ ] Kendi testlerim eklendi ve açıklayabiliyorum
- [ ] Bir hatayı adım adım ayıklayıp raporladım
- [x] Test raporu gerçek sonuçlarla güncel
- [ ] Gizli dosya (`.env`, `*.db`, `uploads/`) depoda yok (`git status`)

## Kod açıklaması

### Test türleri: bu projede hangisi nerede?
| Tür | Ne demek | Bu projede örnek |
|---|---|---|
| **Birim testi** | Tek bir fonksiyonu, dış bağımlılık olmadan sınar | `chunker.split_text`, `security.verify_password`, `sanitize_filename` |
| **Entegrasyon testi** | Birkaç katmanı birlikte sınar (servis + gerçek SQLite + dosya sistemi) | `svc.upload_document` → ayrıştır → parçala → vektörleştir → DB; hatalı migration'ın geri alınması |
| **Uçtan uca (E2E)** | Kullanıcının yaptığı gibi HTTP üzerinden tüm akış | `tests/test_uctan_uca.py` (`TestClient`); `docs/test-raporu/test-raporu.md` §4'teki gerçek sunucu denemesi |

Testlerde **gerçek** SQLite (bellekte, `:memory:`) ve gerçek dosya sistemi (geçici klasör, `TempUploads`) kullanılıyor; sahte (mock) nesne az. İki yerde bilerek sahte nesne var:
- **Embedding:** Gerçek model ~470 MB ve yavaş. Testlerde `HashingEmbedder` kullanılıyor (`tests/__init__.py`).
- **Claude API:** Ücretli ve internet gerektiriyor. `ScriptedLLM` (önceden yazılmış yanıtlar) ve yerel sahte HTTP sunucusu kullanılıyor.

### Sınır durumu (edge case) nedir, ben hangilerini seçtim?
"Mutlu yol" (normal kullanım) dışında kalan, **sınırda** ya da **beklenmedik** girdiler: boş, çok büyük, çok uzun, bozuk, eşzamanlı, kötü niyetli. Seçim mantığım: *kullanıcıdan gelen her girdi* (dosya, dosya adı, sorgu, parola, token) ve *dış kaynaklar* (veritabanı, model) için "en kötü ne gelebilir?" diye sordum. Liste: `docs/test-raporu/test-raporu.md` §2.

### Hata ayıklama yöntemi (6 hatada izlenen adımlar)
1. **Yeniden üret:** Hatayı tetikleyen en küçük girdiyi bul (ör. `"a"*200 + ".txt"`).
2. **Kırmızı test yaz:** Beklenen davranışı test olarak yaz; testin **başarısız** olduğunu gör. Bu, hatanın gerçek olduğunu kanıtlar.
3. **Nedeni bul:** Hata mesajı ve yığın izi (traceback), ilgili satır. Örnek: Hata 2'yi `verify_password("x", None)` ile tetikleyince traceback `AttributeError` gösterir; `except (ValueError, TypeError)` bu türü kapsamıyordu.
4. **En küçük düzeltme:** Yalnızca nedeni düzelt, çevresini yeniden yazma.
5. **Yeşil + regresyon:** Yeni test geçiyor mu, **tüm** testler hâlâ geçiyor mu (`pytest`)?
6. **Belgele:** `docs/duzeltilen-hatalar/duzeltilen-hatalar.md`.

### Neden %100 kapsam hedeflemedim? (Kapsam %94)
- Kapsam yalnızca "bu satır **çalıştı** mı" der, "doğru mu **kontrol edildi** mi" demez. Hiçbir şey kontrol etmeyen bir test de kapsamı artırır.
- Son %5–10'luk kısım genellikle nadir hata dallarıdır (diske yazılamadı, ağ koptu). Bunları zorla tetiklemek çok fazla sahte nesne gerektirir; test kırılgan ve anlaşılmaz olur.
- `embedder.py` %65: gerçek modeli her testte yüklemek testleri dakikalarca yavaşlatır. Bu kodu gerçek sunucuda elle denedim (`docs/test-raporu/test-raporu.md` §4, §6).
- Kaynağı **risk** üzerine harcamak daha değerli: güvenlik, veri bütünlüğü, kullanıcı girdisi.

### Bu hafta değişen kod
| Dosya | Değişiklik | Hata no |
|---|---|---|
| `app/services/documents.py` | Dosya adı kırpılırken uzantı korunur | 1 |
| `app/core/security.py` | `verify_password` metin dışı girdide `False` | 2 |
| `app/services/auth.py` | `MAX_TRACKED_EMAILS`, `_purge_failed()` | 3 |
| `app/core/config.py`, `app/main.py` | `APP_ENV`, `check_secret_key()`, `MAX_DOCX_UNCOMPRESSED_MB` | 4, 5 |
| `app/services/parser.py` | DOCX açılmış boyut denetimi | 5 |
| `app/services/vector_search.py` | Sorgu uzunluğu sınırı | 6 |
| `tests/__init__.py` | Testlere uzun, sahte `SECRET_KEY` | 8 |
| `tests/test_sinir_durumlari.py` | 18 sınır testi | |

### Sözlü sınav soruları ve cevap iskeleti
**1) Birim testi ile entegrasyon testi arasındaki fark nedir?** Birim testi tek bir fonksiyonu yalıtılmış olarak sınar (ör. `chunker.split_text`). Entegrasyon testi birden fazla parçanın birlikte doğru çalıştığını sınar (ör. yükleme → ayrıştırma → parçalama → vektör → veritabanı). Birim testi hızlıdır ve hatanın yerini net gösterir; entegrasyon testi parçalar arasındaki uyumsuzlukları yakalar. Örnek: Hata 7, birim düzeyinde değil, gerçek kütüphaneyle entegrasyonda ortaya çıktı.

**2) Hangi senaryoları test ettin, neden?** Kullanıcıdan gelen her girdi (dosya, dosya adı, sorgu, parola, token) ve dış bağımlılık (veritabanı, model, API) için en kötü durumlar: boş, aşırı büyük, bozuk, kötü niyetli, eşzamanlı. Neden: hatalar en çok bu sınırlarda çıkar ve güvenlik açıkları buradan doğar.

**3) Bir edge case örneği ver.** 200 karakterlik dosya adı: kırpma, uzantıyı silip geçerli dosyanın reddedilmesine yol açıyordu (Hata 1). Ya da birkaç KB'lık DOCX'in açılınca yüzlerce MB olması (Hata 5).

**4) Bulduğun hatayı nasıl ayıkladın?** _(Kendi örneğinle anlat. `README` → Kendi yapacakların 2. madde.)_ İskelet: yeniden ürettim → kırmızı test yazdım → traceback / tarayıcı konsolu / `print` ile nedeni buldum → en küçük düzeltmeyi yaptım → tüm testleri çalıştırdım → belgeledim.

**5) Neden %100 kapsam hedeflenmez?** Kapsam, satırın çalıştığını ölçer, doğrulandığını değil. Son yüzdeler nadir hata dallarıdır ve aşırı sahte nesne gerektirir. Çabayı riskli bölgelere (güvenlik, veri, girdi) harcamak daha verimlidir. Bu projede %94; düşük olan `embedder.py`'yi gerçek modelle elle denedim.

### Deneyim (kendi gözlemini yaz)
- Kendi yazdığım testler ve neden seçtiğim:
- Adım adım ayıkladığım hata:
- Gerçek ortamda beni şaşırtan şey:

### Sık yapılan hatalar
Yalnızca mutlu yolu test etmek · kapsam sayısını kalite sanmak · hatayı test yazmadan düzeltmek (geri gelir) · sahte nesneyle geçen testi yeterli saymak (Hata 7) · testlerin birbirine bağımlı olması (sıra değişince kırılan testler).

### Dürüst not
Bu haftanın testleri ve kapsam ölçümü gerçek FastAPI / pytest ile çalıştırıldı (Windows 11, Python 3.12). Uygulama gerçek sunucuda ve tarayıcıda denendi. **Gerçek Claude API henüz denenmedi** (anahtar yok).
