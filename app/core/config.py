"""Ayarlar ortam degiskenlerinden okunur (anahtarlar ve sifreler koda gomulmez).

Kullanim: `from app.core import config` ... `config.UPLOAD_DIR`
(Degeri cagri aninda okumak icin modul uzerinden eris; `from config import X` kullanma.)
"""
import os
import warnings

try:  # python-dotenv kuruluysa .env dosyasini yukle
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # pragma: no cover
    pass

# Vercel kendi sunucularinda VERCEL=1 tanimlar. Orada disk kalici degildir; yalnizca /tmp yazilabilir.
ON_VERCEL = bool(os.getenv("VERCEL"))

# Yerel: sqlite:///./data/asistan.db   Bulut (Supabase): postgresql://...:6543/postgres (Supabase -> Connect -> Transaction pooler)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/asistan.db").strip()   # panele yapistirirken sona Enter kacabiliyor
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR") or ("/tmp/uploads" if ON_VERCEL else "./uploads")


def is_postgres() -> bool:
    return DATABASE_URL.startswith(("postgresql://", "postgres://"))


def db_path() -> str:
    """'sqlite:///./data/asistan.db' -> './data/asistan.db' (':memory:' da desteklenir)."""
    prefix = "sqlite:///"
    if not DATABASE_URL.startswith(prefix):
        raise ValueError("DATABASE_URL bir SQLite adresi değil ('sqlite:///' ile başlamalı).")
    return DATABASE_URL[len(prefix):]

# --- Dagitim: frontend ayri bir adreste (Vercel) calisir ---
# Tarayicinin backend'e istek atmasina izin verilen adresler (CORS), virgulle ayrilir.
ALLOWED_ORIGINS = [o.strip().rstrip("/") for o in os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500").split(",") if o.strip()]

# --- Hafta 5: kimlik dogrulama ---
SECRET_KEY = os.getenv("SECRET_KEY", "degistir-bunu").strip()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
MIN_PASSWORD_LENGTH = 8
MAX_FAILED_LOGINS = 5          # bu kadar basarisiz denemeden sonra gecici kilit
LOCKOUT_SECONDS = 300
MIN_NAME_LENGTH = 2            # kayitta alinan ad soyad
MAX_NAME_LENGTH = 100
# Kayit olan kisi e-postasina gelen 6 haneli kodu girmeden giris yapamaz ("1" acik, "0" kapali).
# Kapali ise hesap kayit aninda dogrulanmis sayilir (SMTP'siz bir sunucuda denemek icin).
REQUIRE_EMAIL_VERIFICATION = os.getenv("REQUIRE_EMAIL_VERIFICATION", "1").strip() == "1"
VERIFY_CODE_MINUTES = int(os.getenv("VERIFY_CODE_MINUTES", "30"))
# Kisisel API anahtari (Hesabim -> API anahtarlari): bir kullanicinin ayni anda en fazla kac anahtari olabilir
MAX_API_TOKENS_PER_USER = int(os.getenv("MAX_API_TOKENS_PER_USER", "10"))

# --- Hafta 6: belge yukleme ve parcalama ---
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "500"))     # 10 -> 500 (dosya diske akitilarak yazilir); bulutta 50
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))        # karakter; yerel embedding modelinin token siniri icin makul
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))  # ardisik parcalar arasi ortak karakter (yaklasik)
ALLOWED_EXTENSIONS = (".txt", ".pdf", ".docx")
# Bir istekte en fazla kac saniye indekslenir (0 = sinirsiz, hepsi tek istekte). Vercel'de bir istek en fazla
# 300 sn; buyuk belge birden cok kisa istekte, kaldigi yerden devam ederek indekslenir (POST /documents/{id}/index-next).
INDEX_BUDGET_SECONDS = float(os.getenv("INDEX_BUDGET_SECONDS") or ("60" if ON_VERCEL else "0"))

# --- Hafta 7: embedding ve vektor arama ---
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "local")      # "local" | "hf" | "hash"
# "local": kucuk MiniLM bilgisayarda calisir. "hf": Hugging Face sunucusunda BAAI/bge-m3 (Vercel'de torch sigmaz).
# MiniLM sunucuda metni 128 token'da kesiyordu: Turkce 600 karakterlik parcanin ikinci yarisi aranamiyordu.
# bge-m3 8192 token alir ve Turkcede dogru parcayi daha iyi bulur (olcum: docs/istem-deneyleri.md). Anahtar yalnizca .env'de.
_DEFAULT_MODEL = {"hf": "BAAI/bge-m3"}
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL") or _DEFAULT_MODEL.get(EMBEDDING_BACKEND, "paraphrase-multilingual-MiniLM-L12-v2")
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
HF_BASE_URL = os.getenv("HF_BASE_URL", "https://router.huggingface.co/hf-inference")
HF_TIMEOUT_SECONDS = float(os.getenv("HF_TIMEOUT_SECONDS", "60"))
SEARCH_TOP_K = int(os.getenv("SEARCH_TOP_K", "5"))

# --- Hafta 9: harici API (Claude) ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()           # yalnizca ortam degiskeninden / .env'den
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
# Yanit ureten saglayici: "claude" (ucretli) | "groq" (OpenAI uyumlu, ucretsiz katmani var)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude").strip().lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()                     # yalnizca .env'den
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")              # llama modelleri Groq'tan kaldirildi (2026-10)
# Dusunen modeller icin: low|medium|high, bos = gonderme. "low" belgede yazan cevaplarda bile sik sik BILGI_YOK
# diyordu; "medium" ~1-3 sn daha yavas ama belirgin dogru (olcum: docs/istem-deneyleri.md).
GROQ_REASONING_EFFORT = os.getenv("GROQ_REASONING_EFFORT", "medium")

LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "800"))

# --- Hafta 10: RAG ---
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
# Esik yalnizca belgeyle HIC ilgisi olmayan sorulari ayiklar; "yanit belgede var mi" karari modelindir (BILGI_YOK).
# hf (bge-m3) olcumu: belgede olan sorularda en iyi skor >= 0,55; ilgisizlerde 0,3-0,56 -> 0,40 hicbir dogru soruyu kesmez.
_DEFAULT_MIN_SCORE = {"local": "0.30", "hf": "0.40", "hash": "0.15"}
MIN_SCORE = float(os.getenv("MIN_SCORE") or _DEFAULT_MIN_SCORE.get(EMBEDDING_BACKEND, "0.30"))
MAX_QUESTION_CHARS = 1000
# Sohbette belgelerde yanit yoksa (selamlasma, genel soru) model genel bilgisiyle kisa yanit verir; yanit
# "general" durumuyla, kaynaksiz ve arayuzde "belgelerinden degil" etiketiyle gosterilir. 0 = yalnizca belgeler.
GENERAL_CHAT = os.getenv("GENERAL_CHAT", "1") == "1"

# --- Hafta 11: sohbet gecmisi ve baglam ---
CHAT_HISTORY_CHARS = int(os.getenv("CHAT_HISTORY_CHARS", "4000"))   # bu uzunlugu asan gecmis ozetlenir
CHAT_KEEP_RECENT = int(os.getenv("CHAT_KEEP_RECENT", "6"))          # ozetlemede birebir korunan son mesaj sayisi
HISTORY_MSG_MAX_CHARS = 1500                                         # LLM'e giden tek gecmis mesaji siniri
SUMMARY_MAX_CHARS = 1500


# --- Hafta 13: sertlestirme ---
APP_ENV = os.getenv("APP_ENV", "development")                       # "production" ise zayif ayarlar baslatmayi engeller
MAX_DOCX_UNCOMPRESSED_MB = int(os.getenv("MAX_DOCX_UNCOMPRESSED_MB", "1024"))  # DOCX sikistirma bombasi onlemi (hafta 14: 50 -> 1024, 500 MB yukleme icin)

# --- Hafta 14: buyuk dosya / dagitim ---
# Dosya boyutu degil METIN miktari sinirlanir: 500 MB'lik gorsel agirlikli PDF'te metin azdir, ama 500 MB duz metin
# ~1 milyon parca eder (olcum: bu makinede ~43 parca/sn -> ~6 saat). 20 000 parca ~ 5 000 sayfa, en kotu ~8 dakika.
MAX_CHUNKS_PER_DOCUMENT = int(os.getenv("MAX_CHUNKS_PER_DOCUMENT", "20000"))

# --- Dagitim: dosya deposu ---
# "local"   : dosya backend'e gonderilir, sunucu diskine yazilir (yerel calisma)
# "supabase": tarayici dosyayi dogrudan Supabase Storage'a yukler, backend oradan okur. Vercel bir istekte
#             en fazla 4,5 MB kabul ettigi icin bulutta zorunlu.
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local").strip().lower()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")                 # https://<proje>.supabase.co
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()   # GIZLI: yalnizca .env / Vercel paneli
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "belgeler")
STORAGE_TIMEOUT_SECONDS = float(os.getenv("STORAGE_TIMEOUT_SECONDS", "60"))

# --- Hafta 14: parola sifirlama ---
RESET_CODE_MINUTES = int(os.getenv("RESET_CODE_MINUTES", "15"))    # kodun gecerlilik suresi
RESET_MAX_ATTEMPTS = 5             # bu kadar yanlis denemeden sonra kod gecersiz (6 hane = 1 milyon olasilik)
RESET_RESEND_SECONDS = 60          # ayni e-postaya bu sureden sik kod gonderilmez (posta kutusunu bombalama onlemi)
# Son iki sinir e-posta dogrulama kodu icin de gecerlidir (services/email_codes.py).
# E-posta (SMTP). Bos ise: gelistirmede kod sunucu penceresine yazilir, uretimde sifirlama kapali.
SMTP_HOST = os.getenv("SMTP_HOST", "")                              # Gmail: smtp.gmail.com
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))                      # 587 = STARTTLS, 465 = SSL
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")                      # Gmail: hesap parolasi DEGIL, "uygulama sifresi"
SMTP_FROM = os.getenv("SMTP_FROM", "")                              # bos ise SMTP_USER
# Vercel'de islev yanit gonderildikten sonra durdurulabilir; e-posta arka planda kalirsa hic gitmeyebilir.
SEND_EMAIL_INLINE = os.getenv("SEND_EMAIL_INLINE", "1" if ON_VERCEL else "0") == "1"


def check_secret_key() -> None:
    """Varsayilan/kisa SECRET_KEY ile token'lar taklit edilebilir: uretimde baslatmayi reddet, gelistirmede uyar."""
    if SECRET_KEY != "degistir-bunu" and len(SECRET_KEY) >= 32:
        return
    msg = ("SECRET_KEY zayıf veya varsayılan değerde. Şununla üretip .env dosyasına yazın: "
           "python -c \"import secrets; print(secrets.token_hex(32))\"")
    if APP_ENV == "production":
        raise RuntimeError(msg)
    warnings.warn(msg, UserWarning)
