# services/reports/base.py
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

PAGE_W, PAGE_H = A4
MARGIN = 15 * mm
ROW_H = 6.5 * mm
TOP_Y = PAGE_H - MARGIN


def new_canvas() -> tuple:
    """Return (BytesIO buffer, Canvas). Call c.save() then buf.getvalue() when done."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, pageCompression=0)
    return buf, c


def draw_page_header(c: canvas.Canvas, title: str, sd=None) -> float:
    """
    Draw show name (left) and report title (right) at top of page.
    Returns the y coordinate of the content start line (below the rule).
    """
    show_name = ""
    date_club = ""
    if sd:
        show_name = sd.show_eng or ""
        parts = [p for p in [sd.date_eng, sd.club_eng_full] if p]
        date_club = "  |  ".join(parts)

    c.setFont("Helvetica-Bold", 13)
    c.drawString(MARGIN, TOP_Y, show_name)
    c.setFont("Helvetica", 11)
    c.drawRightString(PAGE_W - MARGIN, TOP_Y, title)

    if date_club:
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN, TOP_Y - 14, date_club)

    rule_y = TOP_Y - 26
    c.setLineWidth(0.5)
    c.line(MARGIN, rule_y, PAGE_W - MARGIN, rule_y)
    return float(rule_y - 8)


def draw_footer(c: canvas.Canvas, page_num: int) -> None:
    """Draw centered page number at bottom of current page."""
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(PAGE_W / 2, MARGIN - 4, f"Page {page_num}")
    c.setFillColorRGB(0, 0, 0)
