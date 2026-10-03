"""LLM istemcileri (REST). Yalnizca standart kutuphane (urllib) kullanir.

Iki saglayici desteklenir, hangisinin kullanilacagini .env'deki LLM_PROVIDER secer:
  - ClaudeClient: Anthropic Messages API   POST {base_url}/v1/messages
  - GroqClient:   OpenAI uyumlu Groq API    POST {base_url}/chat/completions  (ucretsiz katman var)
Ikisi de ayni arayuzu sunar: complete(system, messages, max_tokens) -> yanit metni.

Ortak hata yonetimi (_HTTPLLMClient): zaman asimi, gecici hatalarda (429/5xx) ustel geri cekilmeyle yeniden
deneme, kalici hatalarda (400/401/403/404) hemen anlasilir bir istisna. API anahtari hata mesajina ASLA yazilmaz.
"""
import json
import re
import socket
import time
import urllib.error
import urllib.request

from app.core import config

API_VERSION = "2023-06-01"
RETRY_STATUS = {429, 500, 502, 503, 504, 529}      # gecici hatalar: yeniden denenir
USER_AGENT = "P55-RAG-Assistant/1.0"                # bazi API'ler varsayilan 'Python-urllib' istemcisini engelliyor
_THINK = re.compile(r"<think>.*?(</think>|$)", re.DOTALL)   # bazi "dusunen" modeller dusuncesini yanita boyle karistirir


class LLMError(Exception):
    """LLM cagrisi basarisiz."""


class LLMConfigError(LLMError):
    """Ayar eksik (ornegin API anahtari yok)."""


class LLMTimeoutError(LLMError):
    """Sunucu zamaninda yanit vermedi."""


class LLMRateLimitError(LLMError):
    """Hiz siniri (429) asildi ve yeniden denemeler yetmedi."""


class LLMAPIError(LLMError):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class _HTTPLLMClient:
    """Saglayicidan bagimsiz kisim: dogrulama, yeniden deneme, hata cevirme.

    Alt siniflar yalnizca sunlari tanimlar: provider_name, key_env_name, _payload(...), _request(payload),
    _extract(data). Boylece yeni bir saglayici eklemek yeniden deneme mantigini kopyalamayi gerektirmez.
    """
    provider_name = "LLM"
    key_env_name = "API_KEY"

    def __init__(self, api_key, model, base_url, timeout=None, max_retries=None, backoff_base=1.0, sleep=time.sleep):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = config.LLM_TIMEOUT_SECONDS if timeout is None else timeout
        self.max_retries = config.LLM_MAX_RETRIES if max_retries is None else max_retries
        self.backoff_base = backoff_base
        self._sleep = sleep                  # testlerde gercekten beklememek icin disaridan verilebilir
        self.last_usage = None               # {'input_tokens': n, 'output_tokens': m} (saglayicidan bagimsiz)

    # ---- genel arayuz -------------------------------------------------
    def complete(self, system, messages, max_tokens=None) -> str:
        """system: sistem istemi (str). messages: [{'role': 'user'|'assistant', 'content': str}, ...]."""
        if not self.api_key:
            raise LLMConfigError(f"{self.key_env_name} ayarlı değil (.env dosyasına ekleyin)")
        self._validate(messages)
        raw = self._post_with_retry(self._payload(system, messages, max_tokens or config.LLM_MAX_TOKENS))
        return self._parse(raw)

    # ---- alt siniflarin dolduracagi kisimlar --------------------------
    def _payload(self, system, messages, max_tokens) -> dict:      # pragma: no cover
        raise NotImplementedError

    def _request(self, payload) -> urllib.request.Request:         # pragma: no cover
        raise NotImplementedError

    def _extract(self, data):                                       # pragma: no cover
        """Cozumlenmis JSON'dan (metin, kullanim) dondurur; bicim yanlissa KeyError/TypeError/IndexError atar."""
        raise NotImplementedError

    # ---- ic yardimcilar -----------------------------------------------
    @staticmethod
    def _validate(messages):
        if not isinstance(messages, list) or not messages:
            raise ValueError("messages bos olamaz")
        for m in messages:
            if not isinstance(m, dict) or m.get("role") not in ("user", "assistant") \
                    or not isinstance(m.get("content"), str) or not m["content"].strip():
                raise ValueError("Her mesaj {'role': 'user'|'assistant', 'content': dolu metin} olmali")
        if messages[0]["role"] != "user":
            raise ValueError("Ilk mesaj 'user' rolunde olmali")

    def _delay(self, attempt, retry_after=None) -> float:
        if retry_after:
            try:
                return min(float(retry_after), 10.0)       # sunucu 'Retry-After' diyorsa ona uy
            except ValueError:
                pass
        return min(self.backoff_base * (2 ** attempt), 8.0)  # 1s, 2s, 4s, ... (en fazla 8s)

    @staticmethod
    def _error_detail(e: urllib.error.HTTPError) -> str:
        try:
            data = json.loads(e.read().decode("utf-8", errors="replace"))
            return str(data.get("error", {}).get("message") or e.reason)[:300]
        except Exception:
            return str(e.reason)[:300]

    def _post_with_retry(self, payload) -> bytes:
        name = self.provider_name
        for attempt in range(self.max_retries + 1):
            last = attempt >= self.max_retries
            try:
                with urllib.request.urlopen(self._request(payload), timeout=self.timeout) as resp:
                    return resp.read()
            except urllib.error.HTTPError as e:
                status = e.code
                detail = self._error_detail(e)
                if status in RETRY_STATUS and not last:
                    self._sleep(self._delay(attempt, e.headers.get("retry-after") if e.headers else None))
                    continue
                if status == 429:
                    raise LLMRateLimitError(f"{name} API hız sınırı aşıldı, biraz sonra tekrar deneyin") from None
                raise LLMAPIError(f"{name} API hatası ({status}): {detail}", status) from None
            except (socket.timeout, TimeoutError):
                if not last:
                    self._sleep(self._delay(attempt))
                    continue
                raise LLMTimeoutError(f"{name} API {self.timeout:g} sn içinde yanıt vermedi") from None
            except urllib.error.URLError as e:
                if isinstance(e.reason, (socket.timeout, TimeoutError)):
                    if not last:
                        self._sleep(self._delay(attempt))
                        continue
                    raise LLMTimeoutError(f"{name} API {self.timeout:g} sn içinde yanıt vermedi") from None
                if not last:
                    self._sleep(self._delay(attempt))
                    continue
                raise LLMAPIError(f"{name} API'ye bağlanılamadı") from None
        raise LLMAPIError("Beklenmeyen durum")   # pragma: no cover

    def _parse(self, raw: bytes) -> str:
        try:
            text, usage = self._extract(json.loads(raw.decode("utf-8")))
        except (ValueError, KeyError, TypeError, IndexError, AttributeError):
            raise LLMAPIError(f"{self.provider_name} API yanıtı çözümlenemedi") from None
        text = (text or "").strip()
        if not text:
            raise LLMAPIError(f"{self.provider_name} API boş yanıt döndürdü")
        self.last_usage = usage
        return text


class ClaudeClient(_HTTPLLMClient):
    """Anthropic Messages API. Sistem istemi ayri 'system' alaninda gider."""
    provider_name = "Claude"
    key_env_name = "ANTHROPIC_API_KEY"

    def __init__(self, api_key=None, model=None, base_url=None, **kw):
        super().__init__(config.ANTHROPIC_API_KEY if api_key is None else api_key,
                         model or config.CLAUDE_MODEL, base_url or config.ANTHROPIC_BASE_URL, **kw)

    def _payload(self, system, messages, max_tokens) -> dict:
        return {"model": self.model, "max_tokens": max_tokens, "system": system, "messages": messages}

    def _request(self, payload) -> urllib.request.Request:
        return urllib.request.Request(
            self.base_url + "/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": API_VERSION,
                "content-type": "application/json",
                "user-agent": USER_AGENT,
            },
        )

    def _extract(self, data):
        blocks = data["content"]
        text = "".join(b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text")
        return text, data.get("usage")


class GroqClient(_HTTPLLMClient):
    """Groq'un OpenAI uyumlu Chat Completions API'si.

    Claude'dan farklari: anahtar 'Authorization: Bearer' basliginda gider; sistem istemi ayri alan degil,
    listenin basina eklenen {'role': 'system'} mesajidir; yanit choices[0].message.content icindedir.

    Groq'taki guncel modeller (gpt-oss, qwen3) "dusunen" modellerdir: once kendi kendine dusunur, sonra yanitlar.
    reasoning_effort='low' dusunmeyi kisa tutar (daha hizli, token butcesi yanita kalir). Bos birakilirsa
    gonderilmez (dusunmeyen bir modele gecilirse gerekir; yoksa API 400 doner).
    """
    provider_name = "Groq"
    key_env_name = "GROQ_API_KEY"

    def __init__(self, api_key=None, model=None, base_url=None, reasoning_effort=None, **kw):
        super().__init__(config.GROQ_API_KEY if api_key is None else api_key,
                         model or config.GROQ_MODEL, base_url or config.GROQ_BASE_URL, **kw)
        self.reasoning_effort = config.GROQ_REASONING_EFFORT if reasoning_effort is None else reasoning_effort

    def _payload(self, system, messages, max_tokens) -> dict:
        payload = {"model": self.model, "max_tokens": max_tokens,
                   "messages": [{"role": "system", "content": system}] + list(messages)}
        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort
        return payload

    def _request(self, payload) -> urllib.request.Request:
        return urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "authorization": f"Bearer {self.api_key}",
                "content-type": "application/json",
                "user-agent": USER_AGENT,
            },
        )

    def _extract(self, data):
        text = data["choices"][0]["message"]["content"]
        if text:
            text = _THINK.sub("", text)          # yanita karismis dusunce metni kullaniciya gosterilmez
        u = data.get("usage") or {}
        # Kullanimi Claude ile ayni adlara cevir: rapor/test kodu saglayiciyi bilmek zorunda kalmasin
        usage = {"input_tokens": u.get("prompt_tokens"), "output_tokens": u.get("completion_tokens")} if u else None
        return text, usage


PROVIDERS = {"claude": ClaudeClient, "groq": GroqClient}


def get_llm_client(provider=None) -> _HTTPLLMClient:
    """.env'deki LLM_PROVIDER'a gore istemci olusturur ('claude' | 'groq')."""
    name = (provider or config.LLM_PROVIDER or "").strip().lower()
    if name not in PROVIDERS:
        raise LLMConfigError(f"Bilinmeyen LLM_PROVIDER: '{name}' (geçerli: {', '.join(PROVIDERS)})")
    return PROVIDERS[name]()
