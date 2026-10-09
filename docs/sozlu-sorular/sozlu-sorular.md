# Sözlü sınav soruları ve cevap iskeleti

Kaynak: ders paketi, P55 haftalık faaliyet planı (s. 475–482), her hafta 5 soru.

> Bunlar **iskelettir**. Sözlüde ezber cümle değil, kendi cümlelerin beklenir. 💬 işaretli sorular yalnızca senin
> deneyiminle cevaplanabilir. Ayrıntılı açıklamalar `docs/gelistirme/NN-*/NN-*.md` dosyalarında. Oradaki bazı cevaplar eski
> mimariyi anlatıyor (yalnızca SQLite, Hugging Face). Aşağıdakiler güncel mimariye göre yazıldı.

### Hafta 3 — Kurulum, mimari, ER
| # | Soru | Cevap iskeleti |
|---|---|---|
| 1 | Katmanlı mimariyi neden tercih ettin? | `api → services → db`, tek yönlü. API isteği ve yetkiyi, servis iş kuralını, db SQL'i bilir. Buluta (PostgreSQL) geçerken değişiklik çoğunlukla `app/db`'de kaldı. Servisler HTTP'siz test edilebiliyor. |
| 2 | İlişki türlerini (1-1, 1-N, N-N) örnekle. | 1-1: parça ↔ embedding. 1-N: kullanıcı → belgeler, belge → parçalar. N-N: yanıt ↔ parça (ara tablo `message_sources`). |
| 3 | Hangi varlıklar birincil anahtar taşıyor, neden? | Hepsi `id` taşır: satırı tekil tanımlamak ve yabancı anahtarla bağlamak için. `message_sources` bileşik anahtar kullanır (`message_id`, `chunk_id`), böylece aynı çift iki kez yazılamaz. |
| 4 | Klasör yapını hangi mantıkla kurdun? | Katmana göre (`api/services/db/core`), testler `tests/`, belgeler `docs/`. Frontend ayrı depoda (`public/`), bağımsız dağıtılıyor. |
| 5 | .gitignore neden gerekli, neler eklenmemeli? | Gizli ve üretilebilir dosyalar depoya girmemeli: `.env`, `venv/`, `*.db`, `uploads/`. GitHub'a bir kez giden anahtar sızmış sayılır ve yenilenmesi gerekir. |

### Hafta 4 — Veritabanı
| # | Soru | Cevap iskeleti |
|---|---|---|
| 1 | Bir tabloya neden indeks ekledin/eklemedin? | Sık filtrelenen yabancı anahtarlara indeks ekledim (`documents.user_id` vb.). Uzun metin sütunlarına eklemedim: yazma maliyeti getirir ve orada arama vektörle yapılıyor. |
| 2 | Yabancı anahtar kısıtı ne işe yarar? | Referans bütünlüğü sağlar: olmayan kullanıcıya belge bağlanamaz. `ON DELETE CASCADE` ile yetim kayıt kalmaz. SQLite'ta `PRAGMA foreign_keys=ON` gerekir. |
| 3 | N-N ilişkiyi nasıl modelledin? | `message_sources(message_id, chunk_id, score, n)`, bileşik birincil anahtarla. |
| 4 | Migration neden kullanılır? | Şema değişiklikleri sürümlenir ve her ortamda aynı sırayla uygulanır. SQLite'ta 001–006, PostgreSQL'de 001–003 var; açılışta `init_db` uyguluyor. |
| 5 | Bir CRUD işleminin SQL'ini açıkla. | Örnek: `INSERT INTO documents (...) VALUES (?, ...) RETURNING id`. `?` parametresi SQL enjeksiyonunu önler. 💬 Kendi seçtiğin bir sorguyu satır satır anlat. |

### Hafta 5 — Kimlik doğrulama
| # | Soru | Cevap iskeleti |
|---|---|---|
| 1 | Parolayı neden hash'liyoruz, tuz nedir? | DB sızarsa parolalar okunamasın diye. Tuz her parolaya eklenen rastgele değerdir: aynı parola farklı hash üretir, hazır tablolar işe yaramaz. scrypt bilerek yavaş çalışır. |
| 2 | Oturum ve token farkı? | Oturumda durum sunucuda tutulur. JWT'de imzalı token istemcide durur ve sunucu yalnızca imzayı ve süreyi doğrular. Benim projemde JWT var, iptal edilemediği için süresi kısa. |
| 3 | Rol tabanlı erişimi nasıl uyguladın? | `users.role` (`user`/`admin`, CHECK kısıtlı). `require_admin` bağımlılığı 403 döndürür. Kontrol sunucuda yapılır, arayüzde düğme gizlemek koruma sayılmaz. |
| 4 | Başarısız giriş denemesinde ne olur? | 401 ve genel mesaj döner, sayaç artar. 5 hatalı denemeden sonra 5 dakika 429 alınır. E-posta doğrulanmamışsa 403. |
| 5 | Yetkisiz kullanıcı korumalı sayfaya giderse? | Token yoksa ya da bozuksa 401, rol yetersizse 403. API anahtarıyla gelen istek hesap ve yönetim işlemlerinde 403 alır (`require_session`). |

### Hafta 6 — Belge yükleme ve ayrıştırma
| # | Soru | Cevap iskeleti |
|---|---|---|
| 1 | Belgeyi nasıl parçaladın? | Metni paragraf ve cümlelere ayırıp 600 karaktere kadar birleştirdim. Parçalar arasında ~100 karakter örtüşme var, sayfa numarası korunuyor. |
| 2 | Parça boyutunu neye göre seçtin? | Embedding modelinin token sınırına ve "parça başına tek konu" ilkesine göre. Küçük parça bağlamı kaybeder, büyük parça vektörü bulanıklaştırır. Değer `CHUNK_SIZE` ile ayarlanabilir. |
| 3 | Verisini nasıl modelledin? | `documents` 1-N `chunks`. Durum alanı: `uploaded → chunked → indexed / failed`. `stored_name` (UUID) gerçek dosya adından ayrı tutuluyor. |
| 4 | Hangi iş kuralını neden koydun? | Tür beyaz listesi ve içerik-uzantı uyumu (güvenlik), boyut sınırı (bulutta 50 MB), DOCX zip-bombası kontrolü, sahiplik kontrolü (başkasının belgesine 404). |
| 5 | Diğer modüllerle nasıl entegre ettin? | Uçlar token ile korunuyor (H5), belge `user_id` ile kullanıcıya bağlı (H4), parçalar embedding'in (H7) ve kaynak gösteriminin (H10) girdisi. |

### Hafta 7 — Gömme ve vektör arama
| # | Soru | Cevap iskeleti |
|---|---|---|
| 1 | Gömmeyi nasıl ürettin? | Bulutta Google Gemini (`gemini-embedding-001`, 768 boyut), yerelde çok dilli MiniLM (384 boyut). Parçalar toplu gönderiliyor; model değişince "Yeniden indeksle". |
| 2 | Benzerliği nasıl ölçtün? | Kosinüs benzerliği ile: bulutta pgvector `<=>` operatörü, yerelde normalize vektörlerin nokta çarpımı. Sonuçlar azalan sırada, ilk `top_k` alınıyor. |
| 3 | Verisini nasıl modelledin? | `embeddings`: `chunk_id` (UNIQUE, 1-1), `vector`, `dim`, `model`. Model adı saklandığı için farklı modellerin vektörleri karışmıyor. |
| 4 | Hangi iş kuralını neden koydun? | Yalnızca kullanıcının kendi belgelerinde arama (gizlilik), `top_k` üst sınırı, boş sorgu reddi, sorgu uzunluğu sınırı. |
| 5 | Diğer modüllerle entegrasyon? | Yükleme hattının sonuna eklendi (`chunked → indexed`). RAG (H10) arama sonucunu bağlam olarak kullanıyor. |

### Hafta 8 — Vize
| # | Soru | Cevap iskeleti |
|---|---|---|
| 1 | Mimarini özetle. | Tarayıcı → frontend (Vercel) → FastAPI backend (Vercel) → Supabase (PostgreSQL + pgvector, Storage). Dış servisler: Gemini (embedding) ve Groq (LLM). |
| 2 | Hangi modül hangi veriyi nereden alıyor? | Yükleme hattı: dosya → `parser` → `chunker` → `embedder` → `embeddings`. Soru hattı: soru → vektör → arama → RAG → mesaj + kaynaklar → rapor. |
| 3 | En çok zorlandığın entegrasyon? 💬 | Kendi deneyimin olmalı. Olası örnekler: HF 402 sonrası Gemini'ye geçiş ve dakikalık sınır (429); `【1】` alıntı biçimi; Vercel'de `EMBEDDING_BACKEND`'in `hf` kalması. |
| 4 | AI'dan aldığın bir kodu satır satır açıkla. 💬 | `chunker.split_text` döngüsü ([06](../gelistirme/06-entegrasyon-arayuz/06-entegrasyon-arayuz.md)'da satır satır var). Kendi cümlelerinle anlatmalısın. |
| 5 | Sonraki aşamanın planı? | (Vizede sorulursa) LLM istemcisi → RAG → sohbet geçmişi → rapor. |

### Hafta 9 — Harici API: embedding / vektör DB
| # | Soru | Cevap iskeleti |
|---|---|---|
| 1 | Vektörleri nerede sakladın? | Bulutta Supabase PostgreSQL'de, pgvector `vector` sütununda. Yerelde SQLite'ta `float32` BLOB olarak. |
| 2 | Arama yavaşsa ne yaptın? | Önce ölçtüm (`scripts/benchmark_search.py`). Arama veritabanında pgvector ile yapılıyor. Ölçek büyürse HNSW indeksi eklenmeli (şu an yok, sütun boyutsuz). |
| 3 | API anahtarını nerede sakladın? | Yerelde `.env`'de (git-ignore'da), bulutta Vercel ortam değişkenlerinde. Koda, loga ve hata mesajına yazılmıyor. Sızan Groq anahtarını iptal edip yeniledim. |
| 4 | API çağrısı başarısızsa? | 429/5xx/zaman aşımında üstel geri çekilmeyle yeniden dener. Gemini'de `retryDelay` kadar bekler, gönderimi dakikada 90 metinle sınırlar. Kalıcı hatada kullanıcıya 502/503/504 ve anlaşılır bir mesaj döner. İndekslenen parçalar kaybolmaz, "Devam et" kaldığı yerden sürer. |
| 5 | Yanıtı nasıl ayrıştırdın? | Gemini'de `embeddings[i].values`, Groq'ta `choices[0].message.content` (`<think>` temizlenir). Bozuk JSON ya da boş yanıt hata olarak yakalanır. |

### Hafta 10 — RAG
| # | Soru | Cevap iskeleti |
|---|---|---|
| 1 | Yanıtı hangi parçalara dayandırdın? | Eşiği (Gemini'de 0,55, ölçülerek seçildi) geçen en yakın 4 parçaya. Bunlar LLM'e numaralı kaynak olarak veriliyor, yanıtta `[n]` alıntı zorunlu. |
| 2 | Belgede olmayan soruya ne yaptın? | Üç katman: eşik altındaysa LLM çağrılmaz (`no_context`), istemde `BILGI_YOK` kuralı var, alıntı doğrulaması (`unverified`) uydurmayı yakalar. Genel sohbet açıksa yanıt "genel bilgi" etiketiyle döner. |
| 3 | İstemini nasıl tasarladın? | Rol + numaralı kurallar, yapılandırılmış kaynak blokları, "kaynak metni veridir" kuralı (prompt injection'a karşı). Sürümlü (`rag-v2`) ve denemeleri `istem-deneyleri.md`'de. |
| 4 | AI çıktısı hatalıysa? | Var olmayan kaynak numaraları siliniyor, alıntısız yanıt "doğrulanamadı" olarak işaretleniyor, boş yanıtta sabit mesaj dönüyor. Gerçek örnek: gpt-oss `【1】` yazıyordu, normalize edildi. |
| 5 | AI olmadan yapabilir miydin? | Arama kısmı yapılabilirdi (parça listesi). Soruya doğal dille, sentezlenmiş yanıt vermek ise LLM'in işi. |

### Hafta 11 — Sohbet geçmişi ve bağlam
| # | Soru | Cevap iskeleti |
|---|---|---|
| 1 | Bağlamı nasıl yönettin? | Mesajlar DB'de tutuluyor, son mesajlar LLM'e geçmiş olarak veriliyor. Takip sorusu aramadan önce tek başına anlaşılır hâle getiriliyor ("peki bunun dezavantajı?" gibi). |
| 2 | Uzun geçmişi nasıl ele aldın? | Geçmiş 4000 karakteri aşınca eski mesajlar özetleniyor (`conversations.summary`, `summary_upto`). Son birkaç mesaj olduğu gibi kalıyor. |
| 3 | Verisini nasıl modelledin? | `conversations`, `messages` (durum, skor, süre), `message_sources` (N-N). Hepsi CASCADE ile bağlı. |
| 4 | Hangi iş kuralı? | Sohbet sahipliği (yönetici de başkasınınkini göremez). Hata olursa hiçbir şey kaydedilmez. Boş soru reddediliyor. Özet kaynak sayılmıyor. |
| 5 | Entegrasyon? | Arama yeniden yazılmış soruyla çalışıyor, RAG geçmiş ve özeti kullanıyor, rapor `messages` tablosunu okuyor. |

### Hafta 12 — Kullanım ve kaynak raporu
| # | Soru | Cevap iskeleti |
|---|---|---|
| 1 | En çok kullanılan kaynağı nasıl buldun? | `message_sources` ⨝ `chunks` ⨝ `documents`, belgeye göre gruplanıp `COUNT(DISTINCT yanıt)` ile sayılıyor ve sıralanıyor. |
| 2 | Kalite metriğini nasıl izledin? | Her yanıtla birlikte durum (`answered/no_context/no_info/unverified/general`), kaynağa dayalılık, süre ve en iyi skor kaydediliyor. |
| 3 | Hangi metrikleri neden seçtin? | Kullanım (soru sayısı), güvenilirlik (kaynaklı oran), boşluk (yanıtsız oran), hız (süre), arama kalitesi (skor). 💬 Kendi metriğini ekle. |
| 4 | Görseli hangi veriden ürettin? | `/reports/usage` JSON'undan (`daily`, `by_status`, `top_sources`). Arayüz sayıları kendisi hesaplamıyor. PDF çıktısı `report_pdf.py` ile üretiliyor. |
| 5 | Yanlış/eksik veri sonucu nasıl etkiler? | Eksik günler 0 ile dolduruluyor, veri yoksa oran yerine "—" gösteriliyor, bilinmeyen durum ayrı grupta. Kaynaklı olmak doğru olmak demek değil. 💬 "En yüksek: 1" hatası buraya iyi bir örnek olur. |

### Hafta 13 — Test ve hata ayıklama
| # | Soru | Cevap iskeleti |
|---|---|---|
| 1 | Birim ve entegrasyon testi farkı? | Birim testi tek fonksiyonu yalıtılmış sınar (`chunker.split_text`). Entegrasyon testi parçaları birlikte sınar (yükleme → parçalama → vektör → DB, `test_uctan_uca.py`). |
| 2 | Hangi senaryoları test ettin, neden? | Kullanıcı girdileri (dosya, ad, sorgu, parola, token) ve dış servisler: boş, aşırı büyük, bozuk, kötü niyetli durumlar. Hatalar en çok sınırlarda çıkar. |
| 3 | Edge case örneği? | 200 karakterlik dosya adında kırpma uzantıyı siliyordu (Hata 1). NUL karakteri PostgreSQL'de 500 hatası veriyordu. |
| 4 | Bulduğun bir hatayı nasıl ayıkladın? 💬 | **Kendi örneğin olmalı** ("en yüksek: 1", Hata 9). Adımlar: yeniden üret → kırmızı test → nedeni bul → en küçük düzeltme → tüm testler → belgele. |
| 5 | Neden %100 kapsam hedeflenmez? | Kapsam satırın çalıştığını ölçer, doğrulandığını değil. Son yüzdeler aşırı sahte nesne ister. Çaba riskli yerlere harcanmalı. Bende %92 (SQLite), %95 (PostgreSQL). |

### Hafta 14 — Dokümantasyon ve dağıtım
| # | Soru | Cevap iskeleti |
|---|---|---|
| 1 | README'de hangi bölümler olmalı? | Ne yaptığı, kurulum komutları, anahtarlar ve nereye yazıldıkları, testler, ayarlar tablosu, sık sorunlar, klasör yapısı, güvenlik, sınırlar. |
| 2 | Ortam değişkenlerini neden kullanıyorsun? | Gizli değerler koda girmesin ve aynı kod farklı ortamlarda çalışsın diye. `DATABASE_URL` yerelde SQLite, Vercel'de Supabase. |
| 3 | Projeni başka biri nasıl çalıştırır? | İki depoyu klonlar. Backend: `venv` → `pip install -r requirements-local.txt` → `python -m scripts.env_olustur` → `uvicorn app.main:app`. Frontend: `python -m http.server 5500 --directory public`. Bulut için `dagitim.md`. |
| 4 | Hangi kullanılabilirlik iyileştirmesini yaptın? | Yükleme yüzdesi, dosya seçilene kadar pasif "Yükle" düğmesi, büyük dosyayı göndermeden uyarı, koyu/açık tema, mobil düzen, ARIA, animasyon aç/kapa. 💬 Kendininkini ekle. |
| 5 | Dağıtımda karşılaşabileceğin sorun? | Vercel'de 4,5 MB istek sınırı (doğrudan Storage'a yükleme ile çözüldü) ve süre sınırı (parça parça indeksleme). CORS (`ALLOWED_ORIGINS`). HF kredisinin bitmesi (402 → Gemini). Supabase ücretsiz projesinin 1 hafta kullanılmayınca durması. |

### Hafta 15 — Final
| # | Soru | Cevap iskeleti |
|---|---|---|
| 1 | Sistemi uçtan uca anlat. | Yükleme → metin → 600 karakterlik örtüşen parçalar → Gemini vektörü (768) → pgvector. Soru → vektör → kosinüs → eşik → numaralı kaynaklar LLM'e (Groq) → `[n]` alıntı doğrulaması → yanıt + kaynaklar kaydedilir → rapor. |
| 2 | Mimari kararların artı/eksileri? | Katmanlı: test edilebilir ama daha çok dosya. İki depo: bağımsız dağıtım ama CORS ayarı gerekiyor. SQLite + PostgreSQL: yerelde kurulum yok, bulutta kalıcı, ama iki migration klasörü var. Hazır RAG kütüphanesi yok: her satırı açıklayabiliyorum ama daha çok kod yazdım. |
| 3 | Yapay zekâyı nerede, neden kullandın? 💬 | Üründe: embedding (anlam araması) ve LLM (yanıt). Geliştirmede: AI eş programcı; her öneri testle doğrulandı (`ai-kullanim-gunlugu.md`). Kendi örneğini eklemelisin. |
| 4 | Nasıl ölçeklendirirsin? | HNSW indeksi, indekslemeyi kuyrukta arka planda yapmak, giriş sayacını DB'ye ya da Redis'e taşımak, LLM yanıt önbelleği, ücretli planlar. |
| 5 | Yeniden yapsan neyi farklı yapardın? 💬 | Senin cevabın olmalı. Fikirler: baştan PostgreSQL, baştan arka plan indeksleme, ücretli/ücretsiz servis sınırlarını baştan ölçmek. |

### Ek — 3. parti API'den veri çekme (Vikipedi)
| # | Soru | Cevap iskeleti |
|---|---|---|
| 1 | Hangi 3. parti API'yi kullandın, neden? | Vikipedi (MediaWiki Action API). Ücretsiz, anahtar istemiyor, Türkçe içerik var. Lisansı CC BY-SA olduğu için belgenin başına kaynak adresi yazılıyor. |
| 2 | Veriyi nasıl çekiyorsun? | `app/services/wikipedia.py`: arama `list=search`, makale metni `prop=extracts&explaintext=1` (düz metin). İstek `urllib` ile, her istekte tanıtıcı bir `User-Agent` var (Wikimedia kuralı). |
| 3 | Çekilen veri sisteme nasıl giriyor? | `POST /wikipedia/import` metni `documents.import_text_document` ile `.txt` belgesi gibi işler: ayrıştır → parçala → vektörleştir. Sonra arama ve sohbet onu da kullanır. Dosya saklanmaz (`stored_name` boş). |
| 4 | API hata verirse ya da makale yoksa? | Geçersiz dil/boş sorgu 400 (istek atılmadan), makale yok 404, Vikipedi'ye ulaşılamazsa ya da bozuk yanıt gelirse 502 ("dış servis hatası"). |
| 5 | Neden tarayıcı Vikipedi'ye doğrudan gitmiyor? | Kurallar (User-Agent, hata yönetimi) tek yerde kalsın, metin backend'de indekslensin ve kullanıcının hangi belgeyi eklediği sunucuda kayıtlı olsun diye. 💬 Kendi cümlelerinle anlat. |
