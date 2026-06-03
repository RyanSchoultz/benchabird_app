"""Results by Exhibitor report grouped per exhibitor with specials and prize money."""
from collections import defaultdict

from reportlab.lib.units import mm

from models.show_entry import CalculatedEntry
from services.reports.base import (
    MARGIN,
    PAGE_W,
    ROW_H,
    draw_footer,
    draw_page_header,
    new_canvas,
)

_COL_TICKET = MARGIN
_COL_CLASS = MARGIN + 22 * mm
_COL_RESULT = MARGIN + 50 * mm
_SECTION_OVERHEAD_ROWS = 3


def _draw_empty_pdf(message: str, sd=None) -> bytes:
    buf, c = new_canvas()
    y = draw_page_header(c, "Results by Exhibitor", sd)
    c.setFont("Helvetica", 10)
    c.drawString(MARGIN, y - ROW_H * 2, message)
    draw_footer(c, 1)
    c.save()
    return buf.getvalue()


def _draw_col_headers(c, y: float, cont_label: str = "") -> float:
    if cont_label:
        c.setFont("Helvetica-Bold", 9)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(MARGIN, y, cont_label + " (cont.)")
        c.setFillColorRGB(0, 0, 0)
        y -= ROW_H

    c.setLineWidth(0.3)
    c.line(MARGIN, y + 2, PAGE_W - MARGIN, y + 2)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(_COL_TICKET, y, "Ticket #")
    c.drawString(_COL_CLASS, y, "Class")
    c.drawString(_COL_RESULT, y, "Result")
    return y - ROW_H


def generate_results_by_exhibitor(sd=None) -> bytes:
    db = CalculatedEntry._meta.database

    if CalculatedEntry.select().count() == 0:
        return _draw_empty_pdf(
            "No benched birds found. Use Show Participants before generating this report.",
            sd,
        )

    sql = """
        SELECT ce.exh_no, COALESCE(e.name, ''),
               ce.auto_num,
               COALESCE(ce.class_code, ''),
               COALESCE(r.result, ''),
               CASE WHEN nb.exhibit_no IS NOT NULL THEN 1 ELSE 0 END
        FROM calculated_entry ce
        LEFT JOIN exhibitor e ON ce.exh_no = e.exh_no
        LEFT JOIN result r ON ce.auto_num = r.exhibit_no
        LEFT JOIN not_benched nb ON ce.auto_num = nb.exhibit_no
        WHERE r.exhibit_no IS NOT NULL OR nb.exhibit_no IS NOT NULL
        ORDER BY ce.exh_no, ce.auto_num
    """
    rows = db.execute_sql(sql).fetchall()

    if not rows:
        return _draw_empty_pdf("No results recorded yet.", sd)

    exhibitor_rows = defaultdict(list)
    exhibitor_names = {}
    for exh_no, name, ticket_no, class_code, result, is_nb in rows:
        exhibitor_rows[exh_no].append((ticket_no, class_code, result, bool(is_nb)))
        exhibitor_names[exh_no] = name

    specials_sql = """
        SELECT sw.special_nr, COALESCE(sl.description, ''), COALESCE(sl.cash, 0)
        FROM special_winner sw
        JOIN special_list sl ON sw.special_nr = sl.special_nr
        WHERE sw.exhibit_no IN (
            SELECT auto_num FROM calculated_entry WHERE exh_no = ?
        )
        ORDER BY sw.special_nr
    """

    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "Results by Exhibitor", sd)
    first_section = True

    for exh_no in sorted(exhibitor_rows):
        entries = exhibitor_rows[exh_no]
        name = exhibitor_names[exh_no]
        specials = db.execute_sql(specials_sql, (exh_no,)).fetchall()
        prize_total = sum(cash for _, _, cash in specials)
        label = f"Exhibitor #{exh_no}  -  {name}"

        rows_needed = (
            _SECTION_OVERHEAD_ROWS
            + len(entries)
            + (len(specials) + 1 if specials else 0)
            + (1 if prize_total > 0 else 0)
        )

        if not first_section:
            if y - rows_needed * ROW_H < MARGIN:
                draw_footer(c, page_num)
                c.showPage()
                page_num += 1
                y = draw_page_header(c, "Results by Exhibitor", sd)
            else:
                y -= 4
                c.setLineWidth(1.0)
                c.line(MARGIN, y, PAGE_W - MARGIN, y)
                y -= 6
        first_section = False

        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN, y, label)
        y -= ROW_H
        y = _draw_col_headers(c, y)

        for ticket_no, class_code, result, is_nb in entries:
            if y < MARGIN + ROW_H:
                draw_footer(c, page_num)
                c.showPage()
                page_num += 1
                y = draw_page_header(c, "Results by Exhibitor", sd)
                y = _draw_col_headers(c, y, label)

            c.setFont("Helvetica", 9)
            c.drawString(_COL_TICKET, y, str(ticket_no))
            c.drawString(_COL_CLASS, y, class_code)
            if is_nb:
                c.setFillColorRGB(0.8, 0.1, 0.1)
                c.drawString(_COL_RESULT, y, "Not Benched")
                c.setFillColorRGB(0, 0, 0)
            else:
                c.drawString(_COL_RESULT, y, result)
            y -= ROW_H

        if specials:
            if y < MARGIN + ROW_H * 2:
                draw_footer(c, page_num)
                c.showPage()
                page_num += 1
                y = draw_page_header(c, "Results by Exhibitor", sd)
                y = _draw_col_headers(c, y, label)

            y -= 2
            c.setFont("Helvetica-Bold", 8)
            c.drawString(MARGIN, y, "Special prizes:")
            y -= ROW_H
            for _, desc, _ in specials:
                if y < MARGIN + ROW_H:
                    draw_footer(c, page_num)
                    c.showPage()
                    page_num += 1
                    y = draw_page_header(c, "Results by Exhibitor", sd)
                    y = _draw_col_headers(c, y, label)
                c.setFont("Helvetica", 9)
                c.drawString(MARGIN + 6 * mm, y, desc[:60])
                y -= ROW_H

        if prize_total > 0:
            if y < MARGIN + ROW_H:
                draw_footer(c, page_num)
                c.showPage()
                page_num += 1
                y = draw_page_header(c, "Results by Exhibitor", sd)
                y = _draw_col_headers(c, y, label)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(MARGIN, y, f"Prize money: R {prize_total}")
            y -= ROW_H

    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()
