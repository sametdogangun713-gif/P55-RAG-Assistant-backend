# Adım 3 — Kimlik doğrulama ve roller

> Ders planındaki karşılığı: **Hafta 5**. Bu belge eski `hafta-05/README.md` ve `hafta-05/aciklama.md` dosyalarının birleşimidir.

## Ne yapıldı

### Amaç
Kayıt, giriş ve rol tabanlı erişim ile kullanıcı yönetimini kurmak.

### Bu hafta eklenen / değişen dosyalar
| Dosya | Ne işe yarıyor |
|---|---|
| `app/core/security.py` | Parola hash (scrypt + tuz), JWT üretme/doğrulama |
| `app/services/auth.py` | Kayıt/giriş iş kuralları, başarısız giriş kilidi |
| `app/api/deps.py` | `get_db`, `get_current_user`, `require_admin` |
| `app/api/auth.py` | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| `app/api/admin.py` | `GET /admin/users` (yalnız yönetici) |
| `scripts/create_admin.py` | Yönetici hesabı oluşturma |
| `docs/guvenlik-notu.md` | Kısa güvenlik notu (teslim edilecek çıktı) |
| `app/core/config.py`, `requirements.txt` | `SECRET_KEY`, token süresi, PyJWT |

### Çalıştırma ve demo
```bat
pip install -r requirements.txt
python -m scripts.env_olustur
:: .env oluşur ve SECRET_KEY rastgele üretilir (secrets.token_hex(32))
python -m scripts.create_admin
uvicorn app.main:app --reload
```
`http://127.0.0.1:8000/docs` (Swagger) üzerinden:
1. `POST /auth/register` → kullanıcı oluştur
2. `POST /auth/login` → cevaptaki `access_token` değerini kopyala
3. `GET /auth/me` → **Try it out** → `authorization` alanına `Bearer ` + token yaz (araya boşluk) → **Execute**
Aynısını komut satırından da deneyebilirsin:
```bat
curl http://127.0.0.1:8000/auth/me -H "Authorization: Bearer TOKEN_BURAYA"
curl http://127.0.0.1:8000/admin/users -H "Authorization: Bearer NORMAL_KULLANICI_TOKENI"
```
İkinci komut normal kullanıcıda **403** döner; yönetici token'ı ile liste gelir. Token'sız istek **401** döner.

Testler: `pytest tests/test_kimlik.py`

### Kendi yapacakların
1. `hash_password` / `verify_password` fonksiyonlarını kendi cümlelerinle yeniden yaz (örn. `hashlib.pbkdf2_hmac` ile) ve testleri geçir. Neden bu parametreleri seçtiğini açıkla.
2. `PATCH /admin/users/{id}/role` uç noktasını kendin yaz (`require_admin` ile korunsun) ve bir test ekle.
3. `docs/guvenlik-notu.md` "Kendi notlarım" bölümünü doldur.
4. `docs/ai-kullanim-gunlugu.md` boş alanlarını doldur.

### Kontrol listesi
- [x] Parola düz metin saklanmıyor
- [x] Yetkisiz erişim engelleniyor (401/403)
- [x] Oturum/token doğru yönetiliyor (süre, imza)

## Kod açıklaması

### Akış (giriş yapan bir kullanıcının isteği)
1. `POST /auth/login` → `services/auth.login` e-postayı normalize eder, kilit durumuna bakar, kullanıcıyı bulur, parolayı `verify_password` ile doğrular.
2. Başarılıysa `create_access_token` imzalı bir JWT üretir: `sub` (kullanıcı id), `role`, `iat`, `exp`.
3. İstemci sonraki isteklerde `Authorization: Bearer <token>` başlığı gönderir.
4. `deps.get_current_user` başlığı ayrıştırır, `decode_access_token` ile imza + süre doğrular, kullanıcıyı **DB'den** okur.
5. Yönetici uçları ayrıca `require_admin` kullanır → rol `admin` değilse 403.

### Dosya dosya
**`security.hash_password`** — `os.urandom(16)` ile rastgele tuz; `hashlib.scrypt(parola, salt, n, r, p)` yavaş, bellek-yoğun bir türetme fonksiyonudur.
Sonuç `scrypt$n$r$p$tuz$hash` olarak saklanır; parametreler de saklandığı için ileride güçlendirilebilir.
**`verify_password`** — Aynı tuz ve parametrelerle hash'i yeniden hesaplar, `hmac.compare_digest` ile **sabit zamanlı** karşılaştırır
(karakter karakter erken çıkış yapan `==` zamanlama saldırısına açıktır).

**`create_access_token / decode_access_token`** — PyJWT, HS256 (HMAC-SHA256) ile imzalar. `decode` içinde `algorithms=["HS256"]` sabit:
saldırgan `alg: none` göndererek imzayı atlatamaz (testte denendi). `require: ["exp","sub"]` süresiz token'ı reddeder.

**`services/auth.py`** — E-posta regex ve uzunluk kontrolü, parola kuralı (≥8, harf+rakam), kayıtta e-posta küçük harfe çevrilir.
`login` hatası her durumda aynı: *"E-posta veya parola hatalı"*. Kullanıcı yoksa bile sahte bir hash doğrulanır (`_DUMMY_HASH`) → yanıt süresi farkı bilgi sızdırmaz.
Başarısız giriş sayacı: 5 denemeden sonra 5 dk kilit (429).

**`api/deps.py`** — `get_db` istek başına bağlantı açıp kapatır. `get_current_user` 401'leri üretir. `require_admin` 403 üretir.
**Rol token'dan değil veritabanından okunur**: rol değişirse hemen geçerli olur; token içindeki `role` iddiası yetki vermez (testte kanıtlandı).

### Oturum (session) ve token farkı
- **Oturum:** sunucu bir oturum kaydı tutar, istemci yalnızca oturum kimliğini (çerez) taşır. Sunucu durum saklar, iptali kolay.
- **Token (JWT):** bilgi + imza istemcide durur, sunucu durum tutmaz; ölçeklenmesi kolay ama iptali zordur (süre dolana kadar geçerli).
Burada JWT seçtim: API tabanlı, durumsuz; süreyi kısa tuttum (60 dk).

### Sözlü sınav soruları ve cevap iskeleti
**1) Parolayı neden hash'liyoruz, tuz (salt) nedir?**
Veritabanı sızarsa parolalar okunamasın diye. Hash tek yönlüdür. Tuz, her parolaya eklenen rastgele değerdir: aynı parola farklı hash üretir, hazır "gökkuşağı tablosu" işe yaramaz.
scrypt bilerek yavaştır; milyarlarca deneme pahalı olur.

**2) Oturum ve token farkı nedir?** → yukarıdaki bölüm.

**3) Rol tabanlı erişimi nasıl uyguladın?**
`users.role` ('user'/'admin', DB'de CHECK ile sınırlı). `require_admin` bağımlılığı kullanıcının rolünü DB'den okuyup 403 döner. Yönetici uçları (`/admin/...`) bu bağımlılıkla korunur; yönetici hesabı yalnızca `create_admin` betiğiyle açılır.

**4) Başarısız giriş denemesinde ne oluyor?**
401 ve genel hata mesajı; sayaç artar; 5. başarısız denemeden sonra 5 dakika boyunca doğru parola bile 429 ile reddedilir. Başarılı girişte sayaç sıfırlanır.

**5) Yetkisiz kullanıcı korumalı sayfaya giderse ne olur?**
Token yoksa/bozuksa/süresi dolmuşsa 401. Token geçerli ama rol yetersizse 403. Kontrol **sunucuda** yapılır; arayüzde bir düğmeyi gizlemek tek başına koruma sayılmaz.

### Sık yapılan hatalar
Parolayı düz metin saklamak · yetkiyi yalnızca arayüzde kontrol etmek · oturum süresini yönetmemek · `SECRET_KEY`'i koda gömmek (burada `.env`'den okunuyor; varsayılan `degistir-bunu` yalnızca yerel geliştirme için).
