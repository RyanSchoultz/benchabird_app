"""Marked Catalogue report (Access menu 4.4)."""

from reportlab.lib.units import mm

from models.show_entry import CalculatedEntry
from services.reports.base import MARGIN, PAGE_W, ROW_H, draw_footer, draw_page_header, new_canvas


def generate_marked_catalogue(sd=None) -> bytes:
    sql = """
        SELECT
            ce.auto_num,
            ce.exh_no,
            ce.name,
            ce.class_code,
            COALESCE(cd.bird_type, ''),
            COALESCE(cd.class_seq, 999999),
            COALESCE(r.result, ''),
            COALESCE(nb.nb, ''),
            COALESCE(sl.description, sw.special_nr, '')
        FROM calculated_entry ce
        LEFT JOIN class_def cd ON ce.class_code = cd.class_code
        LEFT JOIN result r ON r.exhibit_no = ce.auto_num
        LEFT JOIN not_benched nb ON nb.exhibit_no = ce.auto_num
        LEFT JOIN special_winner sw ON sw.exhibit_no = ce.auto_num
        LEFT JOIN special_list sl ON sl.special_nr = sw.special_nr
        ORDER BY CAST(COALESCE(cd.class_seq, 999999) AS REAL), ce.auto_num
    """
    db = CalculatedEntry._meta.database
    rows = db.execute_sql(sql).fetchall()

    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "4.4 Marked Catalogue", sd)

    if not rows:
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN, y, "No benched birds found. Use Show Participants before generating this report.")
        draw_footer(c, page_num)
        c.save()
        return buf.getvalue()

    last_class = None
    for auto_num, exh_no, name, class_code, bird_type, _, result, nb, special in rows:
        if y < MARGIN + ROW_H * 4:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            y = draw_page_header(c, "4.4 Marked Catalogue", sd)
            last_class = None

        if class_code != last_class:
            c.setFont("Helvetica-Bold", 10)
            label = f"{class_code or ''}  {bird_type}".strip()
            c.drawString(MARGIN, y, label)
            c.setLineWidth(0.4)
            c.line(MARGIN, y - 1, PAGE_W - MARGIN, y - 1)
            y -= ROW_H + 1
            last_class = class_code

        markers = []
        if result:
            markers.append(f"Result: {result}")
        if nb:
            markers.append("NB")
        if special:
            markers.append(f"Special: {special}")

        c.setFont("Helvetica-Bold", 9)
        c.drawString(MARGIN + 3 * mm, y, str(auto_num))
        c.setFont("Helvetica", 8)
        c.drawString(MARGIN + 18 * mm, y, str(exh_no or ""))
        c.drawString(MARGIN + 34 * mm, y, (name or "")[:35])
        c.drawRightString(PAGE_W - MARGIN, y, " | ".join(markers))
        y -= ROW_H

    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()
