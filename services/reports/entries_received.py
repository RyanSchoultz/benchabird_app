# services/reports/entries_received.py
"""Entries Received report — all calculated entries in ticket order."""
from reportlab.lib.units import mm
from models.show_entry import CalculatedEntry
from services.reports.base import (
    new_canvas, draw_page_header, draw_footer,
    MARGIN, PAGE_W, ROW_H,
)

COL_X = [MARGIN, MARGIN + 18*mm, MARGIN + 60*mm, MARGIN + 120*mm]
HEADERS = ["Ticket #", "Exh #", "Name", "Class"]


def generate_entries_received(sd=None) -> bytes:
    entries = list(CalculatedEntry.select().order_by(CalculatedEntry.auto_num))
    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "Entries Received", sd)
    y = _draw_col_headers(c, y)

    for entry in entries:
        if y < MARGIN + ROW_H:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            y = draw_page_header(c, "Entries Received", sd)
            y = _draw_col_headers(c, y)

        c.setFont("Helvetica", 9)
        vals = [
            str(entry.auto_num),
            str(entry.exh_no or ""),
            entry.name or "",
            entry.class_code or "",
        ]
        for x, val in zip(COL_X, vals):
            c.drawString(x, y, val[:40])
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
