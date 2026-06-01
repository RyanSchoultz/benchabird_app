# services/reports/exhibitor_list.py
"""Exhibitor List PDF — all exhibitors with entry counts."""
from reportlab.lib.units import mm
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, LateEntry
from services.reports.base import (
    new_canvas, draw_page_header, draw_footer,
    MARGIN, PAGE_W, ROW_H,
)

COL_X = [MARGIN, MARGIN + 18*mm, MARGIN + 80*mm, MARGIN + 130*mm, MARGIN + 148*mm]
HEADERS = ["Exh #", "Name", "Town", "Entries", "Late"]


def generate_exhibitor_list(sd=None) -> bytes:
    sql = """
        SELECT e.exh_no, e.name, e.town,
               COUNT(DISTINCT se.auto_num) AS entries,
               COUNT(DISTINCT le.auto_num) AS late
        FROM exhibitor e
        LEFT JOIN show_entry se ON e.exh_no = se.exh_no
        LEFT JOIN late_entry le ON e.exh_no = le.exh_no
        GROUP BY e.exh_no, e.name, e.town
        ORDER BY e.exh_no
    """
    db = Exhibitor._meta.database
    rows = db.execute_sql(sql).fetchall()

    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "Exhibitor List", sd)
    y = _draw_col_headers(c, y)

    for exh_no, name, town, entries, late in rows:
        if y < MARGIN + ROW_H:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            y = draw_page_header(c, "Exhibitor List", sd)
            y = _draw_col_headers(c, y)

        c.setFont("Helvetica", 9)
        vals = [str(exh_no), (name or "")[:40], (town or "")[:25],
                str(entries), str(late) if late else ""]
        for x, val in zip(COL_X, vals):
            c.drawString(x, y, val)
        y -= ROW_H

    y -= 4
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN, y, f"Total: {len(rows)} exhibitors")

    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()


def _draw_col_headers(c, y: float) -> float:
    c.setFont("Helvetica-Bold", 9)
    for x, hdr in zip(COL_X, HEADERS):
        c.drawString(x, y, hdr)
    c.setLineWidth(0.3)
    c.line(MARGIN, y - 2, PAGE_W - MARGIN, y - 2)
    return y - ROW_H
