# Kısa ilerleme raporu - Vize (Hafta 8)

Öğrenci: Samet DOĞANGÜN · Proje: P55 - Belge Tabanlı Soru-Cevap Asistanı (RAG)

## Tamamlanan haftalar
| Hafta | Modül | Durum |
|---|---|---|
| 3 | Kurulum, mimari, ER diyagramı, GitHub deposu | Tamam |
| 4 | SQLite şeması (migration), CRUD veri erişim katmanı, sentetik veri | Tamam |
| 5 | Kayıt/giriş, scrypt parola hash, JWT, rol tabanlı erişim | Tamam |
| 6 | Belge yükleme, TXT/PDF/DOCX ayrıştırma, parçalama | Tamam |
| 7 | Embedding, vektör saklama, benzerlik arama | Tamam |
| 8 | Entegrasyon, web arayüzü (giriş, belge, arama), uçtan uca test | Tamam |

## Çalışan ara sürüm
Kullanıcı kaydı/girişi → belge yükleme → otomatik parçalama ve vektörleştirme → anlamsal arama; kullanıcıya özel veri; yönetici ucu.
Etiket: `v0.1-vize`.

## Bu hafta giderilen hatalar
- `.env.example` testi, adında `TOKEN` geçen her ayarı gizli sanıyordu (`ACCESS_TOKEN_EXPIRE_MINUTES` için yanlış alarm) → anahtarın **son ekine** bakacak şekilde düzeltildi.
- Kullanıcıya görünen hata mesajları ASCII/Türkçe karakterden yoksundu → düzgün Türkçe yapıldı.

## Bilinen sınırlar (dürüst liste)
- Başarısız giriş sayacı bellekte; sunucu yeniden başlarsa sıfırlanır.
- Token iptali yok (süre dolana kadar geçerli; süre kısa tutuldu).
- DOCX'te tablo metni paragraflardan sonra eklenir; PDF'te sayfayı bölen cümle iki parçaya ayrılır.
- Yükleme isteği, vektörleştirme bitene kadar bekler (büyük belgelerde yavaş olabilir).
- `hash` embedder anlamsal değil biçimsel benzerlik yakalar; gerçek kalite için `local` model gerekir.
- Arama henüz yanıt üretmiyor (LLM Hafta 9–10'da eklenecek).

## Sonraki adımlar
Hafta 9: Claude API entegrasyonu (hata yönetimi, zaman aşımı, yeniden deneme) · Hafta 10: kaynaklı yanıt (RAG) · Hafta 11: sohbet geçmişi · Hafta 12: kullanım raporu.

## Kendi değerlendirmem
- **En çok öğrendiğim şey:** Bir RAG sisteminin parçalarının (yükleme → parçalama → vektör → arama) birbirine nasıl bağlandığı ve her katmanın ayrı ayrı test edilebildiği. Yerel embedding modelinin, kelimeler birebir aynı olmasa da Türkçe soruyu doğru belgeyle eşleştirmesi.
- **En çok zorlandığım şey ve çözümüm:** Geliştirme ortamı: bilgisayarımda `python` komutu yoktu. Python 3.12 ve Git'i kurup sanal ortam (`venv`) oluşturarak çözdüm. İlk belge yüklemesinin 211 saniye sürmesi (model ilk kez iniyordu): demodan önce uygulamayı bir kez çalıştırıp modeli indirmem gerektiğini öğrendim.
- **Yapay zekâdan aldığım yardımın payı ve kendi katkım:** Yardımın payı yüksek: kodun büyük kısmı yapay zekâyla (Claude, AI Pair Programmer yaklaşımıyla) yazıldı ve bunu AI günlüklerinde açıkça belirttim. Teknoloji ve mimari kararları (Python + FastAPI, SQLite, yerel ücretsiz embedding, web arayüzü, haftalık klasör düzeni) benim kararlarımdı; her modül testler ve gerçek sunucu denemesiyle doğrulandı. Kendi geliştirdiğim bölümler her haftanın README → "Kendi yapacakların" kısmında.
