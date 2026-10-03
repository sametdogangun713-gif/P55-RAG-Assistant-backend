"""Kullanim raporunu PDF'e cevirir (reportlab). Arayuzdeki "PDF indir" dugmesi bunu kullanir.

Neden PDF: CSV, Excel'in bolgesel ayarina gore (ayrac, karakter kodlamasi) farkli aciliyordu; PDF her yerde ayni
gorunur. Yazi tipi: reportlab'in icinde gelen Bitstream Vera (Turkce harfleri - ş ğ ı İ - icerir; ayri dosya
indirmek gerekmez). Standart PDF yazi tipi Helvetica bu harfleri basamaz.
Sunucudan gelen metinler (dosya adi gibi) Paragraph icinde HTML-escape edilir: "<b>" gibi bir dosya adi bicim
komutu olarak yorumlanmaz.
"""
import io
import os
from datetime import datetime, timezone
from xml.sax.saxutils import escape

FONT, FONT_BOLD = "P55Sans", "P55Sans-Bold"

STATUS_LABELS = {
    "answered": "Kaynaklı yanıt", "no_context": "İlgili bölüm bulunamadı", "no_info": "Yeterli bilgi yok",
    "unverified": "Doğrulanamadı", "general": "Genel yanıt (belge dışı)", "unknown": "Bilinmiyor",
}


def _register_fonts():
    import reportlab
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    if FONT in pdfmetrics.getRegisteredFontNames():
        return
    d = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
    pdfmetrics.registerFont(TTFont(FONT, os.path.join(d, "Vera.ttf")))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, os.path.join(d, "VeraBd.ttf")))


def _num(v) -> str:
    """Turkce sayi bicimi: 1.234 / 0,5 ; None -> '—'."""
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.3f}".rstrip("0").rstrip(".").replace(".", ",")
    return f"{v:,}".replace(",", ".")


def _pct(v) -> str:
    return "—" if v is None else "%" + f"{v * 100:.1f}".replace(".", ",")


def _date_tr(iso: str) -> str:
    """'2026-10-03' -> '03.10.2026'"""
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d.%m.%Y")
    except (TypeError, ValueError):
        return str(iso)


def report_to_pdf(report: dict, owner: str = "", now=None) -> bytes:
    """report: reports.usage_report() ciktisi. owner: raporu isteyen (ust bilgide gosterilir). PDF baytlari doner."""
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.shapes import Drawing
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    _register_fonts()
    now = now or datetime.now(timezone.utc)
    black, grey, light = colors.HexColor("#0a0a0a"), colors.HexColor("#555555"), colors.HexColor("#e5e5e5")

    h1 = ParagraphStyle("h1", fontName=FONT_BOLD, fontSize=20, leading=24, textColor=black, spaceAfter=2)
    h2 = ParagraphStyle("h2", fontName=FONT_BOLD, fontSize=12, leading=16, textColor=black, spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("body", fontName=FONT, fontSize=9.5, leading=13, textColor=black)
    small = ParagraphStyle("small", fontName=FONT, fontSize=8, leading=11, textColor=grey)
    cell = ParagraphStyle("cell", fontName=FONT, fontSize=9, leading=12, textColor=black)

    th = ParagraphStyle("th", parent=cell, fontName=FONT_BOLD, textColor=colors.white)

    def table(rows, widths, header=True):
        # Baslik satiri beyaz yazi stiliyle BASTAN olusturulur (Paragraph olustuktan sonra stil degistirmek ise yaramaz)
        data = [[Paragraph(escape(str(c)), th if header and i == 0 else cell) for c in r] for i, r in enumerate(rows)]
        t = Table(data, colWidths=widths, hAlign="LEFT")
        style = [
            ("BOX", (0, 0), (-1, -1), 0.8, black),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, light),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
        if header:
            style += [("BACKGROUND", (0, 0), (-1, 0), black)]
        t.setStyle(TableStyle(style))
        return t

    p, t = report["period"], report["totals"]
    story = [
        Paragraph("P55 · Kullanım ve Kaynak Raporu", h1),
        Paragraph(escape(
            f"Kapsam: {'Tüm sistem' if report['scope'] == 'all' else 'Benim kullanımım'}"
            f"  ·  Dönem: {_date_tr(report['from'])} – {_date_tr(report['to'])} ({report['days']} gün)"
            + (f"  ·  İsteyen: {owner}" if owner else "")), small),
        Paragraph(escape(f"Oluşturulma: {now.strftime('%d.%m.%Y %H:%M')} (UTC)"), small),
        Spacer(1, 6),
    ]

    summary = [["Ölçüt", "Değer"],
               ["Soru (dönem)", _num(p["questions"])],
               ["Kaynağa dayalı yanıt oranı", _pct(p["grounded_rate"])],
               ["Yanıtsız kalan oranı", _pct(p["no_answer_rate"])],
               ["Ortalama yanıt süresi", "—" if p["avg_latency_ms"] is None else _num(round(p["avg_latency_ms"])) + " ms"],
               ["Ortalama en iyi benzerlik", _num(p["avg_best_score"])],
               ["Belge (hazır / toplam)", f"{_num(t['indexed_documents'])} / {_num(t['documents'])}"],
               ["Hatalı belge", _num(t["failed_documents"])],
               ["Parça", _num(t["chunks"])],
               ["Sohbet", _num(t["conversations"])]]
    if t.get("users") is not None:
        summary.append(["Kullanıcı", _num(t["users"])])
    story += [Paragraph("Özet", h2), table(summary, [95 * mm, 60 * mm])]

    status_rows = [["Yanıt durumu", "Sayı"]]
    for k, v in p["by_status"].items():
        if k == "unknown" and not v:
            continue
        status_rows.append([STATUS_LABELS.get(k, k), _num(v)])
    story += [Paragraph("Yanıt kalitesi", h2), table(status_rows, [95 * mm, 60 * mm])]
    if p["answers"] == 0:
        story.append(Paragraph("Bu dönemde yanıt yok; oranlar hesaplanamadı (—).", small))

    story.append(Paragraph("En çok kaynak gösterilen belgeler", h2))
    if report["top_sources"]:
        rows = [["Belge", "Yanıt sayısı"]] + [[s["filename"], _num(s["answers"])] for s in report["top_sources"]]
        story.append(table(rows, [95 * mm, 60 * mm]))
    else:
        story.append(Paragraph("Bu dönemde kaynak gösterilen belge yok.", body))

    daily = report["daily"]
    total_q = sum(d["questions"] for d in daily)
    chart_block = [Paragraph(f"Günlük soru sayısı (toplam {_num(total_q)})", h2)]
    if daily:
        dw, dh = 170 * mm, 42 * mm
        drawing = Drawing(dw, dh)
        chart = VerticalBarChart()
        chart.x, chart.y, chart.width, chart.height = 22, 18, dw - 30, dh - 26
        chart.data = [[d["questions"] for d in daily]]
        chart.bars[0].fillColor = black
        chart.bars[0].strokeColor = None
        chart.valueAxis.valueMin = 0
        top = max([d["questions"] for d in daily] + [1])
        chart.valueAxis.valueMax = top
        chart.valueAxis.valueStep = max(1, -(-top // 4))
        chart.valueAxis.labels.fontName, chart.valueAxis.labels.fontSize = FONT, 7
        step = max(1, len(daily) // 8)                      # x ekseninde en fazla ~8 tarih yazilir
        chart.categoryAxis.categoryNames = [_date_tr(d["date"])[:5] if i % step == 0 else "" for i, d in enumerate(daily)]
        chart.categoryAxis.labels.fontName, chart.categoryAxis.labels.fontSize = FONT, 7
        chart.categoryAxis.strokeColor = chart.valueAxis.strokeColor = black
        drawing.add(chart)
        chart_block.append(drawing)
    story.append(KeepTogether(chart_block))        # baslik ile grafik ayni sayfada kalsin

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(FONT, 7.5)
        canvas.setFillColor(grey)
        canvas.drawString(18 * mm, 10 * mm, "P55 — Belge Tabanlı Soru-Cevap Asistanı")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Sayfa {doc.page}")
        canvas.restoreState()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=18 * mm, title="P55 Kullanım Raporu", author="P55")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
