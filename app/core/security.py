"""Parola hash'leme (scrypt + tuz) ve imzali oturum token'i (JWT, HS256)."""
import base64
import hashlib
import hmac
import os
import time

import jwt

from app.core import config

_SCRYPT_N, _SCRYPT_R, _SCRYPT_P = 2 ** 14, 8, 1


class TokenError(Exception):
    """Token gecersiz, bozuk ya da suresi dolmus."""


def hash_password(password: str) -> str:
    """Her parola icin rastgele TUZ uretir; 'scrypt$n$r$p$tuz$hash' bicininde saklanir.

    Parola duz metin saklanmaz. Tuz sayesinde ayni parola iki kullanicida farkli hash uretir.
    scrypt bilerek yavas ve bellek-yogundur: kaba kuvvet denemesini pahalilastirir.
    """
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32)
    b64 = lambda b: base64.b64encode(b).decode("ascii")
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${b64(salt)}${b64(dk)}"


def verify_password(password: str, stored: str) -> bool:
    if not isinstance(stored, str):
        return False
    try:
        scheme, n, r, p, salt_b64, hash_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        dk = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(dk, expected)   # sabit zamanli karsilastirma


def create_access_token(user_id: int, role: str, expires_minutes=None) -> str:
    minutes = config.ACCESS_TOKEN_EXPIRE_MINUTES if expires_minutes is None else expires_minutes
    now = int(time.time())
    payload = {"sub": str(user_id), "role": role, "iat": now, "exp": now + int(minutes * 60)}
    return jwt.encode(payload, config.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """Imzayi ve son kullanma suresini dogrular. Gecersizse TokenError."""
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"], options={"require": ["exp", "sub"]})
    except jwt.PyJWTError as e:
        raise TokenError(str(e)) from e
