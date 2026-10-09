# Vize sözlü hazırlığı (Hafta 3–8 kapsamı)

Kapsam (ders paketi): geliştirilen modüller, algoritmalar, veritabanı, kod yapısı, yapay zekâ kullanımı ve yazılım mimarisi.
Cevap iskeletlerini **kendi cümlelerinle** yeniden yaz; ezberleme, anla.

## Mimari ve kod yapısı
**Neden katmanlı mimari?** Sorumluluk ayrımı: API yalnızca HTTP/yetki, servisler iş kuralı, `db` yalnızca SQL. Test ve değişiklik kolaylığı.
**Bağımlılık yönü?** api → services → db. Alt katman üst katmanı bilmez.
**Neden `hafta-XX` klasörleri?** Her haftanın notu, testi, açıklaması ve AI günlüğü bir arada; kod ortak `app/` içinde kümülatif.

## Veritabanı
**Hangi tablolar, ilişkiler?** users 1-N documents 1-N chunks 1-1 embeddings; users 1-N conversations 1-N messages; messages N-N chunks (message_sources).
**Neden migration?** Şema sürümlemesi, tekrarlanabilir kurulum.
**`foreign_keys` pragması?** SQLite'ta varsayılan kapalı; açılmazsa CASCADE ve referans bütünlüğü çalışmaz.
**SQL enjeksiyonu?** Parametreli sorgular (`?`); girdi SQL metnine eklenmez.

## Algoritmalar
**Chunking?** Paragraf → cümle; 600 karaktere kadar birleştir; ~100 karakter örtüşme; çok uzun cümleyi kelime sınırından kes.
**Embedding?** Metin → sabit boyutlu vektör (yerel çok dilli model); normalize.
**Benzerlik?** Kosinüs = normalize vektörlerde nokta çarpımı; matris çarpımıyla tüm parçalar tek seferde skorlanır; `argpartition` + `argsort` ile en iyi k.
**Neden tüm belgeleri değil de vektörleri saklıyoruz?** Vektörleri bir kez üretip saklamak, her aramada yeniden hesaplamayı önler.

## Güvenlik
**Parola?** scrypt + rastgele tuz. **Token?** İmzalı JWT (HS256), süreli. **Rol?** Sunucuda, DB'den okunan role göre (`require_admin`).
**Yükleme güvenliği?** Tür beyaz listesi, boyut sınırı, içerik-uzantı uyumu, UUID dosya adı, sahiplik kontrolü (404).
**XSS?** Arayüz sunucu metnini `textContent` ile yazar.

## Yapay zekâ kullanımı (şeffaflık)
- Bu projede yapay zekâ **AI Pair Programmer** olarak kullanıldı: kod önerisi, test, dokümantasyon taslağı.
- Her anlamlı yardım `docs/ai-kullanim-gunlugu/ai-kullanim-gunlugu.md` dosyalarında kayıtlı; çıktıları çalıştırarak/test ederek ve kendi değişikliklerimle doğruladım.
- Açıklayamadığım kodu teslim etmem; bu yüzden her hafta bu belgenin "Kod açıklaması" bölümü'yi okuyup kendi cümlelerimle anlattım.

## Sık gelebilecek ek sorular
- Parça boyutunu değiştirsen arama kalitesi nasıl etkilenir? (Küçük: bağlamsız; büyük: bulanık vektör.)
- İki farklı embedding modeli aynı veritabanında olabilir mi? (Evet, `model` sütunu ile; ama karşılaştırma yalnızca aynı modelle.)
- 1 milyon parça olsaydı? (Tüm matrisi bellekte çarpmak yavaşlar → yaklaşık en yakın komşu indeksleri: FAISS/sqlite-vec/pgvector.)
- `hash` embedder neden var, ne kadar iyi? (İndirmesiz test/yedek; anlamsal değil biçimsel benzerlik.)
- Kilit sayacı sunucu yeniden başlayınca ne olur? (Sıfırlanır; bilinen sınır, `docs/guvenlik-notu/guvenlik-notu.md`.)
