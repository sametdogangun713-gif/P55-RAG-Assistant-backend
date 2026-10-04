# Proje Öneri Formu (2. hafta)

| | | | |
|---|---|---|---|
| **Öğrenci** | Samet DOĞANGÜN | **Numara** | 211161024 |
| **Proje (Kod/Ad)** | P55 – Belge Tabanlı Soru-Cevap Asistanı (RAG) | **Tarih** | 04.10.2026 |
| **Ders** | Bilgisayar Uygulamaları I | **Öğretim elemanı** | Öğr. Gör. Mustafa NARİN |

Ders takvimi: 2. haftada öğrenci projesini seçer; problem analizi, kaynak araştırması ve gereksinim analizini yapıp
öğretim elemanının onayına sunar. Proje künyesi (problem, amaç, hedef kullanıcı, modüller) ders paketinin proje
havuzundan alınmıştır.

## 1. Problem tanımı
Kullanıcılar uzun belgelerde (yönetmelik, ders notu, rapor, kılavuz) aradıkları bilgiyi bulmakta zaman kaybediyor.
Kelime araması yalnızca aynı kelimeyi bulur; soru farklı kelimelerle sorulunca ("devamsızlık sınırı" ↔ "derslerin
%30'undan fazlasına girmeyen") sonuç vermez. Genel sohbet botları ise belgeyi bilmez ve uydurabilir (halüsinasyon).

## 2. Amaç ve hedef kullanıcı
- **Amaç:** Kullanıcının yüklediği belgelere dayanarak, her cümlesinin hangi belge parçasından geldiğini gösteren
  (kaynaklı) yanıt veren bir soru-cevap asistanı kurmak. Belgede yanıt yoksa uydurmak yerine "belgede bulunamadı" demek.
- **Hedef kullanıcı:** Öğrenciler, araştırmacılar ve profesyoneller.
- **Neden önemli:** Belgeye dayalı, doğrulanabilir yanıtlar bilgiye erişimi hızlandırır; kaynak gösterildiği için
  kullanıcı yanıtı kendisi kontrol edebilir.
- 💬 **Bu projeyi neden seçtim:** _(öğrenci yazar)_

## 3. Kapsam — modüller
| # | Modül | Ders planındaki hafta |
|---|---|---|
| 1 | Kurulum, katmanlı mimari, veri modeli (ER) | 3 |
| 2 | Veritabanı ve veri erişim katmanı (migration, CRUD) | 4 |
| 3 | Kimlik doğrulama ve roller (kullanıcı / yönetici) | 5 |
| 4 | Belge yükleme, ayrıştırma (TXT/PDF/DOCX) ve parçalama | 6 |
| 5 | Gömme (embedding) ve vektör arama | 7 |
| 6 | Harici LLM API istemcisi (hata/zaman aşımı yönetimi) | 9 |
| 7 | Kaynaklı yanıt üretimi (RAG), halüsinasyon önleme | 10 |
| 8 | Sohbet geçmişi ve bağlam | 11 |
| 9 | Kullanım raporu ve yönetim paneli | 12 |
| 10 | Web arayüzü | 8, 14 |

**Kapsam dışı:** sesli soru, görüntüden metin okuma (OCR), çok kullanıcılı ortak belge alanı (künyedeki "genişletilebilir
özellikler" ileride değerlendirilebilir).

## 4. Gereksinim analizi
### İşlevsel gereksinimler
1. Kullanıcı ad soyad, e-posta ve parolayla kayıt olur; e-posta adresi gönderilen kodla doğrulanır; giriş yapar, parolasını sıfırlayabilir.
2. Kullanıcı TXT, PDF ve DOCX belge yükler; belge metne çevrilip parçalara ayrılır ve vektörleştirilir.
3. Kullanıcı yalnızca **kendi** belgelerini görür, arar ve siler.
4. Kullanıcı soru sorar; sistem en ilgili parçaları bulur ve yanıtı `[n]` kaynak işaretleriyle verir. Belgede yanıt yoksa bunu açıkça söyler.
5. Sohbetler kaydedilir; takip soruları önceki mesajları dikkate alır.
6. Kullanıcı ve yönetici kullanım raporunu görür (soru sayısı, kaynaklı yanıt oranı, en çok kullanılan belgeler) ve PDF olarak indirir.
7. Yönetici kullanıcıları ve tüm belgeleri yönetir.
8. Başka uygulamalar kişisel API anahtarıyla sisteme bağlanabilir.

### İşlevsel olmayan gereksinimler
| Konu | Gereksinim |
|---|---|
| Güvenlik | Parolalar özetlenerek (scrypt + tuz) saklanır; gizli anahtarlar yalnızca ortam değişkenlerinde; her istekte yetki kontrolü sunucuda |
| Gizlilik (KVKK) | Gerçek kişisel veri kullanılmaz; test ve demo verisi sentetik (`@example.com`) |
| Doğruluk | Yanıt yalnızca getirilen parçalara dayanır; alıntısı geçersiz yanıt "kaynağa dayalı" sayılmaz |
| Maliyet | Ücretsiz katmanlar yeterli olmalı (yerel embedding, Groq ücretsiz katmanı, Supabase/Vercel ücretsiz planı) |
| Taşınabilirlik | Aynı kod hem yerelde (SQLite) hem bulutta (PostgreSQL) çalışır; hangisi olduğuna ayarlar karar verir |
| Kullanılabilirlik | Türkçe arayüz ve hata mesajları; mobilde de kullanılabilir; açık/koyu tema |
| Test edilebilirlik | Otomatik testler (pytest); dış servisler testte sahte sunucularla taklit edilir |

## 5. Teknoloji seçimi
| Katman | Seçim | Kısa gerekçe |
|---|---|---|
| Backend | Python + FastAPI | Yapay zekâ kütüphaneleri Python'da; otomatik API belgesi (Swagger) |
| Veritabanı | SQLite (yerel) · PostgreSQL + pgvector (Supabase, bulut) | Saf SQL + migration dosyaları; vektörler veritabanında |
| Embedding | `sentence-transformers` (yerel) · Hugging Face Inference API, `BAAI/bge-m3` (bulut) | Çok dilli (Türkçe), ücretsiz |
| Yanıt modeli (LLM) | Groq (`openai/gpt-oss-120b`) · Claude API (seçenek) | Ücretsiz katman; sağlayıcı ayarla değişir |
| Arayüz | HTML + CSS + JavaScript (çerçevesiz) | Ayrı depo; her satırı açıklanabilir |
| Dağıtım | Vercel (backend + frontend) · Supabase Storage (dosyalar) | Ücretsiz plan |

💬 **Seçimlerimin gerekçesi (kendi cümlelerimle):** _(öğrenci yazar — sözlüde sorulur)_

## 6. Kaynak araştırması
Projede başvurulan temel kaynaklar:
- P. Lewis vd., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*, NeurIPS 2020 — RAG yaklaşımı.
- N. Reimers, I. Gurevych, *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*, EMNLP 2019 — cümle gömmeleri (`sentence-transformers`).
- J. Chen vd., *BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings*, 2024 — bulutta kullanılan çok dilli model.
- FastAPI, pgvector, Supabase, Groq ve Hugging Face resmî belgeleri.
- Ders paketi: P55 künyesi ve haftalık faaliyet planı.

💬 **Okuduklarımdan öğrendiğim (kısa not):** _(öğrenci yazar)_

**Yapay zekâ kullanım beyanı:** Geliştirmede yapay zekâ (Claude, Claude Code) "AI eş programcı" olarak kullanılmaktadır;
her kullanım [`../ai-kullanim-gunlugu.md`](../ai-kullanim-gunlugu.md)'ye işlenir.

## 7. Ders ölçütlerine uygunluk
| Ölçüt (ders yönergesi) | Bu projede |
|---|---|
| Asgari 4–6 anlamlı modül | ✅ 10 modül (§3) |
| İlişkisel veritabanı | ✅ 9 tablo, yabancı anahtarlar, migration'lar ([`../er-diyagrami.md`](../er-diyagrami.md)) |
| En az bir harici API | ✅ Groq / Claude (LLM), Hugging Face (embedding), Supabase (veritabanı + dosya) |
| Yapay zekâ işlevsel (dekoratif değil) | ✅ Vektör arama + kaynaklı yanıt üretimi projenin çekirdeği |
| Temel test ve belgelenmiş test çıktıları | ✅ [`../test-raporu.md`](../test-raporu.md) |
| Teknik dokümantasyon | ✅ [`../teknik-dokumantasyon.md`](../teknik-dokumantasyon.md) |
| Düzenli Git/GitHub kullanımı | ✅ İki depo (backend, frontend), konu bazlı commit'ler |

## 8. Riskler
Ayrıntı: [`risk-analizi.md`](risk-analizi.md).

## 9. Öğretim elemanı onayı
| | |
|---|---|
| Karar | ☐ Onaylandı  ☐ Revize edilecek |
| Not | |
| Tarih / İmza | |
