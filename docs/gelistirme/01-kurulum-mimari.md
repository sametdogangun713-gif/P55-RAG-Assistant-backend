# Adım 1 — Kurulum, mimari ve ER diyagramı

> Ders planındaki karşılığı: **Hafta 3**. Bu belge eski `hafta-03/README.md` ve `hafta-03/aciklama.md` dosyalarının birleşimidir.

## Ne yapıldı

### Amaç
Geliştirme ortamını kurmak, mimariyi ve veri modelini tasarlamak, GitHub deposunu oluşturmak.

### Bu hafta eklenen / değişen dosyalar
| Dosya | Ne işe yarıyor |
|---|---|
| `app/main.py` | FastAPI uygulaması, `/health` uç noktası |
| `app/core/config.py` | Ortam değişkenlerinden ayar okuma |
| `app/api`, `app/services`, `app/db` | Boş katmanlar (sunum / iş / veri) |
| `docs/er-diyagrami.md` | ER diyagramı (Mermaid, GitHub'da çizilir) |
| `docs/mimari.md` | Katmanlı mimari şeması ve gerekçe alanı |
| `.gitignore`, `scripts/env_olustur.py` | Gizli dosyaları dışarıda tutma; `.env`'i boş şablondan oluşturma |
| `requirements*.txt`, `pytest.ini` | Bağımlılıklar ve test ayarı |

### Çalıştırma (Windows)
```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
python -m scripts.env_olustur
uvicorn app.main:app --reload
```
Tarayıcıda `http://127.0.0.1:8000/health` → `{"status":"ok"}`. Swagger: `http://127.0.0.1:8000/docs`

Testler: `pytest tests/test_iskelet.py`

### Kendi yapacakların (PDF: "Öğrencinin kendi geliştireceği bölümler")
1. `docs/er-diyagrami.md` içindeki varlıkları ve ilişkileri gözden geçir; bir tabloyu ya da alanı kendin ekle/çıkar ve nedenini "Kendi gerekçem" bölümüne yaz.
2. `docs/mimari.md` içindeki "Gerekçem" bölümünü kendi cümlelerinle doldur.
3. `docs/ai-kullanim-gunlugu.md` içindeki boş alanları (kendi değişikliğin, doğrulaman) doldur.

### Kontrol listesi
- [ ] Depo erişilebilir ve düzenli (README, .gitignore var)
- [ ] ER diyagramı varlık/ilişkileri doğru
- [x] Mimari katmanlar tanımlı
- [ ] `/health` çalışıyor, ekran görüntüsü alındı
- [ ] Depo herkese açık (hocanın GitHub hesabı yok; iş birlikçi eklemeye gerek yok, depo bağlantısı paylaşılır)

### Demo
GitHub depo sayfası + `/health` + ER diyagramı + mimari şema gösterilir.

## Kod açıklaması

### Dosya dosya
**`app/main.py`** — `FastAPI(...)` bir uygulama nesnesi üretir. `@app.get("/health")` dekoratörü, aşağıdaki
fonksiyonu GET `/health` adresine bağlar. Fonksiyon bir sözlük döner, FastAPI bunu JSON'a çevirir.
Amaç: iskeletin ayakta olduğunu kanıtlamak.

**`app/core/config.py`** — `os.getenv("ADI", varsayılan)` ortam değişkenini okur; yoksa varsayılanı kullanır.
`load_dotenv()` `.env` dosyasındaki satırları ortam değişkenine çevirir. Böylece gizli değerler koda girmez.
`db_path()` `sqlite:///./data/p55.db` biçimindeki adresten dosya yolunu ayıklar.

**Katman klasörleri** — `api` (HTTP), `services` (iş kuralları), `db` (SQL). Bağımlılık yönü api → services → db.

**`.gitignore`** — `.env` (gizli anahtarlar), `venv/` (kurulu paketler, makineye özel), `data/*.db` (yerel veritabanı),
`uploads/*` (kullanıcı belgeleri; gizlilik/KVKK), `__pycache__` (derleme artıkları) depoya girmez.

**`pytest.ini`** — `pythonpath = .` sayesinde testler `import app...` yapabilir; `testpaths = .` hafta klasörlerindeki testleri bulur.

### Sözlü sınav soruları ve cevap iskeleti
**1) Katmanlı mimariyi neden tercih ettin?**
Sorumlulukları ayırmak için: API yalnızca isteği/yetkiyi, servis iş kuralını, db katmanı SQL'i bilir. Böylece belge ayrıştırma
mantığını HTTP olmadan test edebiliyorum, veritabanını değiştirmem gerekirse yalnızca `app/db` etkilenir.

**2) İlişki türlerini örnekle açıkla.**
1-1: bir parça (chunk) ↔ en fazla bir embedding. 1-N: bir kullanıcı → çok belge, bir belge → çok parça.
N-N: bir cevap birden çok parçaya dayanır, bir parça birden çok cevapta kaynak olur → ara tablo `message_sources`.

**3) Hangi varlıklar birincil anahtar taşıyor, neden?**
Hepsi (`id`): satırı tek ve değişmez biçimde tanımlamak, yabancı anahtarlarla bağlanmak için. `message_sources` tablosunda
bileşik anahtar (`message_id`, `chunk_id`): aynı cevap-parça çifti iki kez yazılamasın diye.

**4) Klasör yapını hangi mantıkla kurdun?**
Katmana göre (api/services/db/core) + test ve belgeler ayrı. Hafta klasörleri (`hafta-XX`) teslim edilecek not, test ve günlükleri toplar;
kod tek ortak `app/` içinde kalır, böylece her hafta kümülatif ilerler.

**5) .gitignore neden gerekli, neler eklenmemeli?**
Gizli bilgi (API anahtarı, parola) ve makineye özel/üretilebilir dosyalar depoya girmesin diye. Eklenmemeli: `.env`, `venv/`, `*.db`,
yüklenen belgeler, indirilen modeller. Bir kez GitHub'a giden anahtar geçmişten silinse bile sızmış sayılır; anahtarı yenilemek gerekir.

### Sık yapılan hatalar
Her şeyi tek dosyada toplamak · ER'de ilişki/anahtarı eksik bırakmak · `.env` dosyasını depoya yüklemek.
