# services/reports/address_tags.py
"""Address Tags PDF — 3-column mailing labels for all exhibitors."""
from reportlab.lib.units import mm
from models.exhibitor import Exhibitor
from services.reports.base import new_canvas, draw_page_header, draw_footer, MARGIN, PAGE_W, PAGE_H

COLS = 3
ROWS = 9
TAG_W = (PAGE_W - 2 * MARGIN) / COLS
TAG_H = (PAGE_H - 2 * MARGIN - 20 * mm) / ROWS
TAGS_PER_PAGE = COLS * ROWS


def generate_address_tags(sd=None) -> bytes:
    exhibitors = list(Exhibitor.select().order_by(Exhibitor.exh_no))
    buf, c = new_canvas()
    page_num = 1

    for i, exh in enumerate(exhibitors):
        page_pos = i % TAGS_PER_PAGE
        if page_pos == 0 and i > 0:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1

        row, col = divmod(page_pos, COLS)
        x = MARGIN + col * TAG_W
        y = PAGE_H - MARGIN - 20 * mm - row * TAG_H

        c.setLineWidth(0.3)
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.rect(x + 2, y - TAG_H + 4, TAG_W - 4, TAG_H - 4)
        c.setStrokeColorRGB(0, 0, 0)

        text_x = x + 6
        text_y = y - 12

        c.setFont("Helvetica-Bold", 9)
        c.drawString(text_x, text_y, exh.name or "")
        text_y -= 11

        c.setFont("Helvetica", 8)
        if exh.address:
            c.drawString(text_x, text_y, exh.address[:40])
            text_y -= 10
        suburb_town = " ".join(p for p in [exh.suburb, exh.town] if p)
        if suburb_town:
            c.drawString(text_x, text_y, suburb_town[:40])
            text_y -= 10
        if exh.zip_code:
            c.drawString(text_x, text_y, exh.zip_code)

    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()
