# Kısa güvenlik notu

| Konu | Bu projede nasıl çözüldü |
|---|---|
| Parola saklama | Düz metin yok; `scrypt` + kullanıcıya özel rastgele tuz (`app/core/security.py`) |
| Oturum | İmzalı JWT (HS256), süreli (`ACCESS_TOKEN_EXPIRE_MINUTES`); imza anahtarı `.env`'de (`SECRET_KEY`) |
| Yetkilendirme | Sunucuda: `get_current_user` kullanıcıyı ve **rolü veritabanından** okur, `require_admin` rolü denetler |
| Kullanıcı numaralandırma | Giriş hatası genel: "E-posta veya parola hatalı" |
| Kaba kuvvet | 5 başarısız denemede 5 dk geçici kilit (bellekte sayaç) |
| SQL enjeksiyonu | Tüm sorgular parametreli (`?`) |
| Yönetici hesabı | Kendi kendine kayıtla yönetici olunamaz; `python -m scripts.create_admin` |
| Gizli anahtarlar | `.env` (git'e girmez); boş şablon `scripts/env_olustur.py` içinde, depoya gerçek değer girmez |

## Bulut (Supabase + Vercel) için ek önlemler
| Konu | Önlem |
|---|---|
| Gizli değerler | Yerelde `.env` (git'e girmez), bulutta Vercel ortam değişkenleri. `.vercelignore` CLI ile yüklemede de `.env`'i dışarıda tutar. Frontend deposunda hiç gizli değer yok (arayüz testi tarar) |
| Supabase gizli anahtarı | Veritabanına ve depoya tam erişim verir: yalnızca backend'de. Tarayıcıya hiç gitmez |
| Supabase REST API | Tüm tablolarda Row Level Security açık, politika yok → Supabase'in otomatik API'si tablolara erişemez; uygulama tablo sahibi olarak bağlanır |
| Dosya deposu | Gizli kova; tarayıcı yalnızca backend'in ürettiği tek kullanımlık imzalı adrese yükler. Yol `kullanıcı-no/rastgele.uzantı`; başkasının klasöründeki yol reddedilir. Tür ve boyut, depodaki **gerçek** dosyayla yeniden kontrol edilir |
| Oturum token'ı | Yalnızca kendi backend'imize gider; Supabase'e giden yükleme isteğinde gönderilmez |
| CORS | Backend yalnızca `ALLOWED_ORIGINS`'teki arayüz adreslerine izin verir |
| Üretim ayarı | `APP_ENV=production` iken zayıf/varsayılan `SECRET_KEY` ile uygulama açılmaz; SMTP yoksa şifre sıfırlama kapalı (503) |
| Veri konumu (KVKK) | Supabase ve Vercel bölgesi Frankfurt (AB). Demo verisi yine sentetik |

## Kişisel API anahtarları (3. parti uygulamalar)
- Anahtar `p55_` + 32 rastgele bayt (`secrets`). Veritabanında yalnızca **SHA-256 özeti** saklanır; anahtar yalnızca
  üretildiği yanıtta bir kez gösterilir. Parolada yavaş scrypt kullanılır çünkü parolalar kısa ve tahmin edilebilir;
  256 bitlik rastgele anahtarda kaba kuvvet imkânsız olduğu için hızlı özet yeterlidir (her istekte çalışır).
- Her anahtarın son kullanma tarihi var (en fazla 1 yıl), tek tek silinebilir; silinen/süresi dolan anahtar 401 alır.
- Anahtarla **yapılamayanlar** (403): yeni anahtar üretme/listeleme/silme, ad ve parola değiştirme, hesap silme,
  yönetim işlemleri. Sızan bir anahtar kendini kalıcı hale getiremez ve hesabı ele geçiremez.
- Anahtar oluşturulunca hesap sahibine **bildirim e-postası** gider (ad + ilk 12 karakter; anahtarın kendisi e-postada
  yok). Parolası ele geçirilip anahtar üretilirse sahibi haberdar olur.
- **Yönetici** tüm anahtarları sahibiyle görür (ilk 12 karakter, tarihler) ve sızan anahtarı iptal eder; sahibine
  e-posta gider. Yönetici anahtar **üretemez** ve anahtarın kendisini göremez: hesaba yalnızca anahtarı oluşturan girer.
  (Kullanıcının haberi olmadan onun adına anahtar üretmek bilerek eklenmedi: bu bir arka kapı olurdu.)
- Tarayıcıdan çalışan bir 3. parti site, CORS yüzünden ancak `ALLOWED_ORIGINS`'e eklenirse bağlanabilir; sunucudan
  çalışan uygulamalar (Postman, Python betiği, bot) CORS'tan etkilenmez. Anahtar tarayıcı koduna gömülmemeli.

## Bilinen sınırlar (dürüst not)
- Kilit sayacı bellekte tutulur: sunucu yeniden başlarsa ve birden çok süreç çalışırsa sıfırlanır/paylaşılmaz.
- Token iptali yok (çıkış yapınca token sunucuda geçersiz kılınmaz, süresi dolana kadar geçerli).
  Bu yüzden süre kısa tutuldu. Kullanıcı silinirse token zaten reddedilir (kullanıcı DB'den okunur).
- Üretimde HTTPS zorunludur; token açık HTTP üzerinden gönderilmemeli.
- API anahtarı için istek sayısı sınırı (rate limit) yok; parola değişince anahtarlar iptal edilmez (ayrı silinir).

## Kendi notlarım (doldur)
-
