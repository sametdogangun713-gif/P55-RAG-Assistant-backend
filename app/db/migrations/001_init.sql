-- 001: Ilk sema (Hafta 3'teki ER diyagramindan)

CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename    TEXT NOT NULL,
    stored_name TEXT,
    mime_type   TEXT,
    size_bytes  INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'uploaded'
                CHECK (status IN ('uploaded', 'chunked', 'indexed', 'failed')),
    error       TEXT,
    uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_documents_user ON documents(user_id);

CREATE TABLE chunks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content     TEXT NOT NULL,
    page_no     INTEGER,
    UNIQUE (document_id, chunk_index)
);

CREATE TABLE embeddings (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id INTEGER NOT NULL UNIQUE REFERENCES chunks(id) ON DELETE CASCADE,
    vector   BLOB NOT NULL,
    dim      INTEGER NOT NULL,
    model    TEXT NOT NULL
);

CREATE TABLE conversations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title      TEXT NOT NULL DEFAULT 'Yeni sohbet',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_conversations_user ON conversations(user_id);

CREATE TABLE messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);

-- N-N: bir cevap birden cok parcaya dayanir, bir parca birden cok cevapta kaynak olur
CREATE TABLE message_sources (
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    chunk_id   INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    score      REAL,
    PRIMARY KEY (message_id, chunk_id)
);
CREATE INDEX idx_message_sources_chunk ON message_sources(chunk_id);
