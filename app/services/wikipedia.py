"""3. parti API: Vikipedi'den makale arama ve makale metnini cekme. Yalnizca standart kutuphane (urllib).

Kullanilan API: MediaWiki Action API (https://<dil>.wikipedia.org/w/api.php). Ucretsizdir, anahtar istemez.
Kurallari: her istekte tanitici bir User-Agent, istekleri arka arkaya yigmamak (burada her istek bir kullanici
tiklamasi). Metin CC BY-SA lisanslidir: belgeye kaynak adresi ve lisans yazilir.

  search("tr", "fotosentez")         -> [{"title", "snippet", "pageid"}, ...]   (list=search)
  fetch_article("tr", "Fotosentez")  -> {"title", "url", "text"}                (prop=extracts, duz metin)
Cekilen metin services/documents.py'de normal bir .txt belgesi gibi parcalanir ve indekslenir.
"""
import html
import json
import re
import urllib.error
import urllib.parse
import urllib.request

from app.core import config

MAX_QUERY_LENGTH = 200
MAX_RESULTS = 10


class WikipediaError(Exception):
    """Vikipedi'ye ulasilamadi ya da beklenmeyen yanit geldi."""


class WikipediaNotFoundError(WikipediaError):
    """Istenen baslikta makale yok."""


class WikipediaInputError(WikipediaError):
    """Kullanicinin girdisi gecersiz (dil, bos sorgu ...)."""


def _check_lang(lang: str) -> str:
    lang = (lang or "").strip().lower()
    if lang not in config.WIKIPEDIA_LANGS:
        raise WikipediaInputError("Desteklenen diller: " + ", ".join(config.WIKIPEDIA_LANGS))
    return lang


def _get(lang: str, params: dict) -> dict:
    """API'ye GET istegi atar, JSON'u sozluk olarak dondurur. formatversion=2: sayfalar liste olarak gelir."""
    query = urllib.parse.urlencode({**params, "format": "json", "formatversion": "2"})
    url = config.WIKIPEDIA_API_URL.format(lang=lang) + "?" + query
    req = urllib.request.Request(url, headers={"User-Agent": config.WIKIPEDIA_USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=config.WIKIPEDIA_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise WikipediaError(f"Vikipedi isteği reddedildi ({e.code})") from None
    except (urllib.error.URLError, TimeoutError) as e:
        raise WikipediaError(f"Vikipedi'ye ulaşılamadı: {getattr(e, 'reason', e)}") from None
    except ValueError:
        raise WikipediaError("Vikipedi geçersiz yanıt döndürdü") from None
    if not isinstance(data, dict):
        raise WikipediaError("Vikipedi geçersiz yanıt döndürdü")
    if "error" in data:                      # API hatasi 200 ile gelir: {"error": {"code": ..., "info": ...}}
        raise WikipediaError("Vikipedi hatası: " + str(data["error"].get("info", ""))[:200])
    return data


def _plain(snippet: str) -> str:
    """Arama ozetindeki <span class="searchmatch"> gibi HTML etiketlerini ve &quot; gibi kacislari temizler.
    Arayuz metni textContent ile yazdigi icin bu yalnizca okunurluk icindir (guvenlik arayuzde)."""
    return html.unescape(re.sub(r"<[^>]+>", "", snippet or "")).strip()


def search(lang: str, query: str, limit: int = 5) -> list:
    """Baslik ve icerige gore makale arar; en fazla `limit` sonuc dondurur."""
    lang = _check_lang(lang)
    query = (query or "").strip()
    if not query:
        raise WikipediaInputError("Arama metni boş olamaz")
    if len(query) > MAX_QUERY_LENGTH:
        raise WikipediaInputError(f"Arama metni en fazla {MAX_QUERY_LENGTH} karakter olabilir")
    limit = max(1, min(int(limit), MAX_RESULTS))
    data = _get(lang, {"action": "query", "list": "search", "srsearch": query, "srlimit": limit,
                       "srnamespace": 0, "srprop": "snippet"})
    hits = (data.get("query") or {}).get("search") or []
    return [{"title": h.get("title", ""), "snippet": _plain(h.get("snippet")), "pageid": h.get("pageid")}
            for h in hits if h.get("title")]


def article_url(lang: str, title: str) -> str:
    return f"https://{lang}.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))


def fetch_article(lang: str, title: str) -> dict:
    """Makalenin tamamini duz metin olarak getirir (bolum basliklari satir olarak kalir).

    redirects=1: "Ataturk" gibi yonlendirme basliklari asil makaleye cevrilir.
    """
    lang = _check_lang(lang)
    title = (title or "").strip()
    if not title:
        raise WikipediaInputError("Makale başlığı boş olamaz")
    if len(title) > MAX_QUERY_LENGTH:
        raise WikipediaInputError(f"Makale başlığı en fazla {MAX_QUERY_LENGTH} karakter olabilir")
    data = _get(lang, {"action": "query", "prop": "extracts", "explaintext": 1, "exsectionformat": "plain",
                       "titles": title, "redirects": 1})
    pages = (data.get("query") or {}).get("pages") or []
    page = pages[0] if pages else {}
    if not page or page.get("missing") or page.get("invalid"):
        raise WikipediaNotFoundError(f"Vikipedi'de \"{title}\" başlıklı makale bulunamadı")
    text = (page.get("extract") or "").strip()
    if not text:
        raise WikipediaNotFoundError(f"\"{title}\" makalesinde metin yok")
    real_title = page.get("title") or title
    return {"title": real_title, "url": article_url(lang, real_title), "text": text}


def as_document_text(article: dict) -> str:
    """Belgeye yazilacak metin: once kaynak ve lisans (CC BY-SA kaynak gostermeyi sart kosar), sonra makale."""
    return (f"{article['title']}\n"
            f"Kaynak: Vikipedi, {article['url']} (CC BY-SA 4.0)\n\n"
            f"{article['text']}\n")
