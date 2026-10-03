"""Testlerde agir/indirme gerektiren embedding modeli yerine hizli 'hash' yedegi kullanilir."""
from app.core import config

config.EMBEDDING_BACKEND = "hash"
# Testler .env'deki gercek anahtardan bagimsiz olsun; 32+ karakter (PyJWT kisa anahtar uyarisi vermesin).
config.SECRET_KEY = "test-anahtari-yalnizca-testlerde-kullanilir-0123456789"
# E-posta dogrulamasi yalnizca test_eposta_dogrulama.py'de acilir; diger testler (belge, arama, sohbet ...)
# kayit olup hemen giris yapabilsin. Dogrulamanin kendisi o dosyada uctan uca denenir.
config.REQUIRE_EMAIL_VERIFICATION = False
