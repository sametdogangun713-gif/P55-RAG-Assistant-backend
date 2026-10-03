# Adım 10 — Kullanım raporu ve yönetim

> Ders planındaki karşılığı: **Hafta 12**. Bu belge eski `hafta-12/README.md` ve `hafta-12/aciklama.md` dosyalarının birleşimidir.

## Ne yapıldı

### Amaç
Sorgu ve kaynak kullanımını gösteren raporlama modülünü (toplulaştırma, kaynak istatistiği, dışa aktarma) ve yönetici panelini geliştirmek.

### Bu hafta eklenen / değişen dosyalar
| Dosya | Ne işe yarıyor |
|---|---|
| `app/services/reports.py` | Toplulaştırma SQL'leri, boş günleri doldurma, CSV (formül enjeksiyonuna karşı güvenli) |
| `app/api/reports.py` | `GET /reports/usage`, `GET /reports/usage.csv` (`scope=me` / `all`) |
| `app/services/admin.py` | Kullanıcıyı verisi ve **diskteki dosyalarıyla** silme |
| `app/api/admin.py` | `GET /admin/documents`, `DELETE /admin/users/{id}` (+ önceki uçlar) |
| `app/static/report.js`, `admin.js`, `index.html`, `style.css`, `app.js` (şimdi frontend `public/`) | **Rapor** ve **Yönetim** (yalnız yönetici) sekmeleri |

### Raporda ne var?
- **Toplamlar:** belge (hazır/toplam), parça, sohbet; yöneticide kullanıcı sayısı
- **Dönem (7/30/90 gün):** soru sayısı, yanıt durumu dağılımı, **kaynağa dayalı yanıt oranı**, **yanıtsız kalan oranı** (kapsam boşluğu), ortalama yanıt süresi, ortalama en iyi skor
- **En çok kaynak gösterilen belgeler** (kaç yanıtta kaynak oldu)
- **Günlük soru sayısı** grafiği (boş günler 0 olarak gösterilir)
- **CSV indir**

### Çalıştırma ve demo
```bat
uvicorn app.main:app --reload
```
Birkaç soru sorduktan sonra **Rapor** sekmesi → "Göster". Yönetici ile giriş yapınca "Kapsam: Tüm sistem" ve **Yönetim** sekmesi görünür; normal kullanıcıda `scope=all` isteği **403** verir (Swagger'dan dene).
Doğrulama: raporda "Soru (dönem)" değerini SQL ile elle say (bu belgenin "Kod açıklaması" bölümü'deki sorgu) ve eşleştiğini göster.

Testler: `pytest tests/test_rapor.py` (elle hesaplanmış beklenen sayılarla)

### Kendi yapacakların
1. Kendi metriğini ekle (örn. *yanıt başına ortalama kaynak sayısı* veya *en yoğun saat*): `usage_report`'a SQL'ini yaz, `report.js`'te göster, teste ekle.
2. Rapordaki iki sayıyı **elle SQL ile** doğrula (Python/sqlite3 ile) ve eşleştiğini bu belgenin "Kod açıklaması" bölümü "Deneyim" bölümüne yaz.
3. CSV'yi Excel'de aç; Türkçe karakterler doğru mu? `=`, `+` ile başlayan dosya adı yükleyip CSV'de başına `'` geldiğini gör.
4. Raporda yanıltıcı olabilecek bir durum bul (örn. 1 sorunun olduğu günde "oran %100") ve nasıl yorumlanması gerektiğini yaz.
5. `docs/ai-kullanim-gunlugu.md` boş alanlarını doldur.

> "Bildirim/zamanlama (varsa)" bu projede **kapsam dışı** bırakıldı (PDF'te isteğe bağlı); karar gerekçesi bu belgenin "Kod açıklaması" bölümü'de.

### Kontrol listesi
- [ ] Hesaplar doğru (elle SQL ile doğrulandı)
- [x] Görseller okunaklı (boş günler, etiketler, erişilebilir açıklama)
- [x] Dışa aktarma çalışıyor (CSV)

## Kod açıklaması

### Metrikler ve neden seçtim
| Metrik | Nasıl hesaplanıyor | Ne söylüyor |
|---|---|---|
| Soru sayısı | `messages` içinde `role='user'` ve dönemde | Kullanım yoğunluğu |
| Kaynağa dayalı yanıt oranı | `SUM(grounded) / yanıt sayısı` | Yanıtların kaç %'i **geçerli kaynak alıntısı** içeriyor |
| Yanıtsız kalan oranı | `(no_context + no_info) / yanıt sayısı` | Kullanıcı sorduğu şeyi belgelerde bulamıyor → **kapsam boşluğu**: hangi belge eksik? |
| Ort. yanıt süresi | `AVG(latency_ms)` | Performans |
| Ort. en iyi skor | `AVG(best_score)` | Aramanın ne kadar iyi eşleştiğinin göstergesi |
| En çok kaynak gösterilen belgeler | `message_sources → chunks → documents`, `COUNT(DISTINCT yanıt)` | Hangi belge işe yarıyor |
| Günlük soru sayısı | `GROUP BY date(created_at)` | Kullanım eğilimi |

**Dürüst yorum:** "Kaynağa dayalı" = yanıt geçerli bir kaynak numarası taşıyor demektir; **yanıtın doğru olduğunu kanıtlamaz**. Doğruluğu ölçmek için insan değerlendirmesi/etiketli test seti gerekir (bu projenin kapsamı dışında).
Yanıtsız kalan oranı yüksekse sorun sistemde değil belge koleksiyonunda olabilir.

### Veri nereden geliyor?
Hafta 11'deki migration 002 alanları (`status`, `grounded`, `latency_ms`, `best_score`) ve `message_sources`. Rapor yeni veri üretmez, yalnızca toplulaştırır.
`COUNT(DISTINCT m.id)`: bir yanıt aynı belgeden 3 parça alıntılasa bile belge o yanıt için **bir** kez sayılır.

### Doğrulama için elle SQL (Python ile)
```python
from app.db import database
c = database.get_connection()
print(c.execute("""SELECT COUNT(*) FROM messages m JOIN conversations cv ON cv.id=m.conversation_id
                   WHERE m.role='user' AND cv.user_id=? AND m.created_at >= date('now','-29 days')""", (1,)).fetchone()[0])
```
Bu sayı, `scope=me`, 30 gün raporundaki "Soru (dönem)" ile aynı olmalı (UTC gün sınırı: rapor UTC tarihiyle çalışır).

### Tasarım kararları (yanıltıcı görsel ve eksik veri)
- **Boş günler 0 olarak doldurulur.** Aksi halde grafik, soru sorulmayan günleri atlayıp eğilimi çarpıtırdı.
- **Veri yoksa oran `None` (grafikte "—"), 0 değil.** "Hiç yanıt yok" ile "tüm yanıtlar başarısız" farklı şeylerdir.
- **Eski (migration öncesi) mesajlar** `status` boş olduğundan "Bilinmiyor" grubunda sayılır, sessizce atlanmaz.
- **Gizlilik:** Raporlar yalnızca **sayı** içerir, sohbet metni içermez. `scope=all` yalnızca yöneticiye açıktır ve **sunucuda** kontrol edilir (403).
- **CSV formül enjeksiyonu:** Dosya adı `=HYPERLINK(...)` gibi başlarsa Excel bunu formül sanıp çalıştırabilir. `=`, `+`, `-`, `@` ile başlayan hücrelerin başına `'` konur (testle doğrulandı). CSV `UTF-8 BOM` ile yazılır (Excel'de Türkçe karakterler için).
- **Grafik erişilebilirliği:** çubukların `title`/`aria-label` metni var; renk tek başına anlam taşımaz (sayılar yazılı).
- **Bildirim/zamanlama:** yapılmadı. Neden: PDF'te "varsa" (isteğe bağlı); zamanlanmış iş (cron/arka plan işleyici) ek altyapı ve test yükü getirir, projenin çekirdek hedefine katkısı sınırlı.

### Yönetim (yalnızca yönetici)
`DELETE /admin/users/{id}`: kullanıcıyı siler; belge dosyalarını **diskten de** siler (sadece veritabanı kaydını silmek, yetim dosya bırakırdı); veritabanındaki belge, parça, vektör, sohbet, mesaj CASCADE ile gider; yönetici kendi hesabını silemez.

### Sözlü sınav soruları ve cevap iskeleti
**1) En çok kullanılan kaynağı nasıl buldun?** `message_sources`'ı `messages`, `chunks`, `documents` ile birleştirip belgeye göre grupladım; bir yanıtı birden çok parça için tekrar saymamak için `COUNT(DISTINCT yanıt_id)` kullandım, en çoktan aza sıraladım.
**2) Kalite metriğini nasıl izledin?** Her yanıtın durumunu (`answered / no_context / no_info / unverified`), kaynağa dayalı olup olmadığını, süresini ve en iyi skorunu mesajla birlikte kaydettim; rapor bunları toplulaştırıyor.
**3) Hangi metrikleri neden seçtim?** Kullanım (soru sayısı), güvenilirlik (kaynağa dayalı oran), kapsam boşluğu (yanıtsız oran), performans (süre), arama kalitesi (en iyi skor), hangi belgenin işe yaradığı (kaynak sıralaması).
**4) Görseli hangi veriden ürettim?** `/reports/usage` JSON'undan: `daily` (günlük soru), `period.by_status`, `top_sources`. Arayüz sayıları kendisi hesaplamaz, sunucunun verdiğini çizer.
**5) Yanlış/eksik veri sonucu nasıl etkiler?** Eksik gün → eğilim çarpıtılır (0 ile doldurdum); veri yokken oran 0 gösterilirse yanıltır (None/"—" gösterdim); eski mesajların durumu boşsa sessizce kaybolur (Bilinmiyor grubu); `grounded` doğruluk değildir (sınırı açıkça yazdım).

### Deneyim (kendi gözlemini yaz)
- Elle SQL ile doğruladığım sayılar:
- Raporda yanıltıcı bulduğum durum ve yorumum:

### Sık yapılan hatalar
Yanıltıcı görsel · yanlış toplulaştırma (aynı yanıtı kaynak sayısı kadar saymak) · eksik veriyi göz ardı etmek · CSV'de formül enjeksiyonunu unutmak.

### Dürüst not
Rapor sorguları ve CSV, elle hesaplanmış beklenen sayılarla test edildi. Arayüz (`report.js`, `admin.js`) 2026-10-02'de tarayıcıda denendi: rapor, CSV ve yönetim sekmesi çalıştı, konsolda hata yoktu. Fark edilen küçük sorun (soru yokken grafik etiketi "en yüksek: 1") Hafta 13'te ele alınıyor.
