# Yol haritası ve ilerleme

Ders planındaki (Bilgisayar Uygulamaları I, P55) adımların durumu ve kalan güzergâh.
Son güncelleme: **2026-10-04** (sürüm 0.18.1). Ölçüm: backend `pytest` → 319 geçti / 2 atlandı (SQLite, kapsam %92); PostgreSQL 16 + pgvector: 320 geçti / 1 atlandı (kapsam %95); frontend 26 test geçti.

## 1. Adımlar
| Adım | Konu | Ders planı | Kod | Test | Belge | Senin görevlerin |
|---|---|---|---|---|---|---|
| 1 | Kurulum, mimari, ER | Hafta 3 | ✅ | ✅ | ✅ | 0 / 3 |
| 2 | Veritabanı şeması, migration, CRUD | Hafta 4 | ✅ | ✅ | ✅ | 0 / 4 |
| 3 | Kimlik doğrulama, roller | Hafta 5 | ✅ | ✅ | ✅ | 0 / 4 |
| 4 | Belge yükleme, ayrıştırma, parçalama | Hafta 6 | ✅ | ✅ | ✅ | 0 / 4 |
| 5 | Embedding, vektör arama | Hafta 7 | ✅ | ✅ | ✅ | 0 / 4 |
| 6 | Entegrasyon, web arayüzü (vize) | Hafta 8 | ✅ | ✅ | ✅ | 0 / 4 |
| 7 | LLM API istemcisi (Claude + Groq) | Hafta 9 | ✅ | ✅ | ✅ | 0 / 5 |
| 8 | RAG, kaynaklı yanıt | Hafta 10 | ✅ | ✅ | ✅ | 0 / 4 |
| 9 | Sohbet geçmişi, özetleme | Hafta 11 | ✅ | ✅ | ✅ | 0 / 4 |
| 10 | Rapor, yönetim | Hafta 12 | ✅ | ✅ | ✅ | 0 / 5 |
| 11 | Test, hata ayıklama | Hafta 13 | ✅ | ✅ | ✅ | 0 / 5 |
| 12 | Dokümantasyon, arayüz, dağıtım (Supabase + Vercel, iki depo) | Hafta 14 | ✅ | ✅ | ✅ | 0 / 5 |
| 13 | Final entegrasyon, `v1.0-final`, sunum | Hafta 15 | — | — | 🟡 iskelet | 0 / 6 |

**Özet:** kod ve otomatik testler tamam; uygulama **canlıda** (Supabase + Vercel, 2026-10-03'ten beri; iki depo GitHub'da,
`v0.1-vize` etiketi iki depoda da var); "senin görevlerin" **0 / 57**. Ders kuralı gereği bu görevleri ve sözlü açıklamayı **sen** yaparsın — açıklanamayan kod puanlanmaz.

## 2. Kalan güzergâh (sıralı)
Sıra, birbirine bağımlılığa göre seçildi: önce hesaplar (her şey onlara bağlı), sonra gerçek ortamda doğrulama, sonra kişisel görevler, en son final.

### A. Depolar ve hesaplar — ✅ tamam
1. ✅ GitHub'da iki public depo (`P55-RAG-Assistant-backend`, `P55-RAG-Assistant-frontend`).
2. ✅ Yükleme kararı: hoca toplu yüklemeye izin verdi (geliştiricinin sözü). Commit tarihleri gerçek.
3. ✅ Supabase (`eu-central-1`), Hugging Face, Vercel hesapları; tablolar + gizli kova kuruldu; iki proje yayında.

### B. Gerçek ortamda doğrulama — *birlikte* (kısmen)
1. ✅ Canlıda: `/health` → postgres, CORS, doğrulama e-postası ulaştı, belge yükleme + yeniden indeksleme + sohbet çalıştı.
2. ⬜ [`dagitim.md`](dagitim.md) §5 uçtan uca kontrol listesi **maddeleri tek tek, ekran görüntüsüyle** (rapor PDF'i, API anahtarı
   bildirimi, yönetici iptali, şifremi unuttum canlıda henüz denenmedi).
3. ⬜ Bulutta `MIN_SCORE` kontrolü (`bge-m3`, eşik 0,40): belgede **olan** 5 / **olmayan** 5 soru, `best_score` değerleri.
4. ⬜ Canlıda karşılaşılan her sorunu [`duzeltilen-hatalar.md`](duzeltilen-hatalar.md)'ye ekle.

### C. Senin görevlerin — *sen* (öncelik sırasıyla)
Her görevin ayrıntısı ilgili adım belgesinde ("Kendi yapacakların"). Sözlüde sorulma olasılığı yüksek olanlar önce:
1. **Adım 11:** `tests/test_benim.py` (2–3 anlamlı test) + Rapor'daki **"en yüksek: 1"** hatasını adım adım ayıkla, `duzeltilen-hatalar.md`'ye "Hata 9" olarak yaz.
2. **Adım 1:** `mimari.md` → "Gerekçem" (artık SQLite + PostgreSQL ve iki depo kararını da içermeli).
3. **Adım 3:** `PATCH /admin/users/{id}/role` uç noktası + testi.
4. **Adım 2:** `size_bytes >= 0` kısıtı — SQLite'ta `001_init.sql`, PostgreSQL'de **yeni** migration (`migrations/postgres/002_*.sql`) + test.
5. **Adım 4 / 9:** iş kuralları (kullanıcı başına 20 belge, 50 sohbet) + testleri.
6. **Adım 5:** numpy'sız kosinüs benzerliği; **Adım 8:** kendi `SYSTEM_PROMPT`'un (`rag-v2`) gerçek API ile; **Adım 10:** kendi metriğin.
7. Tüm adımlar: `ai-kullanim-gunlugu.md` "kendi" alanları.

### D. Final — *sen, ben yardımcı* (Adım 13)
`CHANGELOG.md` son hâli → `v1.0-final` etiketi (iki depoda) → demo senaryosu provası (en az 2 kez) → sunum → jüri soruları.
Ayrıntı: [`gelistirme/13-final.md`](gelistirme/13-final.md).

## 3. Kim ne yapar?
| İş | Kim |
|---|---|
| Kod, test, teknik belgeler, sorun giderme | Claude (AI eş programcı) + sen gözden geçirir, açıklayabilir hâle gelirsin |
| Hesaplar, anahtarlar, parolalar, GitHub'a yükleme kararı | **Yalnızca sen** |
| "Kendi yapacakların" görevleri, AI günlüğünün "kendi" alanları, sözlü cevaplar | **Yalnızca sen** (yol gösterilir, yerine yapılmaz) |
| Ders kuralı / takvim belirsizlikleri | Hocan |
