# services/reports/entry_confirmation.py
"""Exhibitor Entry Confirmation Sheet — one section per exhibitor listing their entries."""
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, CalculatedEntry, LateEntry
from models.class_def import ClassDef
from services.reports.base import (
    new_canvas, draw_page_header, draw_footer,
    MARGIN, PAGE_W, ROW_H,
)

_LATE_COLOR = HexColor('#b45309')  # amber

_COL_TICKET = MARGIN
_COL_CLASS  = MARGIN + 22 * mm
_COL_DESC   = MARGIN + 44 * mm
_SECTION_OVERHEAD_ROWS = 4  # header + contact + col-headers + count-footer


def _draw_col_headers(c, y: float, cont_label: str = "") -> float:
    """Draw column header rule and labels. Optionally draw a continuation label first."""
    if cont_label:
        c.setFont("Helvetica-Bold", 9)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(MARGIN, y, cont_label + " (cont.)")
        c.setFillColorRGB(0, 0, 0)
        y -= ROW_H
    c.setLineWidth(0.3)
    c.line(MARGIN, y, PAGE_W - MARGIN, y)
    y -= ROW_H * 0.6
    c.setFont("Helvetica-Bold", 8)
    c.drawString(_COL_TICKET, y, "Ticket #")
    c.drawString(_COL_CLASS, y, "Class")
    c.drawString(_COL_DESC, y, "Description")
    return y - ROW_H


def generate_entry_confirmation(sd=None, include_late: bool = True) -> bytes:
    use_calculated = CalculatedEntry.select().count() > 0

    class_desc = {
        cd.class_code: f"{cd.main_class or ''} {cd.colour or ''}".strip()
        for cd in ClassDef.select()
    }

    exhibitors = list(Exhibitor.select().order_by(Exhibitor.exh_no))

    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "Entry Confirmation", sd)
    first_section = True
    total_regular = 0
    total_late = 0
    exh_count = 0

    for exh in exhibitors:
        if use_calculated:
            regular = list(
                CalculatedEntry.select()
                .where(CalculatedEntry.exh_no == exh.exh_no)
                .order_by(CalculatedEntry.auto_num)
            )
        else:
            regular = list(
                ShowEntry.select()
                .where(ShowEntry.exh_no == exh.exh_no)
                .order_by(ShowEntry.auto_num)
            )

        late = (
            list(
                LateEntry.select()
                .where(LateEntry.exh_no == exh.exh_no)
                .order_by(LateEntry.auto_num)
            )
            if include_late else []
        )

        if not regular and not late:
            continue

        exh_count += 1
        rows_needed = _SECTION_OVERHEAD_ROWS + len(regular) + len(late)
        if not first_section:
            if y - rows_needed * ROW_H < MARGIN:
                draw_footer(c, page_num)
                c.showPage()
                page_num += 1
                y = draw_page_header(c, "Entry Confirmation", sd)
            else:
                y -= 4
                c.setLineWidth(1.0)
                c.line(MARGIN, y, PAGE_W - MARGIN, y)
                y -= 6

        first_section = False

        # Exhibitor header
        exh_label = f"Exhibitor #{exh.exh_no}  —  {exh.name or ''}"
        c.setFont("Helvetica-Bold", 10)
        header = exh_label
        if exh.club:
            header += f"  [{exh.club}]"
        c.drawString(MARGIN, y, header)
        y -= ROW_H

        # Contact sub-line
        contact = "  |  ".join(p for p in [exh.cell_no, exh.tel_home] if p)
        if contact:
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(MARGIN, y, contact)
            c.setFillColorRGB(0, 0, 0)
            y -= ROW_H * 0.8

        # Column headers
        y = _draw_col_headers(c, y)

        # Regular entry rows
        for entry in regular:
            if y < MARGIN + ROW_H:
                draw_footer(c, page_num)
                c.showPage()
                page_num += 1
                y = draw_page_header(c, "Entry Confirmation", sd)
                y = _draw_col_headers(c, y, exh_label)

            c.setFont("Helvetica", 9)
            ticket = str(entry.auto_num) if use_calculated else "—"
            code = entry.class_code or ""
            desc = class_desc.get(code, "")[:48]
            c.drawString(_COL_TICKET, y, ticket)
            c.drawString(_COL_CLASS, y, code)
            c.drawString(_COL_DESC, y, desc)
            y -= ROW_H
            total_regular += 1

        # Late entry rows
        for entry in late:
            if y < MARGIN + ROW_H:
                draw_footer(c, page_num)
                c.showPage()
                page_num += 1
                y = draw_page_header(c, "Entry Confirmation", sd)
                y = _draw_col_headers(c, y, exh_label)

            c.setFont("Helvetica", 9)
            code = entry.class_code or ""
            desc = class_desc.get(code, "")[:48]
            c.drawString(_COL_TICKET, y, "—")
            c.drawString(_COL_CLASS, y, code)
            c.drawString(_COL_DESC, y, desc)
            c.setFillColor(_LATE_COLOR)
            c.drawRightString(PAGE_W - MARGIN, y, "LATE")
            c.setFillColorRGB(0, 0, 0)
            y -= ROW_H
            total_late += 1

        # Entry count footer
        y -= 2
        c.setLineWidth(0.3)
        c.line(MARGIN, y, PAGE_W - MARGIN, y)
        y -= ROW_H * 0.7
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        parts = [f"{len(regular)} {'entry' if len(regular) == 1 else 'entries'}"]
        if late:
            parts.append(f"{len(late)} late {'entry' if len(late) == 1 else 'entries'}")
        c.drawString(MARGIN, y, "  +  ".join(parts))
        c.setFillColorRGB(0, 0, 0)
        y -= ROW_H * 0.5

    # Document summary
    if exh_count > 0:
        y -= ROW_H
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        summary_parts = [f"{exh_count} {'exhibitor' if exh_count == 1 else 'exhibitors'}",
                         f"{total_regular} {'entry' if total_regular == 1 else 'entries'}"]
        if total_late:
            summary_parts.append(f"{total_late} late")
        c.drawRightString(PAGE_W - MARGIN, y, "  •  ".join(summary_parts))
        c.setFillColorRGB(0, 0, 0)
        y -= ROW_H * 0.7

    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()
