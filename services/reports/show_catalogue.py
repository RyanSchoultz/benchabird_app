# services/reports/show_catalogue.py
"""Show Catalogue — entries grouped by class, sorted by class_seq then exh_no."""
from reportlab.lib.units import mm
from models.show_entry import CalculatedEntry
from services.reports.base import (
    new_canvas, draw_page_header, draw_footer,
    MARGIN, PAGE_W, ROW_H,
)

COL_TICKET = MARGIN + 5 * mm
COL_EXH    = MARGIN + 22 * mm
COL_NAME   = MARGIN + 48 * mm


def generate_show_catalogue(sd=None) -> bytes:
    sql = """
        SELECT ce.auto_num, ce.exh_no, ce.name, ce.class_code,
               COALESCE(cd.bird_type, ''), CAST(COALESCE(cd.class_seq, 0) AS REAL)
        FROM calculated_entry ce
        LEFT JOIN class_def cd ON ce.class_code = cd.class_code
        ORDER BY CAST(COALESCE(cd.class_seq, 0) AS REAL), ce.exh_no
    """
    db = CalculatedEntry._meta.database
    rows = db.execute_sql(sql).fetchall()

    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "Show Catalogue", sd)
    last_class = None

    for auto_num, exh_no, name, class_code, bird_type, _ in rows:
        if y < MARGIN + ROW_H * 3:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            y = draw_page_header(c, "Show Catalogue", sd)
            last_class = None

        if class_code != last_class:
            y -= 3
            c.setFont("Helvetica-Bold", 10)
            label = f"{class_code}  {bird_type}" if bird_type else class_code or ""
            c.drawString(MARGIN, y, label)
            c.setLineWidth(0.4)
            c.line(MARGIN, y - 1, PAGE_W - MARGIN, y - 1)
            y -= ROW_H + 2
            last_class = class_code

        c.setFont("Helvetica", 9)
        c.drawString(COL_TICKET, y, str(auto_num))
        c.drawString(COL_EXH, y, str(exh_no or ""))
        c.drawString(COL_NAME, y, (name or "")[:45])
        c.drawRightString(PAGE_W - MARGIN, y, class_code or "")
        y -= ROW_H

    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()
