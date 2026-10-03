"""Embedding: metni, anlamini temsil eden sabit uzunluklu bir vektore cevirir.

Uc arka uc (.env -> EMBEDDING_BACKEND):
- LocalEmbedder   : sentence-transformers (yerel, ucretsiz, cok dilli) -> kendi bilgisayarinda
- HFEmbedder      : AYNI model, Hugging Face'in sunucusunda (HTTP) -> bulutta (Vercel'e torch ve model sigmaz)
- HashingEmbedder : indirme gerektirmeyen, kelime/harf-n-gram tabanli basit yedek -> testler ve hizli deneme
Tum vektorler L2-normalizedir; bu yuzden iki vektorun nokta carpimi = kosinus benzerligidir.
"""
import json
import math
import re
import socket
import time
import urllib.error
import urllib.request
import zlib
from collections import Counter

import numpy as np

from app.core import config


class EmbeddingError(Exception):
    """Embedding uretilemedi (model yok, indirilemedi, calisirken hata)."""


def tr_lower(text: str) -> str:
    """Turkce'ye duyarli kucuk harf: 'I' -> 'i' degil 'ı', 'İ' -> 'i'."""
    return text.replace("İ", "i").replace("I", "ı").lower().replace("\u0307", "")


_STOPWORDS = {
    "ve", "bir", "bu", "da", "de", "ile", "icin", "için", "mi", "mı", "mu", "mü", "ne", "nasil", "nasıl",
    "ama", "gibi", "cok", "çok", "daha", "en", "o", "su", "şu", "ya", "veya", "ki", "olan", "olarak",
    "her", "tum", "tüm", "ise", "ben", "sen", "biz",
}


class Embedder:
    name = "base"

    def embed_documents(self, texts) -> np.ndarray:
        raise NotImplementedError

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed_documents([text])[0]


class HashingEmbedder(Embedder):
    """Kelimeler, kelime ciftleri ve harf 4-gramlari 'hashing trick' ile sabit boyutlu vektore doner.

    Anlamsal degil BICIMSEL benzerlik yakalar (ortak kelime/kok). Agglutinative Turkce icin harf
    n-gramlari kok benzerligini (kitap/kitabi) kismen yakalar.
    """
    def __init__(self, dim: int = 1024):
        self.dim = dim
        self.name = f"hash-v1-{dim}"

    def _features(self, text: str) -> list:
        tokens = [t for t in re.findall(r"\w+", tr_lower(text)) if len(t) > 1 and t not in _STOPWORDS]
        feats = list(tokens)
        feats += [a + "_" + b for a, b in zip(tokens, tokens[1:])]
        for t in tokens:
            w = f"#{t}#"
            feats += [w[i:i + 4] for i in range(len(w) - 3)]
        return feats

    def _vector(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        for feat, count in Counter(self._features(text)).items():
            v[zlib.crc32(feat.encode("utf-8")) % self.dim] += 1.0 + math.log(count)   # crc32: calistirmalar arasi sabit
        norm = float(np.linalg.norm(v))
        return v / norm if norm > 0 else v

    def embed_documents(self, texts) -> np.ndarray:
        return np.vstack([self._vector(t) for t in texts]).astype(np.float32)


class LocalEmbedder(Embedder):
    def __init__(self, model_name=None):
        self.model_name = model_name or config.EMBEDDING_MODEL
        self.name = "local:" + self.model_name
        self._model = None

    def _load(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise EmbeddingError(
                "sentence-transformers kurulu değil. 'pip install sentence-transformers' çalıştırın "
                "ya da .env dosyasında EMBEDDING_BACKEND=hash yapın."
            ) from e
        try:
            model = SentenceTransformer(self.model_name)
        except Exception as e:
            raise EmbeddingError(f"Embedding modeli yüklenemedi ({self.model_name}): {e}") from e
        model.max_seq_length = 256
        self._model = model

    def _encode(self, texts, prefix="") -> np.ndarray:
        self._load()
        if "e5" in self.model_name.lower():       # e5 modelleri 'query: ' / 'passage: ' on eki ister
            texts = [prefix + t for t in texts]
        try:
            arr = self._model.encode(list(texts), normalize_embeddings=True, convert_to_numpy=True,
                                     show_progress_bar=False, batch_size=32)
        except Exception as e:
            raise EmbeddingError(f"Embedding üretilemedi: {e}") from e
        return np.asarray(arr, dtype=np.float32)

    def embed_documents(self, texts) -> np.ndarray:
        return self._encode(texts, "passage: ")

    def embed_query(self, text: str) -> np.ndarray:
        return self._encode([text], "query: ")[0]


class HFEmbedder(Embedder):
    """Hugging Face Inference API ile embedding (POST .../models/<model>/pipeline/feature-extraction).

    Varsayilan model BAAI/bge-m3 (config.EMBEDDING_MODEL). Once yereldeki MiniLM kullaniliyordu; ancak sunucu onu
    128 token'da kesiyordu ve Turkce 600 karakter 128 token'i asiyordu -> parcanin ikinci yarisi aranamiyordu
    (gercek hata: "Odev teslim tarihi" sorusu bulunamadi). bge-m3 8192 token alir. Bedeli hiz: ~10 parca/sn
    (MiniLM ~40); paralel istek hizlandirmiyor (sunucu siraya koyuyor). Anahtar (HF_TOKEN) hata mesajina asla yazilmaz.
    """
    RETRY_STATUS = {429, 500, 502, 503, 504}         # 503: model sunucuda henuz yukleniyor

    def __init__(self, model_name=None, token=None, base_url=None, timeout=None, max_retries=3, sleep=time.sleep):
        self.model_name = model_name or config.EMBEDDING_MODEL
        self.name = "hf:" + self.model_name
        self.token = config.HF_TOKEN if token is None else token
        self.base_url = (base_url or config.HF_BASE_URL).rstrip("/")
        self.timeout = config.HF_TIMEOUT_SECONDS if timeout is None else timeout
        self.max_retries = max_retries
        self._sleep = sleep                              # testlerde gercekten beklememek icin

    def _repo_id(self) -> str:
        """'paraphrase-...' -> 'sentence-transformers/paraphrase-...' (Hugging Face'teki tam ad)."""
        return self.model_name if "/" in self.model_name else "sentence-transformers/" + self.model_name

    def _request(self, texts) -> urllib.request.Request:
        url = f"{self.base_url}/models/{self._repo_id()}/pipeline/feature-extraction"
        body = json.dumps({"inputs": list(texts), "normalize": True, "truncate": True}).encode("utf-8")
        return urllib.request.Request(url, data=body, method="POST", headers={
            "Authorization": "Bearer " + self.token, "Content-Type": "application/json",
            "User-Agent": "P55-RAG-Assistant/1.0"})

    def _post(self, texts):
        for attempt in range(self.max_retries + 1):
            last = attempt >= self.max_retries
            try:
                with urllib.request.urlopen(self._request(texts), timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code in self.RETRY_STATUS and not last:
                    self._sleep(min(2 ** attempt, 8))
                    continue
                if e.code in (401, 403):
                    raise EmbeddingError("Hugging Face anahtarı (HF_TOKEN) geçersiz veya yetkisiz") from None
                raise EmbeddingError(f"Hugging Face embedding hatası ({e.code})") from None
            except (socket.timeout, TimeoutError, urllib.error.URLError) as e:
                if not last:
                    self._sleep(min(2 ** attempt, 8))
                    continue
                raise EmbeddingError(f"Hugging Face'e ulaşılamadı: {getattr(e, 'reason', e)}") from None
            except ValueError:
                raise EmbeddingError("Hugging Face yanıtı JSON değil") from None

    def embed_documents(self, texts) -> np.ndarray:
        texts = list(texts)
        if not self.token:
            raise EmbeddingError("HF_TOKEN ayarlı değil (.env dosyasına ya da Vercel ortam değişkenlerine ekleyin)")
        data = self._post(texts)
        try:
            arr = np.asarray(data, dtype=np.float32)
        except (TypeError, ValueError):
            raise EmbeddingError("Hugging Face yanıtı beklenen biçimde değil") from None
        if arr.ndim != 2 or arr.shape[0] != len(texts):
            raise EmbeddingError(f"Hugging Face yanıtı beklenen biçimde değil (boyut {arr.shape})")
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        return arr / np.where(norms > 0, norms, 1.0)    # normalize: nokta carpimi = kosinus (sunucuya guvenme)


_cache = {}


def get_embedder() -> Embedder:
    """Ayara gore (EMBEDDING_BACKEND) tek bir ornek uretir ve yeniden kullanir (model bir kez yuklenir)."""
    key = (config.EMBEDDING_BACKEND, config.EMBEDDING_MODEL)
    if key not in _cache:
        if config.EMBEDDING_BACKEND == "hash":
            _cache[key] = HashingEmbedder()
        elif config.EMBEDDING_BACKEND == "local":
            _cache[key] = LocalEmbedder()
        elif config.EMBEDDING_BACKEND == "hf":
            _cache[key] = HFEmbedder()
        else:
            raise EmbeddingError(f"Bilinmeyen EMBEDDING_BACKEND: {config.EMBEDDING_BACKEND}")
    return _cache[key]
