"""Testlerde agir/indirme gerektiren embedding modeli yerine hizli 'hash' yedegi kullanilir."""
from app.core import config

config.EMBEDDING_BACKEND = "hash"
# Testler .env'deki gercek anahtardan bagimsiz olsun; 32+ karakter (PyJWT kisa anahtar uyarisi vermesin).
config.SECRET_KEY = "test-anahtari-yalnizca-testlerde-kullanilir-0123456789"
