""".env dosyasini asagidaki SABLON'dan olusturur ve SECRET_KEY'i rastgele uretir.

Calistirma:  python -m scripts.env_olustur
.env zaten varsa DOKUNMAZ (icindeki API anahtarin silinmesin diye).

Depoda ayri bir .env.example dosyasi yok: sablon burada. Yazilmayan her ayar app/core/config.py'deki varsayilani
kullanir; tum ayarlarin listesi README'deki "Ortam degiskenleri" tablosunda.
Bu sablona ASLA gercek anahtar yazilmaz (depoya gider); gercek degerler yalnizca .env'e yazilir.
"""
import secrets
import sys
from pathlib import Path

SABLON = """\
# Belge Tabanli Soru Asistani yerel ayarlari. Bu dosya git'e GIRMEZ (.gitignore). Gercek anahtarlarini yalnizca buraya yaz.
# Tum ayarlar ve varsayilanlari: README.md -> "Ortam degiskenleri"
APP_ENV=development
SECRET_KEY={secret_key}
DATABASE_URL=sqlite:///./data/asistan.db

# Embedding: local (sentence-transformers, ilk seferde model iner) | hf (Hugging Face) | hash (yalnizca deneme)
EMBEDDING_BACKEND=local
MAX_UPLOAD_MB=500
MAX_CHUNKS_PER_DOCUMENT=20000

# Sohbetin yanit ureten dil modeli: groq (ucretsiz katman) | claude
LLM_PROVIDER=groq
GROQ_API_KEY=
ANTHROPIC_API_KEY=

# Kayit dogrulama ve "Sifremi unuttum" e-postasi. Bos kalirsa gelistirmede kod sunucu penceresine yazilir.
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
"""


def olustur(kok: Path = Path(".")) -> bool:
    hedef = kok / ".env"
    if hedef.exists():
        return False
    hedef.write_text(SABLON.format(secret_key=secrets.token_hex(32)), encoding="utf-8")
    return True


if __name__ == "__main__":
    if olustur():
        print(".env olusturuldu (SECRET_KEY uretildi). API anahtarini istersen .env icine kendin yaz.")
    else:
        print(".env zaten var, dokunulmadi.")
    sys.exit(0)
