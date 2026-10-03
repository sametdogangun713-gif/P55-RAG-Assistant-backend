# Mimari

## Uygulamanın katmanları (backend içi)
```mermaid
flowchart TD
    UI[Tarayıcı arayüzü<br/>P55-RAG-Assistant-frontend] -->|HTTP + JWT| API
    API[Sunum katmanı: app/api<br/>HTTP uç noktaları, yetki kontrolü] --> BL
    BL[İş katmanı: app/services<br/>ayrıştırma, parçalama, gömme, arama, RAG, sohbet] --> DL
    BL --> EXT[(Harici servisler<br/>Groq / Claude, Hugging Face, Supabase Storage)]
    BL --> EMB[Yerel embedding modeli<br/>yalnızca yerelde]
    DL[Veri katmanı: app/db<br/>SQL, migration, CRUD] --> DB[(SQLite yerelde<br/>PostgreSQL + pgvector bulutta)]
    CORE[app/core<br/>ayarlar, güvenlik] -.-> API
    CORE -.-> BL
```

## Dağıtım (iki depo, bulut)
```mermaid
flowchart LR
    U[Tarayıcı] --> FE[Vercel: P55-RAG-Assistant-frontend<br/>statik HTML/CSS/JS]
    U -->|API| BE[Vercel: P55-RAG-Assistant-backend<br/>FastAPI, Frankfurt]
    U -->|imzalı adresle dosya| ST[(Supabase Storage)]
    BE --> PG[(Supabase PostgreSQL<br/>+ pgvector)]
    BE --> ST
    BE --> HF[Hugging Face<br/>embedding]
    BE --> LLM[Groq / Claude]
```
Arayüz ve API ayrı depolarda, ayrı adreslerde çalışır. Arayüz backend adresini `config.js`'ten okur; backend yalnızca
`ALLOWED_ORIGINS`'teki adreslerden gelen tarayıcı isteklerine izin verir (CORS). Ayrıntı: [`dagitim.md`](dagitim.md).

## Katmanların görevi
- **Sunum (app/api):** İstekleri alır, doğrular, kimlik/rol kontrolü yapar, servisleri çağırır. İş mantığı içermez.
- **İş (app/services):** Belge ayrıştırma, chunking, embedding, benzerlik arama, RAG ve sohbet bağlamı burada.
- **Veri (app/db):** Yalnızca SQL: bağlantı, migration, CRUD fonksiyonları. Aynı SQL hem SQLite'ta hem PostgreSQL'de çalışır; farkları `database.PgConnection` kapatır.
- **Çekirdek (app/core):** Ayarlar (`config.py`) ve güvenlik yardımcıları (`security.py`, Hafta 5).

Bağımlılık yönü tek yönlüdür: api → services → db. Alt katman üst katmanı bilmez.

## Gerekçem (kendi cümlelerinle doldur)
- Katmanlı mimariyi neden seçtim:
- SQLite'ı neden seçtim (yerel) ve bulutta neden PostgreSQL'e (Supabase) geçtim:
- Klasör yapısını hangi mantıkla kurdum:
- Frontend ve backend'i neden iki ayrı depoya ayırdım:
