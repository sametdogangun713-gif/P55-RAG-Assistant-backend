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
| Gizli anahtarlar | `.env` (git'e girmez), örnek: `.env.example` |

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

## Bilinen sınırlar (dürüst not)
- Kilit sayacı bellekte tutulur: sunucu yeniden başlarsa ve birden çok süreç çalışırsa sıfırlanır/paylaşılmaz.
- Token iptali yok (çıkış yapınca token sunucuda geçersiz kılınmaz, süresi dolana kadar geçerli).
  Bu yüzden süre kısa tutuldu. Kullanıcı silinirse token zaten reddedilir (kullanıcı DB'den okunur).
- Üretimde HTTPS zorunludur; token açık HTTP üzerinden gönderilmemeli.

## Kendi notlarım (doldur)
-
