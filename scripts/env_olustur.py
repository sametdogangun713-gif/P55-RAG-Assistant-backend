""".env dosyasini .env.example'dan olusturur ve SECRET_KEY'i rastgele uretir.

Calistirma:  python -m scripts.env_olustur
.env zaten varsa DOKUNMAZ (icindeki API anahtarin silinmesin diye).
"""
import re
import secrets
import sys
from pathlib import Path


def olustur(kok: Path = Path(".")) -> bool:
    hedef = kok / ".env"
    if hedef.exists():
        return False
    metin = (kok / ".env.example").read_text(encoding="utf-8")
    metin = re.sub(r"(?m)^SECRET_KEY=.*$", "SECRET_KEY=" + secrets.token_hex(32), metin)
    hedef.write_text(metin, encoding="utf-8")
    return True


if __name__ == "__main__":
    if olustur():
        print(".env olusturuldu (SECRET_KEY uretildi). API anahtarini istersen .env icine kendin yaz.")
    else:
        print(".env zaten var, dokunulmadi.")
    sys.exit(0)
