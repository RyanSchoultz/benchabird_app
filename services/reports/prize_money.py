# services/reports/prize_money.py
"""Prize Money PDF — cash prizes with winner details and total."""
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
COL_NAME  = MARGIN + 120 * mm
COL_CASH  = PAGE_W - MARGIN


def generate_prize_money(sd=None) -> bytes:
    cash_specials = list(
        SpecialList.select()
        .where(SpecialList.cash > 0)
        .order_by(SpecialList.kind_sequence, SpecialList.special_nr)
    )
    winner_map = {w.special_nr: w for w in SpecialWinner.select()}
    entry_map = {e.auto_num: e for e in CalculatedEntry.select()}

    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "Prize Money", sd)
    _draw_col_headers(c, y)
    y -= ROW_H

    total_cash = 0
    for sp in cash_specials:
        if y < MARGIN + ROW_H * 3:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            y = draw_page_header(c, "Prize Money", sd)
            _draw_col_headers(c, y)
            y -= ROW_H

        winner = winner_map.get(sp.special_nr)
        exhibit_no = winner.exhibit_no if winner else None
        entry = entry_map.get(exhibit_no) if exhibit_no else None
        winner_name = entry.name if entry else ""

        c.setFont("Helvetica", 9)
        c.drawString(COL_NR, y, sp.special_nr or "")
        c.drawString(COL_DESC, y, (sp.description or "")[:40])
        c.drawString(COL_WIN, y, str(exhibit_no or ""))
        c.drawString(COL_NAME, y, winner_name[:20])
        c.drawRightString(COL_CASH, y, f"R {sp.cash:,}")
        y -= ROW_H
        total_cash += sp.cash or 0

    if y < MARGIN + ROW_H * 3:
        draw_footer(c, page_num)
        c.showPage()
        page_num += 1
        y = draw_page_header(c, "Prize Money", sd)
        _draw_col_headers(c, y)
        y -= ROW_H
    y -= 4
    c.setLineWidth(0.5)
    c.line(MARGIN, y, PAGE_W - MARGIN, y)
    y -= ROW_H
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN, y, "Total:")
    c.drawRightString(COL_CASH, y, f"R {total_cash:,}")

    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()


def _draw_col_headers(c, y: float) -> None:
    c.setFont("Helvetica-Bold", 9)
    for x, hdr in zip(
        [COL_NR, COL_DESC, COL_WIN, COL_NAME, COL_CASH],
        ["Special #", "Description", "Ticket #", "Winner", "Cash"],
    ):
        if x == COL_CASH:
            c.drawRightString(x, y, hdr)
        else:
            c.drawString(x, y, hdr)
    c.setLineWidth(0.3)
    c.line(MARGIN, y - 2, PAGE_W - MARGIN, y - 2)
