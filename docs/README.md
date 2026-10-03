# Belgeler

Projenin bütün yazılı belgeleri bu klasörde. Kod iki depoda (backend + frontend), belgeler yalnızca burada.

## Başlangıç
| Belge | Ne var? |
|---|---|
| [`yol-haritasi.md`](yol-haritasi.md) | Ders planındaki adımlar, hangisi bitti, ne kaldı, kimin işi |
| [`teknik-dokumantasyon.md`](teknik-dokumantasyon.md) | Modüller, veri modeli, **tüm API uç noktaları**, ana akışlar |
| [`dagitim.md`](dagitim.md) | Supabase + Hugging Face + Vercel kurulumu, ortam değişkenleri, sorun giderme |
| [`mimari.md`](mimari.md) · [`er-diyagrami.md`](er-diyagrami.md) | Katmanlı mimari, veritabanı diyagramı |
| [`guvenlik-notu.md`](guvenlik-notu.md) | Güvenlik önlemleri ve bilinen sınırlar |

## Geliştirme adımları (ders planı sırasıyla)
Her dosya: o adımda ne yapıldı, kodun açıklaması, **sözlü sınav soruları** ve **senin yapacakların**.

| Adım | Belge | Ders planında |
|---|---|---|
| 1 | [Kurulum, mimari ve ER diyagramı](gelistirme/01-kurulum-mimari.md) | Hafta 3 |
| 2 | [Veritabanı şeması, migration ve CRUD](gelistirme/02-veritabani.md) | Hafta 4 |
| 3 | [Kimlik doğrulama ve roller](gelistirme/03-kimlik-dogrulama.md) | Hafta 5 |
| 4 | [Belge yükleme, ayrıştırma ve parçalama](gelistirme/04-belge-isleme.md) | Hafta 6 |
| 5 | [Embedding ve vektör arama](gelistirme/05-embedding-arama.md) | Hafta 7 |
| 6 | [Entegrasyon ve web arayüzü (vize)](gelistirme/06-entegrasyon-arayuz.md) | Hafta 8 |
| 7 | [Harici LLM API istemcisi](gelistirme/07-llm-istemcisi.md) | Hafta 9 |
| 8 | [RAG: kaynaklı yanıt](gelistirme/08-rag.md) | Hafta 10 |
| 9 | [Sohbet geçmişi ve bağlam](gelistirme/09-sohbet-gecmisi.md) | Hafta 11 |
| 10 | [Kullanım raporu ve yönetim](gelistirme/10-rapor-yonetim.md) | Hafta 12 |
| 11 | [Test ve hata ayıklama](gelistirme/11-test-hata-ayiklama.md) | Hafta 13 |
| 12 | [Dokümantasyon, arayüz, dağıtım (Supabase + Vercel)](gelistirme/12-dagitim-dokumantasyon.md) | Hafta 14 |
| 13 | [Final entegrasyon ve sunum](gelistirme/13-final.md) | Hafta 15 |

## Raporlar ve kayıtlar
| Belge | Ne var? |
|---|---|
| [`ai-kullanim-gunlugu.md`](ai-kullanim-gunlugu.md) | Her adımda yapay zekânın nasıl kullanıldığı ("kendi" alanlarını geliştirici doldurur) |
| [`test-raporu.md`](test-raporu.md) | Test sayıları, kapsam, hangi senaryolar neden test edildi |
| [`duzeltilen-hatalar.md`](duzeltilen-hatalar.md) | Testlerle bulunan ve düzeltilen gerçek hatalar |
| [`istem-deneyleri.md`](istem-deneyleri.md) | Gerçek LLM ile istem (prompt) denemeleri |
| [`demo-senaryosu.md`](demo-senaryosu.md) · [`vize-sozlu-hazirlik.md`](vize-sozlu-hazirlik.md) · [`ilerleme-raporu-vize.md`](ilerleme-raporu-vize.md) | Vize demosu ve hazırlığı |
| [`../CHANGELOG.md`](../CHANGELOG.md) | Sürüm değişiklikleri |

## Eski klasör düzeninden geçiş (2026-10-03)
Proje önce tek depo ve `hafta-XX/` klasörleriyle düzenlenmişti. Kod ikiye ayrılınca belgeler burada birleşti,
testler `tests/` klasörüne taşındı. Eski adlarla karşılaşırsan (ör. AI günlüğünde) eşleme:

| Eski | Yeni |
|---|---|
| `hafta-03/test_h03_iskelet.py` | `tests/test_iskelet.py` |
| `hafta-04/test_h04_veritabani.py` | `tests/test_veritabani.py` |
| `hafta-05/test_h05_kimlik.py` | `tests/test_kimlik.py` |
| `hafta-06/test_h06_belge.py` | `tests/test_belge.py` |
| `hafta-07/test_h07_vektor.py` | `tests/test_vektor.py` |
| `hafta-08/test_h08_uctan_uca.py` | `tests/test_uctan_uca.py` (arayüz kısmı → frontend `tests/test_arayuz.py`) |
| `hafta-09/test_h09_llm.py`, `test_h09_groq.py` | `tests/test_llm.py`, `tests/test_groq.py` |
| `hafta-10/test_h10_rag.py` | `tests/test_rag.py` |
| `hafta-11/test_h11_sohbet.py` | `tests/test_sohbet.py` |
| `hafta-12/test_h12_rapor.py` | `tests/test_rapor.py` |
| `hafta-13/test_h13_sinir_durumlari.py` | `tests/test_sinir_durumlari.py` |
| `hafta-13/test_h13_benim.py` (senin yazacağın) | `tests/test_benim.py` |
| `hafta-14/test_h14_*.py` | `tests/test_buyuk_yukleme.py`, `test_kurulum.py`, `test_sifre_sifirlama.py` (+ frontend `test_arayuz.py`) |
| `hafta-XX/README.md` + `aciklama.md` | `docs/gelistirme/NN-*.md` |
| `hafta-XX/ai-log.md` | `docs/ai-kullanim-gunlugu.md` |
| `hafta-XX/GITHUB.md` | kaldırıldı (haftalık yükleme planıydı) |
| Yeni (bulut) | `tests/test_bulut.py` |
