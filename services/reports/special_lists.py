"""Special Lists catalogue report (Access menu 4.2)."""

from reportlab.lib.units import mm

from models.special import SpecialList
from services.reports.base import MARGIN, PAGE_W, ROW_H, draw_footer, draw_page_header, new_canvas


def generate_special_lists(sd=None) -> bytes:
    rows = (
        SpecialList.select()
        .order_by(
            SpecialList.kind_sequence,
            SpecialList.kind,
            SpecialList.bird_type,
            SpecialList.special_nr,
        )
    )

    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "4.2 Special Lists", sd)

    if not rows.exists():
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN, y, "No special prize list records found.")
        draw_footer(c, page_num)
        c.save()
        return buf.getvalue()

    last_group = None
    for row in rows:
        if y < MARGIN + ROW_H * 4:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            y = draw_page_header(c, "4.2 Special Lists", sd)
            last_group = None

        group = row.kind or row.bird_type or "Special Lists"
        if group != last_group:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(MARGIN, y, group)
            y -= ROW_H
            last_group = group

        c.setFont("Helvetica-Bold", 8)
        c.drawString(MARGIN + 3 * mm, y, row.special_nr or "")
        c.setFont("Helvetica", 8)
        c.drawString(MARGIN + 20 * mm, y, (row.bird_type or "")[:28])
        c.drawString(MARGIN + 60 * mm, y, (row.description or "")[:55])
        prize = row.prize1 or ""
        if row.cash:
            prize = f"{prize} R{row.cash}".strip()
        c.drawRightString(PAGE_W - MARGIN, y, prize[:35])
        y -= ROW_H

    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()
