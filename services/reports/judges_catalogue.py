from reportlab.lib.units import mm

from services.judging_catalogue_service import get_judging_entries
from services.reports.base import (
    MARGIN,
    PAGE_W,
    ROW_H,
    draw_footer,
    draw_page_header,
    new_canvas,
)

BOX_LABELS = ["1", "2", "3", "4", "5", "BOB", "R/U BOB", "Champ", "Res", "NB"]


def _draw_boxes(c, y):
    x = MARGIN + 28 * mm
    for label in BOX_LABELS:
        width = 10 * mm if len(label) <= 2 else 16 * mm
        c.rect(x, y - 3, width, 10, stroke=1, fill=0)
        c.setFont("Helvetica", 6)
        c.drawCentredString(x + width / 2, y, label)
        x += width + 2 * mm


def generate_judges_catalogue(sd=None) -> bytes:
    rows = get_judging_entries()
    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "Judges Catalogue", sd)

    if not rows:
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN, y, "Bench birds in Show Participants before printing judging sheets.")
        draw_footer(c, page_num)
        c.save()
        return buf.getvalue()

    last_category = None
    last_main = None
    last_class = None

    for row in rows:
        if row.category != last_category:
            if last_category is not None:
                draw_footer(c, page_num)
                c.showPage()
                page_num += 1
                y = draw_page_header(c, "Judges Catalogue", sd)
            c.setFont("Helvetica-Bold", 13)
            c.drawString(MARGIN, y, row.category)
            y -= ROW_H + 3
            last_category = row.category
            last_main = None
            last_class = None

        if y < MARGIN + ROW_H * 5:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            y = draw_page_header(c, "Judges Catalogue", sd)
            last_main = None
            last_class = None

        if row.main_class != last_main:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(MARGIN, y, row.main_class)
            y -= ROW_H
            last_main = row.main_class
            last_class = None

        if row.class_code != last_class:
            c.setFont("Helvetica-Bold", 9)
            class_label = f"{row.class_code or ''}  {row.colour}".strip()
            c.drawString(MARGIN, y, class_label)
            if row.type_b:
                c.setFont("Helvetica", 8)
                c.drawRightString(PAGE_W - MARGIN, y, row.type_b)
            y -= ROW_H
            last_class = row.class_code

        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN + 4 * mm, y, str(row.auto_num))
        _draw_boxes(c, y)
        y -= ROW_H + 1

    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()
