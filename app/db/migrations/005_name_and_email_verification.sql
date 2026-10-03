-- 005: Ad soyad, e-posta dogrulama ve tek tablo "e-posta kodlari"
-- Kayit olurken kullanicinin adi alinir ve e-posta adresinin gercekten ona ait oldugu 6 haneli kodla dogrulanir.
-- Dogrulama kodu ile parola sifirlama kodu ayni kurallarla calisir (HMAC ozeti, sure, deneme siniri);
-- bu yuzden iki ayri tablo yerine tek tablo + "purpose" (amac) sutunu kullanilir. 004'teki password_resets
-- tablosu bu tabloya katilir. Bekleyen sifirlama kodlari (en fazla 15 dk'lik) kaybolur; kullanici yenisini ister.

ALTER TABLE users ADD COLUMN full_name TEXT NOT NULL DEFAULT '';
ALTER TABLE users ADD COLUMN email_verified_at TEXT;          -- NULL = e-posta henuz dogrulanmadi
-- Bu ozellikten ONCE acilmis hesaplar (yonetici dahil) dogrulanmis sayilir; yoksa hicbiri giris yapamazdi.
UPDATE users SET email_verified_at = created_at;

CREATE TABLE email_codes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    purpose    TEXT NOT NULL CHECK (purpose IN ('verify', 'reset')),   -- e-posta dogrulama | parola sifirlama
    code_hash  TEXT NOT NULL,
    expires_at INTEGER NOT NULL,              -- Unix zamani (saniye)
    attempts   INTEGER NOT NULL DEFAULT 0,    -- yanlis kod denemesi; sinira ulasinca kod gecersiz
    created_at INTEGER NOT NULL
);
CREATE INDEX idx_email_codes_user ON email_codes(user_id, purpose);

DROP TABLE password_resets;
