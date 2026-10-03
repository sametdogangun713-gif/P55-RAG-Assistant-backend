-- 004: Parola sifirlama kodlari (Hafta 14)
-- Kodun kendisi saklanmaz, yalnizca HMAC ozeti (veritabani ele gecse bile kod okunamaz).
-- Bir kullanicinin ayni anda tek gecerli kodu olur; yeni kod istenince eskisi silinir.

CREATE TABLE password_resets (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash  TEXT NOT NULL,
    expires_at INTEGER NOT NULL,              -- Unix zamani (saniye); karsilastirmasi kolay
    attempts   INTEGER NOT NULL DEFAULT 0,    -- yanlis kod denemesi; sinira ulasinca kod gecersiz
    created_at INTEGER NOT NULL
);
CREATE INDEX idx_password_resets_user ON password_resets(user_id);
