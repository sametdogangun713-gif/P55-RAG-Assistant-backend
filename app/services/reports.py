"""Kullanim ve kaynak raporu: toplulastirma sorgulari ve CSV disa aktarma."""
import csv
import io
from datetime import datetime, timedelta, timezone

STATUSES = ("answered", "no_context", "no_info", "unverified", "general")   # general: belge disi genel sohbet


def _scope(user_id):
    """Kullanici filtresi: user_id None ise tum sistem (yonetici), degilse yalnizca o kullanici."""
    return ("", []) if user_id is None else (" AND c.user_id = ?", [user_id])


def _ratio(a, b):
    return round(a / b, 3) if b else None      # veri yoksa None (0 degil): "hic soru yok" ile "hepsi basarisiz"i karistirma


def usage_report(conn, user_id=None, days: int = 30, today=None) -> dict:
    if not 1 <= days <= 365:
        raise ValueError("days 1 ile 365 arasında olmalı")
    today = today or datetime.now(timezone.utc).date()
    start = today - timedelta(days=days - 1)
    start_s = start.isoformat()
    sc, sp = _scope(user_id)
    doc_scope, doc_params = ("", []) if user_id is None else (" WHERE d.user_id = ?", [user_id])

    def one(sql, params):
        return conn.execute(sql, params).fetchone()[0]

    # --- genel toplamlar (zamandan bagimsiz) ---
    totals = {
        "users": one("SELECT COUNT(*) FROM users", []) if user_id is None else None,
        "documents": one("SELECT COUNT(*) FROM documents d" + doc_scope, doc_params),
        "indexed_documents": one("SELECT COUNT(*) FROM documents d" + (doc_scope + " AND" if doc_scope else " WHERE")
                                 + " d.status = 'indexed'", doc_params),
        "failed_documents": one("SELECT COUNT(*) FROM documents d" + (doc_scope + " AND" if doc_scope else " WHERE")
                                + " d.status = 'failed'", doc_params),
        "chunks": one("SELECT COUNT(*) FROM chunks ch JOIN documents d ON d.id = ch.document_id" + doc_scope, doc_params),
        "conversations": one("SELECT COUNT(*) FROM conversations c WHERE 1=1" + sc, sp),
    }

    # --- secilen donem ---
    base = (" FROM messages m JOIN conversations c ON c.id = m.conversation_id"
            " WHERE m.created_at >= ?" + sc)
    params = [start_s] + sp
    questions = one("SELECT COUNT(*)" + base + " AND m.role = 'user'", params)

    by_status = {s: 0 for s in STATUSES}
    by_status["unknown"] = 0
    for status, n in conn.execute("SELECT m.status, COUNT(*)" + base + " AND m.role = 'assistant' GROUP BY m.status", params):
        by_status[status if status in STATUSES else "unknown"] += n
    answers = sum(by_status.values())
    grounded, avg_latency, avg_best = conn.execute(
        "SELECT COALESCE(SUM(m.grounded), 0), AVG(m.latency_ms), AVG(m.best_score)" + base + " AND m.role = 'assistant'",
        params).fetchone()

    period = {
        "questions": questions,
        "answers": answers,
        "by_status": by_status,
        "grounded_rate": _ratio(grounded, answers),
        "no_answer_rate": _ratio(by_status["no_context"] + by_status["no_info"], answers),
        # float(): PostgreSQL AVG sonucu Decimal doner, SQLite float; ikisi de ayni sayiya cevrilir
        "avg_latency_ms": None if avg_latency is None else round(float(avg_latency), 1),
        "avg_best_score": None if avg_best is None else round(float(avg_best), 3),
    }

    # --- en cok kullanilan kaynaklar: kac YANITTA kaynak olarak gosterildi ---
    top_sources = [dict(r) for r in conn.execute(
        "SELECT d.id AS document_id, d.filename, COUNT(DISTINCT m.id) AS answers"
        " FROM message_sources ms JOIN messages m ON m.id = ms.message_id"
        " JOIN conversations c ON c.id = m.conversation_id"
        " JOIN chunks ch ON ch.id = ms.chunk_id JOIN documents d ON d.id = ch.document_id"
        " WHERE m.created_at >= ?" + sc + " GROUP BY d.id ORDER BY answers DESC, d.filename LIMIT 10", params)]

    # --- gunluk soru sayisi: bos gunler 0 olarak DOLDURULUR (bosluk, 'veri yok' gibi yanilticidir) ---
    counts = {day: n for day, n in conn.execute(
        "SELECT substr(m.created_at, 1, 10) AS day, COUNT(*)" + base + " AND m.role = 'user'"
        " GROUP BY substr(m.created_at, 1, 10)", params)}      # substr: SQLite ve PostgreSQL'de ayni calisir
    daily = []
    for i in range(days):
        d = (start + timedelta(days=i)).isoformat()
        daily.append({"date": d, "questions": counts.get(d, 0)})

    return {"scope": "all" if user_id is None else "me", "days": days, "from": start_s, "to": today.isoformat(),
            "totals": totals, "period": period, "top_sources": top_sources, "daily": daily}


def _safe(cell):
    """CSV/Excel formul enjeksiyonu onlemi: =, +, -, @ ile baslayan metinlerin basina ' konur."""
    s = "" if cell is None else str(cell)
    return "'" + s if s[:1] in ("=", "+", "-", "@", "\t", "\r") else s


def report_to_csv(report: dict) -> str:
    """Raporu 'bolum,anahtar,deger' bicimli CSV'ye cevirir (Excel'de Turkce karakterler icin BOM'lu)."""
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["bölüm", "anahtar", "değer"])
    w.writerow(["rapor", "kapsam", report["scope"]])
    w.writerow(["rapor", "başlangıç", report["from"]])
    w.writerow(["rapor", "bitiş", report["to"]])
    for k, v in report["totals"].items():
        w.writerow(["toplam", k, _safe(v)])
    for k, v in report["period"].items():
        if k == "by_status":
            for s, n in v.items():
                w.writerow(["durum", s, n])
        else:
            w.writerow(["dönem", k, _safe(v)])
    for s in report["top_sources"]:
        w.writerow(["kaynak", _safe(s["filename"]), s["answers"]])
    for d in report["daily"]:
        w.writerow(["günlük", d["date"], d["questions"]])
    return "\ufeff" + out.getvalue()
