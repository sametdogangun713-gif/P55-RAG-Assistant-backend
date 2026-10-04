# Ders formları ve raporlar

Ders paketinin **Bölüm 4 — Formlar ve Şablonlar** kısmındaki 10 form, bu projeye uyarlanmış hâliyle burada.
Paketteki öneri: Haftalık İlerleme Raporu, Haftalık Kontrol Listesi ve AI Kullanım Günlüğü **her hafta**; Risk Analizi,
Proje Takvimi ve Proje İzleme Formu **dönem başında** oluşturulup dönem boyunca güncellenir.

> **Kim doldurur?** Proje bilgileri, test sonuçları ve tarihler gibi olgusal alanları Claude (AI eş programcı) doldurur.
> 💬 işaretli alanlar **öğrencinin kendi değerlendirmesidir** (öz değerlendirme, "açıklayabiliyor muyum", yapay zekâ
> çıktısında kendi yaptığı değişiklik): bunları yalnızca öğrenci yazar.

## Ne zaman, hangi form?
| No | Form | Sıklık | Dosya | Durum |
|---|---|---|---|---|
| — | Proje öneri formu (ders takvimi, 2. hafta çıktısı) | Bir kez | [`hafta-02-proje-oneri-formu.md`](hafta-02-proje-oneri-formu.md) | 🟡 💬 alanları + hoca onayı bekliyor |
| 1 | Risk Analizi | Dönem başı, gerektikçe güncellenir | [`risk-analizi.md`](risk-analizi.md) | 🟡 taslak, puanları gözden geçir |
| 2 | Proje Takvimi | Dönem başı, her hafta "Durum" | [`proje-takvimi.md`](proje-takvimi.md) | ✅ güncel |
| 3 | Haftalık Kontrol Listesi | Her hafta | [`haftalik/`](haftalik/) (her haftanın dosyasında) | 3. haftadan başlar |
| 4 | Danışman (Öğretim Elemanı) Kontrol Formu | Her hafta | — | Öğretim elemanı doldurur, depoya konmaz |
| 5 | Öğrenci Öz Değerlendirme Formu | Her hafta / dönem | [`haftalik/`](haftalik/) (her haftanın dosyasında) | 💬 3. haftadan başlar |
| 6 | Proje İzleme Formu | Dönem başı, her hafta güncellenir | [`proje-izleme-formu.md`](proje-izleme-formu.md) | ✅ güncel |
| 7 | GitHub Kullanım Kontrol Listesi | Dönem başı, gerektikçe | [`github-kontrol-listesi.md`](github-kontrol-listesi.md) | ✅ güncel |
| 8 | Yapay Zekâ Kullanım Günlüğü | Her hafta | [`../ai-kullanim-gunlugu.md`](../ai-kullanim-gunlugu.md) (başta form tablosu) | 💬 "Değişikliğim" ve "Açıklar mı?" sütunları |
| 9 | Haftalık İlerleme Raporu | Her hafta | [`haftalik/`](haftalik/) — şablon: [`haftalik/_sablon.md`](haftalik/_sablon.md) | 3. haftadan başlar |
| 10 | Final Teknik Dokümantasyon | Final (16. hafta) | Aşağıdaki eşleme; son hâli 15. haftada | 🟡 bölümlerin çoğu hazır |

## Her hafta yapılacaklar (3.–15. haftalar)
1. Haftanın başında `haftalik/hafta-NN.md` şablondan açılır (Claude açar).
2. Hafta içinde: o haftanın gösterimi (demo), "Kendi yapacakların" görevleri, commit'ler.
3. Hafta sonunda: ilerleme raporu + kontrol listesi doldurulur; Proje Takvimi ve Proje İzleme Formu'nda "Durum"
   güncellenir; AI günlüğüne o haftanın satırları eklenir. 💬 alanlarını öğrenci yazar.
4. Hepsi o hafta içinde commit'lenip GitHub'a yüklenir (tarih geriye çekilmez).

## Form 10 — Final Teknik Dokümantasyon eşlemesi
Şablondaki 14 bölüm ve bugün karşılık gelen belge. Final haftasında tek bir belgede birleştirilecek.

| Bölüm | Şu an nerede? |
|---|---|
| 1. Özet · 2. Problem ve Amaç | [`hafta-02-proje-oneri-formu.md`](hafta-02-proje-oneri-formu.md), [`../../README.md`](../../README.md) |
| 3. Gereksinimler | [`hafta-02-proje-oneri-formu.md`](hafta-02-proje-oneri-formu.md) §4 |
| 4. Sistem Mimarisi | [`../mimari.md`](../mimari.md) |
| 5. Veritabanı Tasarımı | [`../er-diyagrami.md`](../er-diyagrami.md) |
| 6. Modüller | [`../teknik-dokumantasyon.md`](../teknik-dokumantasyon.md) §2 |
| 7. API Entegrasyonu | [`../teknik-dokumantasyon.md`](../teknik-dokumantasyon.md) §4, [`../dagitim.md`](../dagitim.md) |
| 8. Yapay Zekâ Bileşeni | [`../gelistirme/08-rag.md`](../gelistirme/08-rag.md), [`../istem-deneyleri.md`](../istem-deneyleri.md) |
| 9. Test | [`../test-raporu.md`](../test-raporu.md), [`../duzeltilen-hatalar.md`](../duzeltilen-hatalar.md) |
| 10. Kurulum ve Kullanım | [`../../README.md`](../../README.md), [`../dagitim.md`](../dagitim.md) |
| 11. Ekran Görüntüleri | ⬜ final haftasında eklenecek |
| 12. Karşılaşılan Zorluklar | [`../duzeltilen-hatalar.md`](../duzeltilen-hatalar.md), haftalık raporların "Karşılaşılan sorunlar" bölümleri |
| 13. Sonuç ve Gelecek Çalışmalar | ⬜ 💬 final haftasında |
| 14. Kaynaklar ve AI Kullanım Beyanı | [`hafta-02-proje-oneri-formu.md`](hafta-02-proje-oneri-formu.md) §6, [`../ai-kullanim-gunlugu.md`](../ai-kullanim-gunlugu.md) |
