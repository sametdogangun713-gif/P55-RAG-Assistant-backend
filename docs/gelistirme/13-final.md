# Adım 13 — Final entegrasyon, sürüm ve sunum

> Ders planındaki karşılığı: **Hafta 15** — tüm modüllerin son entegrasyonu, uçtan uca senaryo, `v1.0-final`, demo ve sunum.
> Final sözlü savunması 16. haftada. **Bu adımın büyük kısmı senin işin:** sistemi kendin anlatabilmelisin.

## Ne yapılacak

### 1. Son entegrasyon kontrolü
- [ ] Backend testleri: `pytest` → hepsi geçiyor (sayıyı [`../test-raporu.md`](../test-raporu.md)'ye yaz)
- [ ] Frontend testleri: `python -m unittest discover -s tests`
- [ ] Bulutta [`../dagitim.md`](../dagitim.md) §5 kontrol listesi **gerçek API ile** (Groq + Hugging Face + Supabase)
- [ ] Yerelde de aynı senaryo (backend `uvicorn` + frontend `http.server`) — internet kesilirse demo yerelden yapılır
- [ ] `git grep -n "sb_secret_\|gsk_\|hf_\|sk-ant-"` iki depoda da boş; `.env` depoda yok
- [ ] Supabase projesi **aktif** (1 hafta kullanılmazsa durur — sunumdan 1 gün önce aç)

### 2. Sürüm
1. [`../../CHANGELOG.md`](../../CHANGELOG.md) → `[1.0.0]` bölümünü son hâliyle doldur.
2. İki depoda da etiket:
   ```bat
   git tag -a v1.0-final -m "P55 final sürümü"
   git push origin v1.0-final
   ```

### 3. Demo senaryosu (≈ 7 dakika)
Vize senaryosunun ([`../demo-senaryosu.md`](../demo-senaryosu.md)) devamı. Önerilen akış:
1. **Problem (30 sn):** Uzun belgelerde bilgi bulmak zor; sohbet botları uydurur.
2. **Ana sayfa → kayıt/giriş** (bulut adresinden).
3. **Belge yükle** (PDF, birkaç MB) → yüzde ilerlemesi → "hazır". Supabase Storage'da dosyayı göster.
4. **Arama:** belgedeki bir kavram → parça + benzerlik skoru. "Kelime değil anlam araması" vurgusu.
5. **Sohbet:** belgede olan soru → `[1]` kaynaklı yanıt ve kaynak listesi. Takip sorusu ("peki bunun dezavantajı?") → bağlam korunuyor.
6. **Halüsinasyon önleme:** belgede olmayan soru → "bilgi bulamadım".
7. **Rapor:** soru sayısı, kaynağa dayalı oran, en çok kullanılan belge; CSV.
8. **Yönetim** (yönetici hesabı) kısaca.
9. **Mimari slaydı** (aşağıda) + testler: `pytest` çıktısı.
Yedek plan: bulut çalışmazsa yerel sürüm; internet yoksa ekran görüntüleri.

### 4. Sunum taslağı (8–10 slayt)
1. Başlık: P55 – Belge Tabanlı Soru-Cevap Asistanı · Samet DOĞANGÜN · Öğr. Gör. Mustafa NARİN
2. Problem ve hedef
3. Ne yapar? (özellik tablosu)
4. Mimari: tarayıcı → frontend (Vercel) → backend (Vercel, FastAPI) → Supabase (PostgreSQL + pgvector, Storage), Hugging Face, Groq ([`../dagitim.md`](../dagitim.md) diyagramı)
5. RAG nasıl çalışır: parçalama → embedding → benzerlik → kaynaklı istem → alıntı doğrulama
6. Güvenlik: scrypt, JWT, sahiplik kontrolü, RLS, gizli anahtarlar, CORS
7. Test ve kalite: test sayıları, kapsam, bulunan gerçek hatalar
8. Dağıtım: yerelden buluta, karşılaşılan sınırlar ve çözümleri
9. Yapay zekâ kullanımı: nerede, nasıl doğruladım, neyi kendim yaptım
10. Sınırlar ve gelecek çalışmalar

### 5. Olası jüri soruları ve cevap iskeleti
**1) Sistemin tamamını uçtan uca anlat.** Kullanıcı belge yükler → metin çıkarılır, ~600 karakterlik örtüşen parçalara bölünür → her parça çok dilli modelle 384 boyutlu vektöre çevrilir, PostgreSQL'de (pgvector) saklanır → soru da vektöre çevrilir, kosinüs benzerliğiyle en yakın parçalar bulunur → eşiğin altındakiler atılır → kalanlar numaralı kaynak olarak LLM'e verilir, "yalnızca bunlara dayan, `[n]` ile alıntı yap, yoksa BILGI_YOK de" denir → yanıttaki alıntılar doğrulanır → yanıt ve kaynaklar kaydedilir, raporlara yansır.
**2) Mimari kararlarının artı/eksileri.** Katmanlı (api → services → db): test edilebilir, değiştirilebilir; eksi: küçük projede fazladan dosya. İki depo: arayüz ve API bağımsız dağıtılır; eksi: CORS ve adres ayarı. SQLite + PostgreSQL: yerelde kurulumsuz, bulutta kalıcı; eksi: iki migration klasörü. Hazır RAG kütüphanesi (LangChain vb.) yerine kendi kodum: her satırı açıklayabiliyorum; eksi: daha çok kod.
**3) Yapay zekâyı nerede, neden kullandın?** Üründe: embedding (anlam araması) ve yanıt üretimi (LLM). Geliştirmede: AI eş programcı (kod önerisi, test fikri, hata ayıklama) — her öneriyi testle doğruladım, açıklayabildiğim hâle getirdim; ayrıntı `ai-kullanim-gunlugu.md`. *(Kendi örneğini ekle.)*
**4) Nasıl ölçeklendirirsin?** Vektör sütununu boyutla sabitleyip HNSW indeksi; indekslemeyi kuyruğa alıp arka planda yapmak (yükleme beklemesin); başarısız giriş sayacını veritabanına/Redis'e taşımak; LLM yanıtlarını önbelleğe almak; ücretli planlarla süre/boyut sınırlarını yükseltmek.
**5) Yeniden yapsan neyi farklı yapardın?** *(Kendi cevabın.)* Fikir: baştan PostgreSQL ile başlamak; indekslemeyi baştan arka plan işi olarak tasarlamak; arayüzde bir çerçeve (ör. küçük bir bileşen yapısı) kullanmak.

## Kendi yapacakların
1. Demo senaryosunu **en az iki kez** baştan sona prova et (bir kez bulutta, bir kez yerelde), süreyi tut.
2. Sunum slaytlarını **kendin** hazırla (taslak yukarıda).
3. Jüri sorularının 3. ve 5. cevaplarını **kendi cümlelerinle** yaz.
4. `CHANGELOG.md` `[1.0.0]` bölümünü tamamla, `v1.0-final` etiketini iki depoda da at.
5. Kod tabanından rastgele 3 dosya seç; her birini satır satır anlatabildiğini kendine sesli anlatarak kontrol et.
6. `ai-kullanim-gunlugu.md` → Adım 13 "kendi" alanları.
