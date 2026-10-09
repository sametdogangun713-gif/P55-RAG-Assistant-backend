# Adım 9 — Sohbet geçmişi ve bağlam

> Ders planındaki karşılığı: **Hafta 11**. Bu belge eski `hafta-11/README.md` ve `hafta-11/aciklama.md` dosyalarının birleşimidir.

## Ne yapıldı

### Amaç
Konuşma geçmişini kalıcı tutan, takip sorularını anlayan ve uzun konuşmaları yönetebilen sohbet modülünü geliştirmek.

### Bu hafta eklenen / değişen dosyalar
| Dosya | Ne işe yarıyor |
|---|---|
| `app/db/migrations/002_message_quality.sql` | `messages`'a durum/kaynağa-dayalı/gecikme/en iyi skor; `message_sources.n` |
| `app/db/migrations/003_conversation_summary.sql` | `conversations.summary`, `summary_upto` |
| `app/db/conversations.py` | Sohbet, mesaj ve mesaj-kaynak CRUD |
| `app/services/chat.py` | Bağlam penceresi, özetleme, takip sorusu yeniden yazma, kalıcı kayıt |
| `app/api/conversations.py` | `POST/GET /conversations`, `GET/POST /conversations/{id}/messages`, `DELETE /conversations/{id}` |
| `app/static/chat.js`, `index.html`, `style.css` (şimdi frontend `public/`) | **Sohbet** sekmesi (liste, mesajlar, kaynaklar) |
| `tests/helpers.py` | Paylaşılan sahte LLM (`ScriptedLLM`) |
| `docs/er-diyagrami/er-diyagrami.md` | Yeni alanlar işlendi |
| frontend `tests/test_arayuz.py` | XSS testi `public/` altındaki tüm uygulama `.js` dosyalarını tarar (vendor/ hariç) |

### Çalıştırma ve demo
```bat
uvicorn app.main:app --reload
```
Tarayıcıda **Sohbet** sekmesi → "Yeni sohbet" → belgene ait bir soru sor → yanıt ve **kaynaklar** (açılır) görünür → "peki ya ... ?" gibi bir takip sorusu sor → sistem önceki konuyu anlar.
Kalıcılık: sayfayı yenile, sohbeti listeden aç; mesajlar duruyor. Başka bir kullanıcıyla giriş yapınca bu sohbetler görünmez.
Uzun sohbet: `.env` içinde `CHAT_HISTORY_CHARS=600`, `CHAT_KEEP_RECENT=2` yapıp 5–6 soru sor; özetleme devreye girer (veritabanında `conversations.summary` dolar).

Testler: `pytest tests/test_sohbet.py` (sahte LLM ile)

### Kendi yapacakların
1. `CHAT_HISTORY_CHARS` ve `CHAT_KEEP_RECENT` değerlerini değiştirerek 8 soruluk bir konuşmada özetlemenin **ne zaman** tetiklendiğini gözle; sonucu bu belgenin "Kod açıklaması" bölümü'deki "Deneyim" bölümüne yaz.
2. Kendi iş kuralını ekle: **kullanıcı başına en fazla 50 sohbet** (aşılırsa 400) veya **sohbet başına en fazla 200 mesaj**. Serviste uygula, teste ekle.
3. `REWRITE_SYSTEM` istemini kendi cümlelerinle yaz; 5 takip sorusunda eski/yeni yöntemi karşılaştır (gerçek API ile).
4. `docs/ai-kullanim-gunlugu/ai-kullanim-gunlugu.md` boş alanlarını doldur.

### Kontrol listesi
- [x] Sohbet Geçmişi ve Bağlam çalışıyor
- [x] Doğrulama/iş kuralları uygulanıyor (sahiplik, boş soru, hata olunca kayıt yok)
- [x] Önceki modüllerle tutarlı (RAG, arama, belge silme)

## Kod açıklaması

### Sorun: LLM'in hafızası yoktur
Her API çağrısı bağımsızdır; "peki ya ikincisi?" sorusunu anlaması için önceki konuşmayı **biz** göndeririz. Ama (1) geçmiş uzadıkça maliyet/gecikme artar ve modelin bağlam sınırı dolar,
(2) takip sorusu tek başına arama için anlamsızdır ("o ne yapar?" → vektör aramada hiçbir şey bulamaz).

### Veri modeli
`conversations` 1-N `messages`; her assistant mesajı N-N `message_sources` ile hangi parçalara dayandığını tutar (`n` = yanıttaki `[n]` işareti).
Migration 002: `messages.status / grounded / latency_ms / best_score` — yanıtın kalitesi (Hafta 12 raporu bunlardan beslenir). Migration 003: `conversations.summary`, `summary_upto` (özete katılan son mesaj id'si).
`ALTER TABLE ... ADD COLUMN` ile mevcut veriye dokunmadan şema büyür; `NOT NULL` kolon için `DEFAULT` gerekir (`summary_upto INTEGER NOT NULL DEFAULT 0`).

### `chat.send_message` akışı
1. Sahiplik (`get_owned_conversation`): yoksa/başkasınınsa aynı hata (404). **Yönetici bile başkasının sohbetini göremez** (gizlilik).
2. Boş/çok uzun soru → `ValueError`, **LLM'e hiç gidilmeden**.
3. **`build_context`:** özetlenmemiş mesajlar (`id > summary_upto`) toplamı `CHAT_HISTORY_CHARS`'ı aşarsa → eski kısım **özetlenir**, son `CHAT_KEEP_RECENT` mesaj birebir kalır. Özet `conversations.summary`'de saklanır, bir sonraki turda önceki özet + yeni bölüm birleştirilir (kayan özet).
4. **`rewrite_question`:** geçmiş varsa LLM'e "son soruyu tek başına anlaşılır yaz" denir; sonuç **aramada** kullanılır, kullanıcıya görünen soru değişmez. Hata olursa özgün soruyla devam.
5. `rag.answer_question(..., history, retrieval_query, system_extra=özet)` (Hafta 10).
6. **Her şey başarılıysa** kullanıcı mesajı + yanıt + kaynaklar kaydedilir. LLM/embedding hatasında **hiçbir şey kaydedilmez** → geçmiş tutarlı kalır (roller hep dönüşümlü), kullanıcı soruyu tekrar gönderebilir.
7. İlk mesajda sohbet başlığı sorunun ilk 60 karakteri olur.

### Önemli ayrıntılar
- **Eski alıntı numaraları temizlenir** (`strip_citations`): önceki yanıttaki `[1]`, yeni istemdeki `[1]` ile karışmasın diye geçmişe giderken silinir. Veritabanındaki metin değişmez.
- **Özet bilgi kaynağı değildir:** sistem istemine "özet yalnızca konuşmayı anlamak içindir, yanıtı yine `<kaynaklar>`'a dayandır" yazılır; aksi halde özetteki (belki hatalı) bilgi kaynaksız gerçek gibi kullanılabilirdi.
- **API kuralı:** roller dönüşümlü, `user` ile başlar, `assistant` ile biter → `normalize_history`.
- **Tek mesaj kırpma:** geçmiş mesajı en fazla 1500 karakter gider.
- **Özetleme başarısız olursa** soru yine yanıtlanır; özet kaydedilmez, sonraki turda tekrar denenir.
- **Maliyet/gecikme dengesi:** takip sorusunda 1 ek LLM çağrısı (yeniden yazma), nadiren bir özet çağrısı var. Alternatif: yeniden yazmayı atlayıp önceki soruyu aramaya eklemek (ucuz ama daha az doğru). Küçük model (`haiku`) kullanıldığı için maliyet düşük tutuldu.
- Belge silinirse eski yanıtlar kalır ama kaynak bağlantıları (`message_sources`, CASCADE) kaybolur; yanıttaki `[n]` işareti yetim kalır — bilinen sınır.

### Sözlü sınav soruları ve cevap iskeleti
**1) Bağlamı nasıl yönettin?** Mesajları veritabanında tutuyorum; her soruda son mesajları (alıntı numaraları temizlenmiş) LLM'e geçmiş olarak veriyorum. Takip sorusunu aramadan önce tek başına anlaşılır hale getiriyorum. Roller dönüşümlü olacak şekilde normalize ediyorum.
**2) Uzun geçmişi nasıl ele aldın?** Karakter bütçesi (`CHAT_HISTORY_CHARS`) aşılınca eski mesajları LLM'e özetletiyorum; özeti `conversations.summary`'de saklıyorum, `summary_upto` ile hangi mesajların özete girdiğini biliyorum; son birkaç mesaj birebir kalıyor. Özet kayan: önceki özet + yeni bölüm → yeni özet.
**3) Bu modülün verisini nasıl modelledim?** `conversations`, `messages` (+ kalite alanları), `message_sources` (N-N, `n` numarası), özet alanları; hepsi kullanıcıya CASCADE ile bağlı.
**4) Hangi iş kuralını neden koydum?** Sohbet sahipliği (yönetici dahil kimse başkasınınkini göremez - gizlilik); hata olursa hiçbir şey kaydetmeme (tutarlı geçmiş); boş soruyu LLM'e gitmeden reddetme (maliyet); özet "kaynak değildir" kuralı (halüsinasyon).
**5) Diğer modüllerle entegrasyon?** Arama (Hafta 7) yeniden yazılmış soruyla çalışır; RAG (Hafta 10) geçmiş + özet alır; kimlik doğrulama (Hafta 5) sahipliği sağlar; Hafta 12 raporu `messages`/`message_sources` alanlarını okur.

### Deneyim (kendi gözlemini yaz)
- `CHAT_HISTORY_CHARS=…`, `CHAT_KEEP_RECENT=…` ile özet … . mesajda tetiklendi.
- Takip sorusu yeniden yazma örnekleri (önce → sonra):

### Sık yapılan hatalar
Doğrulamayı atlamak · erişim/sahiplik kontrolünü unutmak · ilişkili kayıtları yönetmemek · tüm geçmişi sınırsız göndermek · eski kaynak numaralarını yeni istemle karıştırmak.

### Dürüst not
Sohbet servisi sahte LLM ile test edildi (özetleme, yeniden yazma, hata durumları dahil). Gerçek modelin özet ve yeniden yazma kalitesini kendi API anahtarınla gözlemlemen gerekir. Arayüz (`chat.js`) 2026-10-02'de tarayıcıda açıldı: sohbet oluşturma, listeleme ve API anahtarı yokken hata mesajının gösterilmesi çalıştı, konsolda hata yoktu. Gerçek yanıtın ve kaynakların ekranda gösterimi API anahtarıyla ayrıca denenmeli.
