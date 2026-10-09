# Teslim kontrol listesi — P55 gereksinimleri karşılanıyor mu?

Kaynak: ders paketi, P55 künyesi (s. 40) ve P55 haftalık faaliyet planı (s. 475–482).
Kontrol tarihi: **2026-10-08**. O gün yapılan ölçümler:

- Backend `pytest`: **336 geçti, 2 atlandı, 0 başarısız**
- Frontend `unittest`: **29 geçti**
- Canlı `/health` yanıtı: `{"status":"ok","database":"postgres"}`, frontend 200 döndü
- Gizli anahtar taraması iki depoda da temiz çıktı (tek eşleşme, `tests/test_llm.py` içindeki sahte test değeri)

Depolar:
- **backend** = https://github.com/sametdogangun713-gif/P55-RAG-Assistant-backend
- **frontend** = https://github.com/sametdogangun713-gif/P55-RAG-Assistant-frontend

Durum işaretleri: ✅ yapıldı · 🟡 kısmen · ⬜ yapılmadı · 💬 öğrencinin kendisi yapmalı (ders kuralı: yapay zekâ yerine yapamaz).

---

## 1. Proje künyesi (s. 40): temel modüller

| Gereksinim | Durum | GitHub'daki dosya |
|---|---|---|
| Belge yükleme/ayrıştırma (PDF, DOCX, TXT) | ✅ | backend `app/services/documents.py`, `parser.py`, `storage.py` (Supabase Storage) · `app/api/documents.py` · frontend `public/docs/docs.js` |
| Parçalama ve gömme (embedding) | ✅ | backend `app/services/chunker.py` (600 kr. parça, 100 kr. örtüşme), `embedder.py` (yerel MiniLM / Google Gemini), `indexing.py` |
| Vektör arama | ✅ | backend `app/services/vector_search.py`, `app/db/embeddings.py` (PostgreSQL + pgvector `<=>`), `app/api/search.py` |
| Yanıt üretimi (kaynaklı) | ✅ | backend `app/services/rag.py` (alıntı doğrulama), `prompts.py`, `llm_client.py` (Groq / Claude) |
| Sohbet geçmişi | ✅ | backend `app/services/chat.py`, `app/db/conversations.py`, `app/api/conversations.py` · frontend `public/chat/chat.js` |
| Yönetim | ✅ | backend `app/services/admin.py`, `app/api/admin.py` · frontend `public/admin/admin.js` |
| Yapay zekâ bileşeni: RAG | ✅ | `rag.py` + [`../gelistirme/08-rag.md`](../../gelistirme/08-rag/08-rag.md) + [`../istem-deneyleri.md`](../../istem-deneyleri/istem-deneyleri.md) |
| Önerilen teknolojiler (Python/FastAPI, vektör DB + PostgreSQL, embedding/LLM API) | ✅ | FastAPI · Supabase PostgreSQL + pgvector · Gemini embedding API · Groq LLM API · Vercel |
| 3. parti API'den veri çekme | ✅ | backend `app/services/wikipedia.py`, `app/api/wikipedia.py` (Vikipedi, `GET /wikipedia/search`, `POST /wikipedia/import`) · `tests/test_vikipedi.py` · frontend `public/wiki/wiki.js` |
| Genişletilebilir özellik: çoklu belge | ✅ | arama ve sohbet kullanıcının tüm belgelerinde çalışır |
| Genişletilebilir özellik: sesli soru | ⬜ | yok (künyede isteğe bağlı) |
| Genişletilebilir özellik: kurumsal bilgi tabanı | ⬜ | yok (künyede isteğe bağlı) |

## 2. Haftalık "Teslim edilecek çıktılar" (s. 475–482)

| Hafta | PDF'teki teslim çıktısı | Durum | GitHub'daki dosya | 💬 "Öğrencinin kendi geliştireceği" |
|---|---|---|---|---|
| 3 | GitHub deposu (README + .gitignore) · ER diyagramı · Mimari şema | ✅ | iki depoda `README.md`, `.gitignore` · backend `docs/er-diyagrami/er-diyagrami.md` + `.svg` · `docs/mimari/mimari.md` | 🟡 `mimari.md` "Gerekçem" yazılı; [01](../../gelistirme/01-kurulum-mimari/01-kurulum-mimari.md) "Kendi yapacakların" işaretlenmedi |
| 4 | Şema/scriptler · örnek veriyle dolu DB · CRUD kodu | ✅ | `app/db/migrations/*.sql` (SQLite 001–006, PostgreSQL 001–003) · `scripts/seed.py` (sentetik `@example.com`) · `app/db/*.py` | ⬜ `size_bytes >= 0` kısıtı + test ([02](../../gelistirme/02-veritabani/02-veritabani.md)) |
| 5 | Çalışan kayıt/giriş · rol tabanlı erişim · kısa güvenlik notu | ✅ | `app/services/auth.py`, `app/core/security.py` (scrypt + JWT), `app/api/deps.py` (`require_admin`) · `docs/guvenlik-notu/guvenlik-notu.md` | ⬜ `PATCH /admin/users/{id}/role` + test ([03](../../gelistirme/03-kimlik-dogrulama/03-kimlik-dogrulama.md)) |
| 6 | Çalışan belge yükleme/ayrıştırma · kod + kısa açıklama | ✅ | yukarıdaki dosyalar · [`04-belge-isleme.md`](../../gelistirme/04-belge-isleme/04-belge-isleme.md) | ⬜ kullanıcı başına 20 belge kuralı + test |
| 7 | Çalışan gömme ve vektör arama · kod + kısa açıklama | ✅ | yukarıdaki dosyalar · [`05-embedding-arama.md`](../../gelistirme/05-embedding-arama/05-embedding-arama.md) | ⬜ numpy'sız kosinüs benzerliği |
| 8 (vize) | Etiketli ara sürüm · güncel AI günlüğü · kısa ilerleme raporu | ✅ | `v0.1-vize` etiketi (iki depoda) · `docs/ai-kullanim-gunlugu/ai-kullanim-gunlugu.md` · `docs/ilerleme-raporu-vize/ilerleme-raporu-vize.md` · `docs/demo-senaryosu/demo-senaryosu.md` · `docs/vize-sozlu-hazirlik/vize-sozlu-hazirlik.md` | 💬 demoyu kendin anlatman |
| 9 | Çalışan API entegrasyonu (embedding / vektör DB) · hata yönetimi | ✅ | `embedder.py` (`GeminiEmbedder`: 429 bekleme, dakikalık sınır) · `llm_client.py` (yeniden deneme) · `app/api/errors.py` (502/503/504) · anahtarlar yalnızca `.env` / Vercel'de | ⬜ [07](../../gelistirme/07-llm-istemcisi/07-llm-istemcisi.md) görevleri |
| 10 | Çalışan yapay zekâ bileşeni · AI kullanım günlüğü | ✅ | `rag.py`, `prompts.py` (`rag-v2`) · `docs/istem-deneyleri/istem-deneyleri.md` (gerçek LLM sonuçları) | ⬜ kendi `SYSTEM_PROMPT` denemen |
| 11 | Çalışan sohbet geçmişi ve bağlam · kod + kısa açıklama | ✅ | `chat.py` (özetleme, `CHAT_HISTORY_CHARS=4000`) · [`09-sohbet-gecmisi.md`](../../gelistirme/09-sohbet-gecmisi/09-sohbet-gecmisi.md) | ⬜ kullanıcı başına 50 sohbet kuralı + test |
| 12 | Çalışan rapor/pano · (varsa) bildirim | ✅ | `app/services/reports.py`, `report_pdf.py` (PDF), CSV ucu · frontend `public/report/report.js` · bildirim yok (PDF'te "varsa") | ⬜ kendi metriğin |
| 13 | Test dosyaları · test sonuç raporu · düzeltilen hata listesi | ✅ | backend `tests/` (24 test dosyası) · frontend `tests/test_arayuz.py` · `docs/test-raporu/test-raporu.md` · `docs/duzeltilen-hatalar/duzeltilen-hatalar.md` | 🟡 Kendi bulduğun hatalar **Hata 9** (Hugging Face 402) ve **Hata 10** (CSV / Excel) yazıldı · `tests/test_benim.py` yok |
| 14 | Tamamlanmış README · teknik dokümantasyon · güncellenmiş arayüz | ✅ | iki depoda `README.md` · `docs/teknik-dokumantasyon/teknik-dokumantasyon.md` (tüm API uçları) · `docs/dagitim/dagitim.md` · frontend `public/*` (koyu/açık tema, mobil, ARIA) | ⬜ kurulumu temiz ortamda kendin doğrulaman |
| 15 | Final sürüm (etiketli) · final teknik dokümantasyon · sunum ve demo | 🟡 | `docs/gelistirme/13-final/13-final.md` (demo akışı + 10 slaytlık taslak) · `CHANGELOG.md` | ⬜ `v1.0-final` etiketi yok · `[1.0.0]` boş · sunum dosyası yok · prova yok |

## 3. Genel ders kuralları ve formlar

| Kural / çıktı | Durum | Nerede / not |
|---|---|---|
| Gizli anahtar depoda yok | ✅ | 2026-10-08 taraması temiz; `.env` git-ignore'da |
| Gerçek kişisel veri yok (KVKK) | 🟡 | Depodaki veri sentetik. **Ancak canlı veritabanında kendi CV / SGK belgelerin var.** Demodan önce sil. |
| Ekran görüntüleri | 🟡 | `docs/ekran-goruntuleri/` (10 adet). `01-ana-sayfa.jpg` eski ana sayfayı gösteriyor. |
| AI kullanım günlüğü (Form 8) | ✅ / 💬 | `docs/ai-kullanim-gunlugu/ai-kullanim-gunlugu.md`: "Kendi yaptığım değişiklik" alanları 08.10'da senin onayladığın listeye göre dolduruldu. Kalan 💬: "Açıklar mı? (E/H)" sütunu ve 10 kayıttaki "Neden bu çözümü kullandım" alanı |
| Haftalık ilerleme raporu + kontrol listesi + öz değerlendirme (Form 9/3/5) | ⬜ | `docs/raporlar/haftalik/` içinde yalnızca `_sablon.md` var |
| Proje öneri formu | 🟡 | `docs/raporlar/hafta-02-proje-oneri-formu/hafta-02-proje-oneri-formu.md`. 💬 alanları ve hoca onayı bekliyor |
| Risk analizi · proje takvimi · izleme formu · GitHub kontrol listesi | ✅ / 🟡 | `docs/raporlar/`. Risk puanlarını gözden geçirmen gerekiyor |
| Final teknik dokümantasyon (Form 10) | 🟡 | Bölümler ayrı dosyalarda ([eşleme](../README.md)). 11 (ekran görüntüleri) ve 13 (sonuç) eksik |
| Küçük, açıklayıcı commit'ler, gerçek tarih | ✅ | backend 42, frontend 25 commit. Hoca toplu yüklemeye izin verdi (senin sözün) |
| Yerelde commit'lenmemiş değişiklik | 🟡 | frontend `public/index.html` (menüden "Nasıl çalışır" kaldırıldı) + `tests/test_arayuz.py` |

---

## 4. Sözlü sınav soruları ve cevap iskeleti

Ayrı dosyaya taşındı: [`docs/sozlu-sorular/sozlu-sorular.md`](../../sozlu-sorular/sozlu-sorular.md) (13 hafta × 5 soru + 3. parti API ek soruları).

---

## 5. Eksikler (öncelik sırasıyla)

**Teslimden önce mutlaka (puanı doğrudan etkiler):**
1. 💬 **Kendi yapacakların** kod görevleri yapılmadı (karar: senin; AI günlüğünde de böyle yazıyor). Hata ayıklama örneği olarak Hata 9 ve 10 kaydedildi. Hocan bu bölümlerden puan kırabilir.
2. 💬 **AI günlüğü:** "Açıklar mı? (E/H)" sütunu (yalnızca sen yazabilirsin) ve "Neden bu çözümü kullandım" alanları (10 kayıt).
3. **`v1.0-final` etiketi** (iki depoda) + `CHANGELOG.md` `[1.0.0]` bölümü.
4. 💬 **Sunum** (taslak: [`13-final.md`](../../gelistirme/13-final/13-final.md) §4) ve en az 2 demo provası.
5. **Canlıdaki gerçek kişisel belgeler** (CV, SGK dökümü): demodan önce sil, demoyu sentetik belgeyle yap (KVKK).

**İyi olur:**
6. Haftalık ilerleme raporları (`docs/raporlar/haftalik/`): yalnızca şablon var. Toplu teslim izni olsa bile hocan haftalık rapor isteyebilir; sor.
7. Güncel ekran görüntüleri (`01-ana-sayfa.jpg` eski), Form 10 bölüm 11 ve 13.
8. `dagitim.md` §5'teki canlı kontrollerin eksik kalanları (PDF rapor, şifremi unuttum, API anahtarı bildirimi canlıda denenmedi).
9. Frontend'de commit'lenmemiş küçük değişiklik ("Nasıl çalışır" menü bağlantısı): commit'le ya da geri al.
10. Künyedeki isteğe bağlı genişletmeler (sesli soru, kurumsal bilgi tabanı): zorunlu değil.
