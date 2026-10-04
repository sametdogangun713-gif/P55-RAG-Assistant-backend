# Adım 7 — Harici LLM API istemcisi

> Ders planındaki karşılığı: **Hafta 9**. Bu belge eski `hafta-09/README.md` ve `hafta-09/aciklama.md` dosyalarının birleşimidir.

## Ne yapıldı

### Amaç
Gömme ve vektör arama servislerini, harici bir yapay zekâ API'siyle (Claude) birlikte güvenli ve hataya dayanıklı biçimde entegre etmek.

### Tasarım kararı (PDF: "Embedding API / Vektör DB")
- **Embedding:** yerel ücretsiz model (Hafta 7). `Embedder` arayüzü sayesinde ileride bir embedding API'sine geçmek, yalnızca yeni bir sınıf yazmak demektir.
- **Vektör saklama:** SQLite BLOB + numpy (ayrı bir vektör veritabanı yok; bu ölçekte yeterli). Büyürse pgvector/FAISS/sqlite-vec seçenekleri bu belgenin "Kod açıklaması" bölümü'de.
- **Harici API:** Anthropic **Claude Messages API** (yanıt üretimi, Hafta 10'da RAG'de kullanılacak).
- **Ücretsiz seçenek:** **Groq** (OpenAI uyumlu API, ücretsiz katmanı var). Hangisinin kullanılacağını `.env`'deki `LLM_PROVIDER=claude|groq` seçer; kodun geri kalanı farkı bilmez.

### Bu hafta eklenen / değişen dosyalar
| Dosya | Ne işe yarıyor |
|---|---|
| `app/services/llm_client.py` | LLM REST istemcileri: ortak taban sınıf (zaman aşımı, yeniden deneme, hata sınıfları) + `ClaudeClient` + `GroqClient` + `get_llm_client()` (sağlayıcı seçimi) |
| `app/api/errors.py` | LLM hatalarını HTTP kodlarına çevirir (503/504/429/502) |
| `app/api/admin.py` | `POST /admin/llm-test` (yalnız yönetici) — bağlantı denemesi |
| `app/api/deps.py` | `get_llm` bağımlılığı (`LLM_PROVIDER`'a göre istemci; yanlış değer → 503) |
| `app/services/vector_search.py` | Vektör matrisini daha hızlı kurma (ölçümlü) |
| `scripts/benchmark_search.py` | Arama hızı ölçümü |
| `app/core/config.py`, `scripts/env_olustur.py` | `LLM_PROVIDER`, `ANTHROPIC_API_KEY` / `GROQ_API_KEY` (boş), modeller, zaman aşımı, deneme sayısı |
| `tests/test_groq.py` | Groq istek biçimi, yanıt ayrıştırma, sağlayıcı seçimi testleri |

### API anahtarı kurulumu (ÖNEMLİ)
1. Anahtarı al: Groq için https://console.groq.com/keys (ücretsiz), Claude için Anthropic Console (ücretli).
2. **Yalnızca** `.env` dosyasına yaz: `LLM_PROVIDER=groq` ve `GROQ_API_KEY=...` (ya da `LLM_PROVIDER=claude` ve `ANTHROPIC_API_KEY=...`). `.env` git'e girmez; `scripts/env_olustur.py` şablonunda anahtarlar **boş** kalır.
3. Anahtarı asla sohbete, koda, ekran görüntüsüne, commit mesajına yazma. Yanlışlıkla GitHub'a gittiyse hemen Console'dan **iptal et ve yenisini üret** (geçmişten silmek yetmez).

### Çalıştırma ve demo
```bat
python -m scripts.create_admin
uvicorn app.main:app --reload
```
Swagger'da (`/docs`): yönetici olarak `POST /auth/login` → token → `POST /admin/llm-test` (`authorization: Bearer ...`).
Başarılıysa seçili modelin yanıtı ve model adı gelir. `.env`'den anahtarı silip tekrar dene → **503** ve anlaşılır mesaj (hata yönetimi demosu).
Arama hızı: `python -m scripts.benchmark_search`

Testler: `pytest tests/test_llm.py tests/test_groq.py` (gerçek bir yerel sahte API sunucusuna karşı çalışır; internet ve anahtar gerekmez)

### Kendi yapacakların
1. Claude API çağrısını **önce kendin** `curl` ile dene (dokümantasyondan başlık ve gövdeyi çıkar), sonra `llm_client.py` ile karşılaştır. Fark var mı?
2. Testlere yeni bir hata senaryosu ekle (örn. 400 "geçersiz istek" → yeniden denenmemeli).
3. `scripts/benchmark_search.py`'yi kendi bilgisayarında çalıştır; sonuçlarını bu belgenin "Kod açıklaması" bölümü'deki tabloyla karşılaştır.
4. Anahtarın depoda olmadığını doğrula: `git grep -n "sk-"`, `git grep -n "gsk_"`, `git grep -n "hf_"`, `git grep -n "sb_secret_"` (sonuçlar boş olmalı; iki depoda da).
5. `docs/ai-kullanim-gunlugu.md` boş alanlarını doldur.

### Kontrol listesi
- [ ] API anahtarı depoda değil (`git grep` boş, `.env` ignore'da)
- [x] Hatalar yönetiliyor (zaman aşımı, 429, 5xx, bağlantı hatası, bozuk yanıt)
- [x] Entegrasyon doğru çalışıyor (`/admin/llm-test`, kendi seçtiğin sağlayıcıyla)

## Kod açıklaması

### Claude API çağrısı nasıl çalışıyor? (REST)
`POST https://api.anthropic.com/v1/messages` — başlıklar: `x-api-key` (anahtar), `anthropic-version: 2023-06-01`, `content-type: application/json`.
Gövde (JSON): `model`, `max_tokens`, `system` (sistem istemi), `messages` (`[{"role":"user","content":"..."}]`).
Yanıt (JSON): `content` bir **blok listesidir**; metin bloklarının `type == "text"` olanlarının `text` alanı birleştirilir.
Neden `requests`/SDK değil de `urllib`? Ek bağımlılık yok, tüm HTTP ayrıntısı (başlık, gövde, hata kodu) görünür; REST'i sözlüde anlatması kolay.
(İstersen resmi `anthropic` SDK'sına geçilebilir; mantık aynıdır.)

### `llm_client.ClaudeClient.complete`
1. **Anahtar yoksa** ağ çağrısı yapmadan `LLMConfigError` (testte kanıtlandı).
2. `_validate`: mesajlar boş olamaz, roller `user/assistant`, ilk mesaj `user` (API kuralı).
3. `_post_with_retry`: şu hata türlerinde şöyle davranır:

| Durum | Davranış |
|---|---|
| 200 | Yanıtı ayrıştır |
| 429 / 500 / 502 / 503 / 504 / 529 (geçici) | Üstel geri çekilmeyle yeniden dene (1 s, 2 s, 4 s…, en fazla 8 s); `Retry-After` başlığı varsa ona uy. Denemeler biterse 429 → `LLMRateLimitError`, diğerleri → `LLMAPIError` |
| 400 / 401 / 403 / 404 (kalıcı) | **Hemen** `LLMAPIError` (yeniden denemek anlamsız) |
| Zaman aşımı | Yeniden dene; biterse `LLMTimeoutError` |
| Bağlantı kurulamadı | Yeniden dene; biterse `LLMAPIError("bağlanılamadı")` |
| Bozuk/boş yanıt | `LLMAPIError` |

4. **Anahtar hata mesajlarına asla yazılmaz** (başlıklar loglanmaz/yansıtılmaz; testle denetlendi).
5. `timeout`: yanıt gelmezse isteği sonsuza kadar bekleyip sunucuyu kilitlemeyiz.

### Neden "geri çekilme" (backoff)?
Sunucu yoğunken hemen tekrar denemek yükü artırır. Bekleme süresini katlayarak artırmak hem sunucuya nefes aldırır hem de geçici hataların geçmesine zaman tanır.

### Groq desteği: aynı arayüz, farklı istek biçimi
Claude ücretli olduğu için ücretsiz katmanı olan **Groq** da eklendi. Groq, OpenAI'nin "Chat Completions" biçimini kullanır:
`POST https://api.groq.com/openai/v1/chat/completions`.

| | Claude | Groq |
|---|---|---|
| Anahtar başlığı | `x-api-key: ...` | `Authorization: Bearer ...` |
| Sistem istemi | ayrı `system` alanı | listenin başına `{"role": "system", ...}` mesajı |
| Yanıt metni | `content[]` içindeki `type=="text"` blokları | `choices[0].message.content` |
| Kullanım | `usage.input_tokens / output_tokens` | `usage.prompt_tokens / completion_tokens` (Claude adlarına çevrilir) |

**Kod nasıl düzenlendi?** Yeniden deneme, zaman aşımı, hata çevirme ve mesaj doğrulama iki sağlayıcıda **aynı**; bu yüzden ortak bir taban sınıfa (`_HTTPLLMClient`) taşındı. `ClaudeClient` ve `GroqClient` yalnızca farklı olan üç şeyi tanımlar: `_payload` (gövde), `_request` (adres + başlıklar), `_extract` (yanıttan metni çıkarma). Kod tekrarı yok; yeni bir sağlayıcı eklemek = yeni bir küçük alt sınıf.
`get_llm_client()` `.env`'deki `LLM_PROVIDER` değerine bakıp doğru sınıfı oluşturur; API uçları ve RAG kodu hangi sağlayıcının kullanıldığını bilmez (yalnızca `.complete(...)` çağırır).
Ayrıca istekte kendi `User-Agent` başlığımızı gönderiyoruz: bazı API'ler `urllib`'in varsayılan "Python-urllib" kimliğini engelleyebiliyor.

### API katmanı
`errors.llm_http_error`: `LLMConfigError`→503 (ayar eksik), `LLMTimeoutError`→504, `LLMRateLimitError`→429, diğer→502 (kötü ağ geçidi).
Kullanıcıya teknik ayrıntı değil anlaşılır mesaj gider. `/admin/llm-test` yalnızca yönetici içindir (maliyet ve kötüye kullanım kontrolü).

### Vektörleri nerede sakladım, arama yavaşsa ne yaptım?
Vektörler SQLite `embeddings.vector` BLOB'unda (`float32` ham bayt). **Ölçüm** (bu ortamda, 384 boyut; senin makinende farklı çıkar — `python -m scripts.benchmark_search`):

| Parça sayısı | Toplam arama |
|---|---|
| 1.000 | ≈ 2,5 ms |
| 10.000 | ≈ 54 ms |
| 50.000 | ≈ 232 ms |

50.000 parçada dökümü: **SQL'den vektörleri okuma ≈ 150 ms**, BLOB'ları matrise çevirme ≈ 39 ms (eski `np.vstack` yöntemi ≈ 68 ms), matris×sorgu çarpımı ≈ 6,6 ms.
**Sonuç:** darboğaz matematik değil, veriyi okumak/kopyalamak. Yaptığım iyileştirme: satır satır `vstack` yerine tek `frombuffer` (10 bin parçada ≈ 4 kat, 50 bin parçada ≈ 1,7 kat hızlı).
Daha da büyürse sıradaki adımlar (yapılmadı, nedenleriyle): kullanıcı başına matrisi bellekte **önbelleğe almak** (belge ekle/sil'de geçersiz kılmak gerekir), yaklaşık en yakın komşu indeksi (FAISS/sqlite-vec/pgvector). Bu proje ölçeğinde (yüzlerce–binlerce parça) gereksiz karmaşıklık.

### Sözlü sınav soruları ve cevap iskeleti
**1) Vektörleri nerede sakladın?** SQLite'ta `embeddings` tablosunda `float32` BLOB olarak; `chunk_id` ile parçaya, `model` ile üreten modele bağlı. Ayrı vektör veritabanı kullanmadım çünkü ölçek küçük ve tek dosyalı kurulum işimi basitleştiriyor.
**2) Arama yavaşsa ne yaptın?** Önce ölçtüm (benchmark): maliyet SQL okuma ve matris kurmadaydı, çarpım değil. Matris kurmayı hızlandırdım; daha büyük ölçekte önbellek veya ANN indeksi planlıyorum.
**3) API anahtarını nasıl ve nerede sakladın?** Ortam değişkeni olarak `.env` dosyasında; `.env` `.gitignore`'da, depodaki şablonda değer boş. Koda gömülü değil, hata mesajına/loga yazılmıyor. Sızarsa iptal edip yenisini üretirim.
**4) API çağrısı başarısızsa ne oluyor?** Geçici hatada (429/5xx/zaman aşımı) üstel geri çekilmeyle yeniden denenir; kalıcı hatada hemen anlaşılır bir istisna fırlar; API katmanı bunu 503/504/429/502'ye çevirir; kullanıcı anlaşılır mesaj görür, sistem çökmez.
**5) Yanıtı nasıl ayrıştırdın?** JSON'u çözüp `content` blok listesinden `type == "text"` bloklarını birleştiriyorum (Groq'ta `choices[0].message.content`); bozuk JSON, eksik alan ya da boş metin `LLMAPIError` olur.
**Ek) Neden iki sağlayıcı, kodu nasıl ayırdın?** Claude ücretli, Groq'un ücretsiz katmanı var. Ortak işler (yeniden deneme, hata yönetimi) taban sınıfta; farklı olan istek/yanıt biçimi alt sınıflarda. `.env`'deki `LLM_PROVIDER` ile kod değiştirmeden geçiş yapılır.

### Sık yapılan hatalar
Anahtarı koda gömmek · hataları yakalamamak · zaman aşımı koymamak · her hatayı körlemesine yeniden denemek (kalıcı hatalar) · anahtarı hata mesajında göstermek.

### Dürüst not
`llm_client.py`'yi burada gerçek bir yerel sahte API sunucusuna karşı test ettim (başarı, 429/5xx yeniden deneme, 401, zaman aşımı, bağlantı hatası, bozuk yanıt).
**Gerçek Claude API'sine bu ortamdan çağrı yapamadım** (ağ ve anahtar yok); `/admin/llm-test` ile kendi bilgisayarında bir kez denemen gerekir. Model adı (`CLAUDE_MODEL`) `.env`'den değiştirilebilir.
Groq istemcisi de aynı yerel sahte sunucuyla test edildi (`test_groq.py`); varsayılan model `openai/gpt-oss-120b`. İlk gerçek denemede (2026-10-03) önceki varsayılan `llama-3.3-70b-versatile` **404** döndü: Groq Llama modellerini kaldırmış. Hesaba açık modeller API'den (`GET /models`) listelenip `gpt-oss-120b` seçildi. Bu model "düşünen" bir model olduğu için `GROQ_REASONING_EFFORT=low` gönderilir (düşünme kısa, yanıt hızlı); yanıta `<think>` etiketiyle düşünce karışırsa temizlenir (qwen gibi modeller için). Yeni anahtarla **gerçek çağrılar başarılı** (2026-10-03): Türkçe yanıt 0,5–2,6 sn'de geldi; `gpt-oss-120b`, `gpt-oss-20b` ve `qwen3.8-27b` karşılaştırıldı (ayrıntı: `docs/istem-deneyleri.md`).
