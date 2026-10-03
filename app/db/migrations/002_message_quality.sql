-- 002: Cevap kalitesi ve kaynak numarasi (Hafta 11)
-- assistant mesajlari icin: durum (answered/no_context/no_info/unverified), kaynaga dayali mi, gecikme, en iyi skor
ALTER TABLE messages ADD COLUMN status TEXT;
ALTER TABLE messages ADD COLUMN grounded INTEGER;
ALTER TABLE messages ADD COLUMN latency_ms INTEGER;
ALTER TABLE messages ADD COLUMN best_score REAL;
-- yanittaki [n] isaretinin hangi kaynaga karsilik geldigi
ALTER TABLE message_sources ADD COLUMN n INTEGER;
