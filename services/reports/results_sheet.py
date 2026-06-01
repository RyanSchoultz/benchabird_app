# services/reports/results_sheet.py
"""Results Sheet — all recorded results with name and class."""
from reportlab.lib.units import mm
from models.results import Result, NotBenched
from services.reports.base import (
    new_canvas, draw_page_header, draw_footer,
    MARGIN, PAGE_W, ROW_H,
)

COL_X = [MARGIN, MARGIN + 18*mm, MARGIN + 55*mm, MARGIN + 110*mm, MARGIN + 140*mm]
HEADERS = ["Ticket #", "Exh #", "Name", "Class", "Result"]


def generate_results_sheet(sd=None) -> bytes:
    sql = """
        SELECT r.exhibit_no, COALESCE(ce.exh_no, ''), COALESCE(ce.name, ''),
               COALESCE(ce.class_code, ''), COALESCE(r.result, ''),
               CASE WHEN nb.exhibit_no IS NOT NULL THEN 'NB' ELSE '' END
        FROM result r
        LEFT JOIN calculated_entry ce ON r.exhibit_no = ce.auto_num
        LEFT JOIN not_benched nb ON r.exhibit_no = nb.exhibit_no
        ORDER BY r.exhibit_no
    """
    db = Result._meta.database
    rows = db.execute_sql(sql).fetchall()

    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "Results Sheet", sd)
    y = _draw_col_headers(c, y)

    for exhibit_no, exh_no, name, class_code, result, nb_flag in rows:
        if y < MARGIN + ROW_H:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            y = draw_page_header(c, "Results Sheet", sd)
            y = _draw_col_headers(c, y)

        c.setFont("Helvetica", 9)
        vals = [str(exhibit_no), str(exh_no), name[:35], class_code, result]
        for x, val in zip(COL_X, vals):
            c.drawString(x, y, val)

        if nb_flag:
            c.setFillColorRGB(0.8, 0.1, 0.1)
            c.drawRightString(PAGE_W - MARGIN, y, "NB")
            c.setFillColorRGB(0, 0, 0)
        y -= ROW_H

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
