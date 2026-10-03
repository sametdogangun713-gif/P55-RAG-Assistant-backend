-- 003: Uzun sohbetler icin ozet (Hafta 11)
ALTER TABLE conversations ADD COLUMN summary TEXT;
-- ozete dahil edilen son mesajin id'si (bundan eski mesajlar baglama tekrar eklenmez)
ALTER TABLE conversations ADD COLUMN summary_upto INTEGER NOT NULL DEFAULT 0;
