-- 006: Kisisel API anahtarlari (personal access token)
-- Kullanici "Hesabim"dan bir anahtar (orn. p55_Xy12...) uretir; Postman, bir betik ya da baska bir uygulama
-- (3. parti) bu anahtarla "Authorization: Bearer p55_..." basligini gondererek P55 API'sine baglanir.
-- Anahtarin KENDISI saklanmaz, yalnizca SHA-256 ozeti saklanir (parola gibi): veritabani sizsa bile anahtarlar
-- kullanilamaz. Anahtar kullaniciya yalnizca uretildigi anda bir kez gosterilir.

CREATE TABLE api_tokens (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,   -- hesap silinince anahtarlar da gider
    name         TEXT NOT NULL,                  -- kullanicinin verdigi ad: "Postman", "Telegram botu" ...
    prefix       TEXT NOT NULL,                  -- ilk 12 karakter (p55_Xy12abcd): listede hangi anahtar oldugu anlasilsin
    token_hash   TEXT NOT NULL UNIQUE,           -- SHA-256 (hex); her istekte bu sutunla aranir
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TEXT,                           -- NULL = hic kullanilmadi
    expires_at   TEXT NOT NULL                   -- 'YYYY-MM-DD HH:MM:SS' (UTC); suresiz anahtar yok
);
CREATE INDEX idx_api_tokens_user ON api_tokens(user_id);
