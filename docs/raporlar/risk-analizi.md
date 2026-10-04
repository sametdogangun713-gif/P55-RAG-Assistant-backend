# 1. Risk Analizi

| | | | |
|---|---|---|---|
| **Öğrenci** | Samet DOĞANGÜN | **Numara** | 211161024 |
| **Proje (Kod/Ad)** | P55 – Belge Tabanlı Soru-Cevap Asistanı (RAG) | **Tarih** | 04.10.2026 (ilk sürüm) |

**Skor:** Olasılık (1–3) × Etki (1–3). 1–2 düşük, 3–4 orta, 6–9 yüksek risk. Yüksek riskler için mutlaka önlem tanımlanır.

> 💬 Bu bir **taslaktır**: olasılık/etki puanları öğrencinin kendi değerlendirmesidir; gözden geçirip gerekirse değiştir.
> Dönem boyunca yeni bir risk çıkarsa ya da biri gerçekleşirse tabloya ve "Gerçekleşen riskler" bölümüne eklenir.

| No | Risk | Kategori | Ol. | Etki | Skor | Önlem / Aksiyon |
|---|---|---|---|---|---|---|
| 1 | Kodun büyük kısmı yapay zekâ ile yazıldığı için öğrencinin kodu sözlüde açıklayamaması | AI/Etik | 3 | 3 | **9** | Her adımın belgesindeki açıklama ve sözlü sorular haftasında birlikte çalışılır; "Kendi yapacakların" görevlerini öğrenci kendisi yapar; AI günlüğü; açıklayamadığı kod teslim edilmez |
| 2 | RAG, embedding, vektör arama gibi yeni kavramların öğrenilmesinin uzun sürmesi | Teknik | 2 | 3 | **6** | Her hafta yalnızca o haftanın kavramına odaklanmak; küçük denemeler (ör. `scripts/hf_dene.py`); kavram notları `docs/gelistirme/` içinde |
| 3 | Gizli anahtarın (API anahtarı, parola) depoya, ekrana ya da sohbete sızması | Güvenlik | 2 | 3 | **6** | Anahtarlar yalnızca `.env` / Vercel ortam değişkenlerinde; `.gitignore`; commit öncesi tarama; sızarsa anahtar hemen iptal edilip yenisi üretilir |
| 4 | Demo günü internet ya da bulut servisinin (Vercel, Supabase, Groq) çalışmaması | Dış | 2 | 3 | **6** | Aynı kod yerelde de çalışır (SQLite + yerel embedding); demo senaryosu yerelde de prova edilir |
| 5 | Harici API'nin (Groq, Hugging Face) ücretsiz katman limiti, model kaldırılması ya da ücret çıkarması | Dış | 2 | 2 | 4 | Sağlayıcı ve model `.env`'den değişir (Groq ↔ Claude); embedding yerelde de çalışır; hata mesajları anlaşılır (503) |
| 6 | Ücretsiz bulut planı sınırları (Supabase dosya başına 50 MB, hareketsiz projeyi duraklatma; Vercel istek süresi) | Dış | 2 | 2 | 4 | Büyük belge parça parça indekslenir; sınır arayüzde gösterilir; demo öncesi proje uyandırılır |
| 7 | Modelin belgede olmayan bilgiyi uydurması (halüsinasyon) ya da yanlış kaynak göstermesi | AI | 2 | 2 | 4 | Yalnızca getirilen parçalara dayanan istem, alıntı doğrulama, benzerlik eşiği (`MIN_SCORE`), "belgede yok" yanıtı; ölçümler `istem-deneyleri.md` |
| 8 | Haftalık teslimlerin birikmesi, haftasında yüklenmemesi | Zaman | 2 | 2 | 4 | Her hafta başında haftalık rapor dosyası açılır, hafta içinde commit; takvim `proje-takvimi.md` |
| 9 | Gerçek kişisel verinin sisteme ya da yapay zekâya girilmesi (KVKK) | Etik/Hukuk | 1 | 3 | 3 | Yalnızca sentetik veri (`@example.com`); demo belgeleri uydurma |

## Gerçekleşen riskler (dönem içi kayıt)
| Tarih | Risk no | Ne oldu? | Ne yapıldı? |
|---|---|---|---|
| 03.10.2026 | 3 | Groq API anahtarı yapay zekâ sohbetine yapıştırıldı | Anahtar iptal edildi (sonraki istek 401), yenisi yalnızca `.env`'e yazıldı; sohbete anahtar yazılmaması kuralı |
| 03.10.2026 | 5 | Planlanan Groq modeli (`llama-3.3-70b-versatile`) hesapta yoktu (404) | Hesaptaki model listesi kontrol edildi, `openai/gpt-oss-120b`'ye geçildi |
| 03.10.2026 | 7 | Bulutta yanıt kalitesi düşüktü: embedding modeli Türkçe parçaları 128 token'da kesiyordu | Model `BAAI/bge-m3`'e değiştirildi, ölçüldü (12 sorudan 9 → 11 doğru) |
