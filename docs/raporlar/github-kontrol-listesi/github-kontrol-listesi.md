# 7. GitHub Kullanım Kontrol Listesi

| | | | |
|---|---|---|---|
| **Öğrenci** | Samet DOĞANGÜN | **Numara** | 211161024 |
| **Proje (Kod/Ad)** | P55 – Belge Tabanlı Soru-Cevap Asistanı (RAG) | **Son kontrol** | 04.10.2026 |

| Madde | Durum | Açıklama |
|---|---|---|
| Proje için ayrı bir depo oluşturuldu | [x] | İki depo: backend (API + belgeler) ve frontend (arayüz) |
| Öğretim elemanı iş birlikçi/izleyici olarak eklendi | [ ] | Öğretim elemanının GitHub hesabı yok; depolar **herkese açık (public)**, bağlantıyla izlenebilir |
| .gitignore eklendi (gizli/gereksiz dosyalar hariç) | [x] | `.env`, `*.db`, `uploads/*`, `venv/`, `__pycache__/` yok sayılıyor |
| README oluşturuldu ve güncel | [x] | Kurulum, çalışma biçimleri, ortam değişkenleri tablosu |
| Commit'ler küçük ve anlamlı | [x] | Konu bazlı commit'ler (ör. `feat: kullanım raporu PDF olarak`) |
| Commit mesajları açıklayıcı | [x] | `feat:` / `fix:` / `docs:` / `chore:` önekleri + Türkçe açıklama |
| Her haftanın çalışması ilgili hafta içinde yüklendi | [ ] | 3. haftadan itibaren her hafta işaretlenecek; ilk yükleme öğretim elemanının izniyle toplu yapıldı |
| Gizli anahtar/parola/API anahtarı depoda yok (ortam değişkeni) | [x] | Depodaki dosyalar anahtar desenleri için tarandı; anahtarlar yalnızca `.env` ve Vercel ortam değişkenlerinde |
| Düzenli klasör/katman yapısı | [x] | `app/api → app/services → app/db`, `tests/`, `docs/` |
| (Varsa) dal (branch) kullanımı anlamlı | [ ] | Tek dal (`main`) kullanılıyor |

**Depo bağlantıları:**
- Backend: https://github.com/sametdogangun713-gif/P55-RAG-Assistant-backend
- Frontend: https://github.com/sametdogangun713-gif/P55-RAG-Assistant-frontend
