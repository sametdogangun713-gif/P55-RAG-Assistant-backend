# Adım 2 — Veritabanı şeması, migration ve CRUD

> Ders planındaki karşılığı: **Hafta 4**. Bu belge eski `hafta-04/README.md` ve `hafta-04/aciklama.md` dosyalarının birleşimidir.

## Ne yapıldı

### Amaç
Veritabanı şemasını oluşturmak, ilişkileri kurmak ve temel veri erişim (CRUD) katmanını yazmak.

### Bu hafta eklenen / değişen dosyalar
| Dosya | Ne işe yarıyor |
|---|---|
| `app/db/migrations/001_init.sql` | Tüm tabloların, kısıtların ve indekslerin şeması |
| `app/db/database.py` | Bağlantı açma + migration çalıştırıcı |
| `app/db/users.py`, `documents.py`, `chunks.py` | CRUD fonksiyonları (parametreli SQL) |
| `scripts/seed.py` | Sentetik örnek veri (gerçek kişisel veri yok → KVKK) |
| `tests/helpers.py` | Testlerde bellekte temiz veritabanı |
| `app/main.py` | Açılışta migration'ları çalıştırır |

### Çalıştırma ve demo
```bat
python -m scripts.seed
python -c "from app.db import database; c=database.get_connection(); print([dict(r) for r in c.execute('SELECT id, filename, status FROM documents')])"
pytest tests/test_veritabani.py
```
Gösterilecek: şema, örnek veriyle dolu veritabanı, birkaç CRUD sorgusu, kısıtların (yabancı anahtar, benzersiz e-posta) hata vermesi.

### Kendi yapacakların
1. `documents.size_bytes` için `CHECK (size_bytes >= 0)` kısıtını kendin yaz. **İki veritabanı var:**
   SQLite'ta `app/db/migrations/001_init.sql` içine (yerel `data\p55.db`'yi silip yeniden oluştur);
   PostgreSQL'de bulut veritabanı zaten kurulduğu için 001'i değiştirmek işe yaramaz → **yeni** migration yaz:
   `app/db/migrations/postgres/002_size_check.sql` → `ALTER TABLE documents ADD CONSTRAINT documents_size_nonneg CHECK (size_bytes >= 0);`
   (Sözlüde iyi soru: neden çalışan bir veritabanında eski migration dosyası değiştirilmez?)
   (`data\p55.db` dosyasını silip uygulamayı/seed'i yeniden çalıştır; veri sentetik olduğu için sorun olmaz.)
2. Bu kısıt için `test_veritabani.py` içine kendi testini ekle.
3. Bir ilişkiyi (örn. `chunks → documents`) ve bir kısıtı sözlüde elle anlatabilecek hâle gel (bu belgenin "Kod açıklaması" bölümü).
4. `docs/ai-kullanim-gunlugu.md` boş alanlarını doldur.

### Kontrol listesi
- [x] İlişki ve kısıtlar çalışıyor
- [x] CRUD işlemleri sorunsuz
- [x] Sentetik veri KVKK'ya uygun (gerçek kişisel veri yok)

## Kod açıklaması

### Dosya dosya
**`database.py` → `get_connection`**
`sqlite3.connect(yol)` bir bağlantı açar. `row_factory = sqlite3.Row` satırlara `satir["email"]` ile erişmemizi sağlar.
`PRAGMA foreign_keys = ON` kritik: SQLite'ta yabancı anahtar denetimi **varsayılan kapalıdır**, her bağlantıda açılmalı.
Açılmazsa `ON DELETE CASCADE` ve "olmayan kullanıcıya belge ekleme" engeli çalışmaz.

**`database.py` → `run_migrations`**
`migrations/` klasöründeki `.sql` dosyalarını ada göre sıralar; `schema_migrations` tablosunda kayıtlı olmayanları çalıştırır.
Her dosya `BEGIN; ... COMMIT;` içinde çalışır; hata olursa geri alınır. Böylece şema değişiklikleri sürümlenir ve her ortamda aynı sırayla uygulanır.

**`001_init.sql`** — Önemli kısıtlar:
- `email ... UNIQUE COLLATE NOCASE` → aynı e-posta büyük/küçük harf farkıyla iki kez kaydolamaz.
- `role CHECK (role IN ('user','admin'))`, `status CHECK (...)` → geçersiz değer veritabanı seviyesinde engellenir.
- `REFERENCES users(id) ON DELETE CASCADE` → kullanıcı silinince belgeleri, parçaları, vektörleri, sohbetleri de silinir.
- `UNIQUE (document_id, chunk_index)` → aynı belgede aynı sıra numarası iki kez olamaz (aynı zamanda `document_id` ile aramayı hızlandıran indeks).
- `message_sources` bileşik birincil anahtar `(message_id, chunk_id)` → N-N ara tablosu, aynı çift tekrar yazılamaz.

**`users.py`, `documents.py`, `chunks.py`** — Her fonksiyon `conn` alır, **parametreli sorgu** (`?`) kullanır.
Parametreli sorguda kullanıcı girdisi SQL metnine eklenmez, değer olarak bağlanır; bu yüzden `x' OR '1'='1` gibi girdiler etkisizdir (testte kanıtlandı).
`create_user` benzersizlik ihlalini `DuplicateEmailError` olarak yukarı taşır; servis katmanı bunu anlamlı hataya çevirecek.

**Neden saf SQL (ORM değil)?** SQL'i doğrudan görmek ve açıklamak sözlü için daha kolay; proje küçük, sorgu sayısı sınırlı.

### İndeksler
- `idx_documents_user` → "bir kullanıcının belgeleri" sorgusu `WHERE user_id = ?` ile yapılır.
- `idx_conversations_user`, `idx_messages_conversation` → sohbet listesi ve mesaj listesi aynı biçimde.
- `idx_message_sources_chunk` → raporda "hangi parça kaç kez kaynak oldu" sorgusu için.
- `embeddings.chunk_id` UNIQUE ve `users.email` UNIQUE → otomatik indeks oluşur.
- **Eklemediklerim:** `chunks.content` gibi uzun metin alanlarına indeks yok (arama vektörle yapılır, SQL `LIKE` ile değil). Her indeks yazmayı yavaşlatır ve yer kaplar.

### Bir CRUD örneği: SQL'i açıklama
`INSERT INTO documents (user_id, filename, stored_name, mime_type, size_bytes) VALUES (?, ?, ?, ?, ?)`
→ yeni satır ekler; `status` varsayılan `'uploaded'`, `uploaded_at` varsayılan `CURRENT_TIMESTAMP` (UTC).
`cur.lastrowid` yeni satırın `id`'sidir; sonra `get_document` ile geri okuruz.
`conn.commit()` çağrılana kadar değişiklik kalıcı olmaz (işlem/transaction).

### Sözlü sınav soruları ve cevap iskeleti
**1) Bir tabloya neden indeks ekledin/eklemedin?**
Sık filtrelenen yabancı anahtar sütunlarına ekledim (`documents.user_id` gibi) çünkü her sayfa açılışında "bu kullanıcının belgeleri" sorgulanıyor.
Uzun metin sütunlarına eklemedim; indeks yazma maliyeti getirir ve orada arama SQL ile değil vektörle yapılıyor.

**2) Yabancı anahtar kısıtı ne işe yarar?**
Referans bütünlüğü: `documents.user_id` olmayan bir kullanıcıya işaret edemez; `ON DELETE CASCADE` ile üst kayıt silinince bağlı kayıtlar yetim kalmaz.
(SQLite'ta `PRAGMA foreign_keys=ON` gerekir.)

**3) N-N ilişkiyi nasıl modelledin?**
Cevaplar ↔ parçalar: ara tablo `message_sources(message_id, chunk_id, score)` ve bileşik birincil anahtar. Her satır "bu cevap bu parçaya dayanıyor"u söyler, `score` benzerlik skorunu tutar.

**4) Migration neden kullanılır?**
Şema değişikliklerini sürümlemek ve her makinede aynı sırayla, tekrar çalıştırılabilir biçimde uygulamak için. Elle SQL çalıştırmak hata ve ortam farkı üretir.
Bu projede `001_init.sql` ilk şemayı kurar, sonraki haftalarda `002`, `003` dosyaları `ALTER TABLE` ile alan ekler.

**5) Bir CRUD işleminin SQL'ini açıkla.** → yukarıdaki INSERT örneği; ayrıca
`SELECT d.*, (SELECT COUNT(*) FROM chunks c WHERE c.document_id = d.id) AS chunk_count FROM documents d ...` ilişkili alt sorgu ile parça sayısını hesaplar.

### Sık yapılan hatalar
İlişkisiz tablolar · kısıt tanımlamamak · `foreign_keys` pragmasını açmamak · gerçek kişisel veri kullanmak (burada yalnızca `@example.com` sentetik veri var).
