# 6. Proje İzleme Formu

| | | | |
|---|---|---|---|
| **Öğrenci** | Samet DOĞANGÜN | **Numara** | 211161024 |
| **Proje (Kod/Ad)** | P55 – Belge Tabanlı Soru-Cevap Asistanı (RAG) | **Son güncelleme** | 04.10.2026 (2. hafta) |

Projedeki her modülün planlanan hafta, durum ve tamamlanma yüzdesi ile izlenmesi içindir.

**Tamamlanma % nasıl hesaplanıyor?** Kod + otomatik testler + belge = %70; öğrencinin o modüldeki kendi görevleri
("Kendi yapacakların") = %20; haftalık gösterim (demo) ve sözlü açıklama = %10. Yani kodu hazır ama gösterimi ve kendi
görevleri yapılmamış modül %70 görünür.

| Modül | Planlanan Hafta | Durum | Tamamlanma % | Not |
|---|---|---|---|---|
| Kurulum, katmanlı mimari, ER | 3 | Kod tamam, gösterim bekliyor | 70 | Kendi görevler 0 / 3 (ör. `mimari.md` → "Gerekçem") |
| Veritabanı şeması, migration, CRUD | 4 | Kod tamam, gösterim bekliyor | 70 | 0 / 4 · SQLite + PostgreSQL migration'ları |
| Kimlik doğrulama ve roller | 5 | Kod tamam, gösterim bekliyor | 70 | 0 / 4 · e-posta doğrulama, şifremi unuttum, kişisel API anahtarı da var |
| Belge yükleme, ayrıştırma, parçalama | 6 | Kod tamam, gösterim bekliyor | 70 | 0 / 4 · TXT/PDF/DOCX; bulutta 50 MB |
| Embedding + vektör arama | 7 | Kod tamam, gösterim bekliyor | 70 | 0 / 4 · yerel MiniLM / bulut `bge-m3` |
| Entegrasyon + web arayüzü (vize) | 8 | Kod tamam, gösterim bekliyor | 70 | 0 / 4 · `v0.1-vize` etiketi iki depoda var |
| Harici LLM API istemcisi | 9 | Kod tamam, gösterim bekliyor | 70 | 0 / 5 · Groq (gerçek API ile denendi) + Claude |
| RAG: kaynaklı yanıt | 10 | Kod tamam, gösterim bekliyor | 70 | 0 / 4 · istem `rag-v2` |
| Sohbet geçmişi ve bağlam | 11 | Kod tamam, gösterim bekliyor | 70 | 0 / 4 |
| Kullanım raporu ve yönetim | 12 | Kod tamam, gösterim bekliyor | 70 | 0 / 5 · rapor PDF |
| Test ve hata ayıklama | 13 | Kod tamam, gösterim bekliyor | 70 | 0 / 5 · 319 test geçiyor (SQLite, %92), PostgreSQL 320 (%95) |
| Dokümantasyon, dağıtım | 14 | Kod tamam, gösterim bekliyor | 70 | 0 / 5 · Supabase + Vercel'de canlı |
| Final entegrasyon, sunum | 15 | Planlandı | 10 | 0 / 6 · `docs/gelistirme/13-final.md` iskelet |

**Toplam öğrenci görevi:** 0 / 57 (liste: [`../yol-haritasi.md`](../yol-haritasi.md) §2C).

## Güncelleme geçmişi
| Tarih | Değişiklik |
|---|---|
| 04.10.2026 | İlk sürüm |
| 04.10.2026 | 0.18.1 (API anahtarı bildirimi, yönetici denetimi); test sayıları yeniden ölçüldü; `v0.1-vize` etiketi var |
