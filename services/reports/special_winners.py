# services/reports/special_winners.py
"""Special Winners PDF — all special awards with winner and prize details."""
from reportlab.lib.units import mm
from models.special import SpecialList, SpecialWinner
from models.show_entry import CalculatedEntry
from services.reports.base import (
    new_canvas, draw_page_header, draw_footer,
    MARGIN, PAGE_W, ROW_H,
)

COL_NR    = MARGIN
COL_DESC  = MARGIN + 20 * mm
COL_WIN   = MARGIN + 100 * mm
COL_PRIZE = MARGIN + 130 * mm


def generate_special_winners(sd=None) -> bytes:
    specials = list(SpecialList.select().order_by(
        SpecialList.kind_sequence, SpecialList.special_nr
    ))
    winner_map = {
        w.special_nr: w for w in SpecialWinner.select()
    }
    entry_map = {
        e.auto_num: e for e in CalculatedEntry.select()
    }

    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "Special Winners", sd)
    _draw_col_headers(c, y)
    y -= ROW_H

    last_kind = None
    for sp in specials:
        if y < MARGIN + ROW_H * 2:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            y = draw_page_header(c, "Special Winners", sd)
            _draw_col_headers(c, y)
            y -= ROW_H
            last_kind = None

        if sp.kind and sp.kind != last_kind:
            c.setFont("Helvetica-Bold", 9)
            c.drawString(MARGIN, y, sp.kind.upper())
            y -= ROW_H
            last_kind = sp.kind

        winner = winner_map.get(sp.special_nr)
        exhibit_no = winner.exhibit_no if winner else None

        c.setFont("Helvetica", 9)
        c.drawString(COL_NR, y, sp.special_nr or "")
        c.drawString(COL_DESC, y, (sp.description or "")[:38])
        c.drawString(COL_WIN, y, str(exhibit_no or ""))
        c.drawString(COL_PRIZE, y, (sp.prize1 or "")[:25])
        y -= ROW_H

    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()


def _draw_col_headers(c, y: float) -> None:
    c.setFont("Helvetica-Bold", 9)
    for x, hdr in zip(
        [COL_NR, COL_DESC, COL_WIN, COL_PRIZE],
        ["Special #", "Description", "Exhibit #", "Prize"],
    ):
        c.drawString(x, y, hdr)
    c.setLineWidth(0.3)
    c.line(MARGIN, y - 2, PAGE_W - MARGIN, y - 2)
