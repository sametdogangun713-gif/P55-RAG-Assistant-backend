# Vize demo senaryosu (yaklaşık 5 dakika)

**Hazırlık (demodan önce):** temiz bir veritabanı (`data\asistan.db` sil), `.env` içinde `EMBEDDING_BACKEND=local` (ya da hızlı olsun diye `hash`),
2 kısa **sentetik** belge hazırla (kişisel veri yok): biri "vektör arama", biri başka bir konu hakkında. Sunucu açık: `uvicorn app.main:app --reload`.

1. **(30 sn) Mimari:** `docs/mimari.md` şemasını göster: api → services → db.
2. **(30 sn) Veritabanı:** `docs/er-diyagrami.md`'yi göster; `001_init.sql` içinde bir yabancı anahtar ve bir CHECK kısıtı göster.
3. **(45 sn) Kayıt ve giriş:** tarayıcıda kayıt ol, giriş yap. Yanlış parolayla bir kez dene → genel hata mesajı.
4. **(60 sn) Yükleme:** belgeyi yükle; tabloda durumun `hazır` olduğunu ve parça sayısını göster. `.exe` uzantılı bir dosyayı yüklemeyi dene → reddedilir.
5. **(60 sn) Arama:** belgedeki bir konuyu sor; en üstteki sonucun doğru parça olduğunu ve skorunu göster. Belgede olmayan bir şey sor → skorların düşük olduğunu göster (Hafta 10'un konusu).
6. **(30 sn) Yetki:** ikinci bir kullanıcıyla giriş yap; ilk kullanıcının belgelerini göremediğini göster.
7. **(30 sn) Test:** terminalde `pytest` → hepsi geçiyor.
8. **(30 sn) GitHub:** depo sayfasını, commit geçmişini ve `v0.1-vize` etiketini göster.

**Olası takılma noktaları:** ilk `local` embedding çalıştırması model indirir (önceden bir kez çalıştır) · port 8000 meşgulse `--port 8001` · token süresi dolarsa yeniden giriş.
