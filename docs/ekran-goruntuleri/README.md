# Ekran görüntüleri

Uygulamanın çalışır hâlinin kanıtı. Bütün veriler **sentetiktir** (`@example.com` hesapları, uydurma yönetmelik metinleri);
gerçek kişisel veri yok.

## Güncel sürüm (04.10.2026)
Yerelde çalıştırıldı: backend SQLite + yerel embedding modeli, sohbet yanıtları gerçek Groq API'sinden (`openai/gpt-oss-120b`).
Bu yüzden yükleme sınırı "500 MB" görünüyor; bulut sürümünde (Vercel + Supabase) bu sınır 50 MB.

| # | Ekran | Ne gösteriyor? |
|---|---|---|
| 1 | [Ana sayfa](01-ana-sayfa.jpg) | Giriş yapmamış kullanıcının gördüğü tanıtım sayfası (koyu tema) |
| 2 | [Giriş penceresi](02-giris.jpg) | E-posta + parola ile giriş, "Şifremi unuttum", kayıt bağlantısı |
| 3 | [Belgelerim](03-belgelerim.jpg) | Belge yükleme alanı, yüklenen 3 belge, durum (hazır), parça sayısı |
| 4 | [Sohbet](04-sohbet.jpg) | Kaynaklı yanıtlar (`[1]` + belge adı + benzerlik); belgede olmayan soruya etiketli genel yanıt |
| 5 | [Arama](05-arama.jpg) | Vektör araması: en yakın parçalar benzerlik puanına göre sıralı |
| 6 | [Rapor](06-rapor.jpg) | Kullanım ve kaynak raporu: soru sayısı, kaynağa dayalı yanıt oranı, en çok kaynak gösterilen belge, günlük grafik |
| 7 | [Hesabım](07-hesabim.jpg) | Ad soyad, parola değiştirme, API anahtarları |
| 8 | [Yönetim](08-yonetim.jpg) | Yalnızca yöneticinin gördüğü kullanıcı ve belge listesi (rol tabanlı erişim) |
| 9 | [Açık tema](09-acik-tema.jpg) | Aynı Belgelerim ekranı açık temada |
| 10 | [Mobil sohbet](10-mobil-sohbet.jpg) | 375 px genişlikte (telefon) sohbet ekranı |

## İlk sürüm (02.10.2026)
Projenin ilk gerçek ortam denemesinden (vize kapsamındaki modüller, eski tema).

| Ekran | Ne gösteriyor? |
|---|---|
| [Belgelerim](ilk-surum/01-belgelerim.jpg) | Yüklenen TXT ve PDF belgeler, parça sayıları |
| [Arama](ilk-surum/02-arama.jpg) | "Kütüphane pazar günü açık mı?" sorgusunun benzerlik sıralı sonuçları |
