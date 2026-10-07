"""Veritabani baglantisi ve migration (surum gecisi) calistirici.

Iki veritabani desteklenir, hangisi kullanilacagini DATABASE_URL secer:
- sqlite:///./data/asistan.db      -> yerel gelistirme ve testler (kurulum gerektirmez)
- postgresql://...             -> bulut (Supabase). Vercel'in diski kalici olmadigi icin SQLite dosyasi orada yasayamaz.

Depo (repository) modulleri iki veritabaninda da AYNI SQL'i kullanir: `?` yer tutucusu, `RETURNING id`,
`ON CONFLICT`. PostgreSQL tarafinda bu farklar PgConnection sinifinda kapatilir; boylece servisler hangi
veritabaninin kullanildigini bilmez (katmanli mimari: api -> services -> db).
"""
import sqlite3
from pathlib import Path

from app.core import config

MIGRATIONS_DIR = Path(__file__).parent / "migrations"           # SQLite: 001_init.sql, 002_..., ...
PG_MIGRATIONS_DIR = MIGRATIONS_DIR / "postgres"                   # PostgreSQL: ayni sema, PostgreSQL lehcesiyle
MIGRATION_LOCK_ID = 5555                                          # ayni anda iki sunucu migration yapmasin

try:                                    # PostgreSQL surucusu yalnizca bulutta/Postgres testinde gerekir
    import psycopg
except ImportError:                     # pragma: no cover - yerelde kurulu olmayabilir
    psycopg = None

# Iki veritabaninin "kisit ihlali" hatalari (UNIQUE, CHECK, FOREIGN KEY) tek isimle yakalanabilsin
IntegrityError = (sqlite3.IntegrityError,) + ((psycopg.IntegrityError,) if psycopg else ())
DatabaseError = (sqlite3.Error,) + ((psycopg.Error,) if psycopg else ())


class Row(tuple):
    """sqlite3.Row gibi davranan satir: hem row[0] hem row['email'] hem de dict(row) calisir."""

    def __new__(cls, names, values):
        row = super().__new__(cls, values)
        row._names = names
        return row

    def __getitem__(self, key):
        if isinstance(key, str):
            return tuple.__getitem__(self, self._names.index(key))
        return tuple.__getitem__(self, key)

    def keys(self):
        return list(self._names)


def _row_factory(cursor):
    """psycopg her sorgu icin satir ureticisi ister; sutun adlarini bir kez alip Row nesnesi uretir."""
    if cursor.description is None:          # INSERT/UPDATE gibi sonuc dondurmeyen komutlar
        return lambda values: values
    names = [c.name for c in cursor.description]
    return lambda values: Row(names, values)


def _to_pg(sql: str) -> str:
    """SQLite yer tutucusu `?` -> psycopg yer tutucusu `%s`. SQL'deki gercek `%` (LIKE '%a%') `%%` olur."""
    return sql.replace("%", "%%").replace("?", "%s")


class PgConnection:
    """psycopg baglantisini sqlite3.Connection gibi kullandiran ince sarmalayici.

    Depo kodunun kullandigi kadarini taklit eder: execute, executemany, commit, rollback, close,
    `with conn:` (hata yoksa commit, varsa rollback). Satirlar Row nesnesidir.
    """
    dialect = "postgres"

    def __init__(self, raw):
        self._raw = raw

    def execute(self, sql, params=None):
        cur = self._raw.cursor(row_factory=_row_factory)
        if params:
            cur.execute(_to_pg(sql), list(params))
        else:
            cur.execute(sql)                # parametresiz: SQL oldugu gibi gider (birden cok komut da olabilir)
        return cur

    def executemany(self, sql, seq):
        cur = self._raw.cursor()
        rows = [list(p) for p in seq]
        if rows:
            cur.executemany(_to_pg(sql), rows)
        return cur

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        self._raw.close()

    @property
    def in_transaction(self) -> bool:
        return self._raw.info.transaction_status != psycopg.pq.TransactionStatus.IDLE

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        return False


def dialect(conn) -> str:
    """'sqlite' ya da 'postgres' (vektor aramasi gibi lehceye ozel yerlerde kullanilir)."""
    return getattr(conn, "dialect", "sqlite")


def get_connection(db_path=None):
    """Yeni bir baglanti acar. Satirlar sozluk gibi okunur (row['email']).

    db_path verilirse (testler) her zaman SQLite kullanilir.
    SQLite:
    - foreign_keys: SQLite'ta yabanci anahtar kontrolu varsayilan KAPALIDIR, her baglantida acilmali.
    - check_same_thread=False: FastAPI istegi farkli is parcaciklarinda calistirabilir.
    PostgreSQL:
    - prepare_threshold=None: Supabase'in baglanti havuzu (transaction modu, port 6543) hazir sorgulari
      (prepared statement) baglantilar arasinda tasiyamaz; kapatmazsak rastgele hatalar olur.
    """
    if db_path is None and config.is_postgres():
        if psycopg is None:
            raise RuntimeError("PostgreSQL için 'psycopg' paketi gerekli: pip install -r requirements.txt")
        raw = psycopg.connect(config.DATABASE_URL, prepare_threshold=None,
                              connect_timeout=config.DB_CONNECT_TIMEOUT)
        return PgConnection(raw)
    path = db_path or config.db_path()
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _applied(conn) -> set:
    return {r["version"] for r in conn.execute("SELECT version FROM schema_migrations")}


def _run_pg_migrations(conn) -> list:
    """PostgreSQL: tum bekleyen migration'lar TEK islemde ve bir kilit altinda uygulanir.

    Vercel'de ayni anda birden cok sunucu ornegi acilabilir; pg_advisory_xact_lock ikincisini birincisi
    bitene kadar bekletir, o da tablolari hazir bulur ve hicbir sey yapmaz.
    """
    newly = []
    try:
        conn.execute(f"SELECT pg_advisory_xact_lock({MIGRATION_LOCK_ID})")
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations ("
                     " version TEXT PRIMARY KEY,"
                     " applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
        conn.execute("ALTER TABLE schema_migrations ENABLE ROW LEVEL SECURITY")
        applied = _applied(conn)
        for f in sorted(PG_MIGRATIONS_DIR.glob("*.sql")):
            if f.stem in applied:
                continue
            conn.execute(f.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (f.stem,))
            newly.append(f.stem)
        conn.commit()                       # kilit de burada birakilir
    except Exception:
        conn.rollback()
        raise
    return newly


def run_migrations(conn) -> list:
    """migrations/ klasorundeki henuz uygulanmamis .sql dosyalarini sirayla calistirir.

    Uygulanan surumler `schema_migrations` tablosunda tutulur; ayni dosya iki kez calismaz.
    Her migration tek bir islem (BEGIN..COMMIT) icindedir: yarida hata olursa geri alinir.
    """
    if dialect(conn) == "postgres":
        return _run_pg_migrations(conn)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        " version TEXT PRIMARY KEY,"
        " applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.commit()
    applied = _applied(conn)
    newly = []
    for f in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if f.stem in applied:
            continue
        sql = f.read_text(encoding="utf-8")
        try:
            conn.executescript("BEGIN;\n" + sql + "\nCOMMIT;")
            conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (f.stem,))
            conn.commit()
        except Exception:
            if conn.in_transaction:
                conn.rollback()
            raise
        newly.append(f.stem)
    return newly


def init_db(db_path=None) -> list:
    """Baglanti ac, migration'lari uygula, kapat. Uygulama acilisinda cagrilir."""
    conn = get_connection(db_path)
    try:
        return run_migrations(conn)
    finally:
        conn.close()
