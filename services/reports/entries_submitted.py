"""Pre-show Entries Submitted report sourced from ShowEntry."""

from collections import defaultdict

from reportlab.lib.units import mm

from models.class_def import ClassDef
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry
from services.reports.base import MARGIN, PAGE_W, ROW_H, draw_footer, draw_page_header, new_canvas

SECTION_GAP = 4 * mm


def _load_data():
    exhibitor_map = {row.exh_no: row for row in Exhibitor.select() if row.exh_no is not None}
    class_map = {row.class_code: row for row in ClassDef.select() if row.class_code}
    entries = list(ShowEntry.select().order_by(ShowEntry.exh_no, ShowEntry.auto_num))
    entries_by_exhibitor: dict[int, list[ShowEntry]] = defaultdict(list)
    entries_by_class: dict[str, list[ShowEntry]] = defaultdict(list)
    for entry in entries:
        if entry.exh_no is not None:
            entries_by_exhibitor[entry.exh_no].append(entry)
        entries_by_class[entry.class_code or ""].append(entry)
    return entries_by_exhibitor, entries_by_class, exhibitor_map, class_map


def _class_seq(class_code: str | None, class_map: dict[str, ClassDef]) -> float:
    class_def = class_map.get(class_code or "")
    try:
        return float(class_def.class_seq) if class_def and class_def.class_seq is not None else 999999.0
    except (TypeError, ValueError):
        return 999999.0


def _new_page(canvas, page_num: int, title: str, sd):
    draw_footer(canvas, page_num)
    canvas.showPage()
    page_num += 1
    y = draw_page_header(canvas, title, sd)
    return page_num, y


def generate_entries_submitted(sd=None) -> bytes:
    entries_by_exhibitor, entries_by_class, exhibitor_map, class_map = _load_data()

    buf, canvas = new_canvas()
    page_num = 1

    y = draw_page_header(canvas, "Entries Submitted - Summary", sd)
    page_num, y = _draw_summary(canvas, page_num, y, entries_by_exhibitor, exhibitor_map, sd)

    draw_footer(canvas, page_num)
    canvas.showPage()
    page_num += 1
    y = draw_page_header(canvas, "Entries Submitted - By Class", sd)
    page_num, y = _draw_by_class(canvas, page_num, y, entries_by_class, exhibitor_map, class_map, sd)

    draw_footer(canvas, page_num)
    canvas.showPage()
    page_num += 1
    y = draw_page_header(canvas, "Entries Submitted - By Exhibitor", sd)
    page_num, y = _draw_by_exhibitor(canvas, page_num, y, entries_by_exhibitor, exhibitor_map, class_map, sd)

    draw_footer(canvas, page_num)
    canvas.save()
    return buf.getvalue()


def _draw_summary(canvas, page_num: int, y: float, entries_by_exhibitor, exhibitor_map, sd):
    title = "Entries Submitted - Summary"
    col_exh = MARGIN
    col_name = MARGIN + 16 * mm
    col_club = MARGIN + 92 * mm
    col_count = PAGE_W - MARGIN

    def draw_header(current_y: float) -> float:
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(col_exh, current_y, "Exh #")
        canvas.drawString(col_name, current_y, "Name")
        canvas.drawString(col_club, current_y, "Club")
        canvas.drawRightString(col_count, current_y, "Entries")
        canvas.setLineWidth(0.3)
        canvas.line(MARGIN, current_y - 2, PAGE_W - MARGIN, current_y - 2)
        return current_y - ROW_H

    y = draw_header(y)
    total_entries = 0

    for exh_no in sorted(entries_by_exhibitor):
        if y < MARGIN + ROW_H:
            page_num, y = _new_page(canvas, page_num, title, sd)
            y = draw_header(y)
        exhibitor = exhibitor_map.get(exh_no)
        count = len(entries_by_exhibitor[exh_no])
        total_entries += count
        canvas.setFont("Helvetica", 9)
        canvas.drawString(col_exh, y, str(exh_no))
        canvas.drawString(col_name, y, ((exhibitor.name if exhibitor else "") or "")[:42])
        canvas.drawString(col_club, y, ((exhibitor.club if exhibitor else "") or "")[:20])
        canvas.drawRightString(col_count, y, str(count))
        y -= ROW_H

    canvas.setLineWidth(0.3)
    canvas.line(MARGIN, y + ROW_H - 1, PAGE_W - MARGIN, y + ROW_H - 1)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(col_name, y, f"Total: {len(entries_by_exhibitor)} exhibitors")
    canvas.drawRightString(col_count, y, str(total_entries))
    return page_num, y - ROW_H


def _draw_by_class(canvas, page_num: int, y: float, entries_by_class, exhibitor_map, class_map, sd):
    title = "Entries Submitted - By Class"
    current_bird_type = None
    current_main_class = None
    sorted_codes = sorted(entries_by_class, key=lambda code: _class_seq(code, class_map))

    for class_code in sorted_codes:
        class_def = class_map.get(class_code)
        bird_type = ((class_def.bird_type if class_def else "") or "").upper()
        main_class = ((class_def.main_class if class_def else "") or "").upper()
        colour = (class_def.colour if class_def else "") or ""

        if bird_type != current_bird_type:
            if y < MARGIN + ROW_H * 4:
                page_num, y = _new_page(canvas, page_num, title, sd)
            current_bird_type = bird_type
            current_main_class = None
            y -= 2
            canvas.setFont("Helvetica-Bold", 10)
            canvas.drawString(MARGIN, y, bird_type)
            canvas.setLineWidth(0.5)
            canvas.line(MARGIN, y - 2, PAGE_W - MARGIN, y - 2)
            y -= ROW_H + 1

        if main_class != current_main_class:
            current_main_class = main_class
            if y < MARGIN + ROW_H * 3:
                page_num, y = _new_page(canvas, page_num, title, sd)
            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawString(MARGIN + 4 * mm, y, main_class)
            y -= ROW_H

        if y < MARGIN + ROW_H * 2:
            page_num, y = _new_page(canvas, page_num, title, sd)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(MARGIN + 8 * mm, y, f"{class_code}  {colour}"[:58])
        y -= ROW_H * 0.85

        for entry in entries_by_class[class_code]:
            if y < MARGIN + ROW_H:
                page_num, y = _new_page(canvas, page_num, title, sd)
            exhibitor = exhibitor_map.get(entry.exh_no)
            name = exhibitor.name if exhibitor else f"ExhNo {entry.exh_no}"
            canvas.setFont("Helvetica", 9)
            canvas.drawString(MARGIN + 14 * mm, y, f"{name}  (#{entry.exh_no})"[:72])
            y -= ROW_H * 0.9
        y -= 2

    return page_num, y


def _draw_by_exhibitor(canvas, page_num: int, y: float, entries_by_exhibitor, exhibitor_map, class_map, sd):
    title = "Entries Submitted - By Exhibitor"

    for exh_no in sorted(entries_by_exhibitor):
        exhibitor = exhibitor_map.get(exh_no)
        exhibitor_entries = entries_by_exhibitor[exh_no]
        count = len(exhibitor_entries)
        name = exhibitor.name if exhibitor else f"ExhNo {exh_no}"

        if y < MARGIN + ROW_H * 3:
            page_num, y = _new_page(canvas, page_num, title, sd)

        canvas.setFont("Helvetica-Bold", 10)
        label = f"#{exh_no}  {name}  -  {count} entr{'y' if count == 1 else 'ies'}"
        canvas.drawString(MARGIN, y, label[:70])
        canvas.setLineWidth(0.3)
        canvas.line(MARGIN, y - 2, PAGE_W - MARGIN, y - 2)
        y -= ROW_H

        for entry in sorted(exhibitor_entries, key=lambda row: _class_seq(row.class_code, class_map)):
            if y < MARGIN + ROW_H:
                page_num, y = _new_page(canvas, page_num, title, sd)
            class_def = class_map.get(entry.class_code)
            colour = class_def.colour if class_def else ""
            canvas.setFont("Helvetica", 9)
            canvas.drawString(MARGIN + 8 * mm, y, f"{(entry.class_code or ''):<8} {colour}"[:58])
            y -= ROW_H * 0.9

        y -= SECTION_GAP

    return page_num, y
