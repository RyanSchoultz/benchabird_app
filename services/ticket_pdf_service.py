# services/ticket_pdf_service.py
"""Generate a printable PDF of exhibit cage tickets using ReportLab canvas."""
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

# Layout: 3 columns × 7 rows = 21 tickets per A4 page
COLS = 3
ROWS_PER_PAGE = 7
MARGIN = 10 * mm


def generate_ticket_pdf(tickets: list, show_name: str = "Bird Show") -> bytes:
    """
    Generate an A4 PDF of cage tickets.

    Args:
        tickets: list of dicts with keys ticket_no, auto_num, exh_no, name, class_code
        show_name: printed at the bottom of each ticket

    Returns:
        PDF as bytes (starts with b'%PDF')
    """
    buf = io.BytesIO()
    page_w, page_h = A4  # 595.28 x 841.89 pts

    ticket_w = (page_w - 2 * MARGIN) / COLS
    ticket_h = (page_h - 2 * MARGIN) / ROWS_PER_PAGE

    c = canvas.Canvas(buf, pagesize=A4)

    tickets_per_page = COLS * ROWS_PER_PAGE

    for i, ticket in enumerate(tickets):
        pos = i % tickets_per_page
        if pos == 0 and i > 0:
            c.showPage()

        col = pos % COLS
        row = pos // COLS

        x = MARGIN + col * ticket_w
        y = page_h - MARGIN - (row + 1) * ticket_h

        _draw_ticket(c, x, y, ticket_w, ticket_h, ticket, show_name)

    if not tickets:
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN, page_h / 2, "No tickets to print.")

    c.save()
    return buf.getvalue()


def _draw_ticket(c, x: float, y: float, w: float, h: float,
                 ticket: dict, show_name: str) -> None:
    """Draw a single ticket at (x, y) with dimensions (w, h)."""
    pad = 3 * mm

    c.rect(x, y, w, h)

    # Exhibit number — large and prominent
    c.setFont("Helvetica-Bold", 20)
    c.drawString(x + pad, y + h - 10 * mm, f"#{ticket['ticket_no']:03d}")

    # Class code — secondary heading
    c.setFont("Helvetica-Bold", 9)
    class_code = (ticket['class_code'] or '')[:12]
    c.drawString(x + pad, y + h - 16 * mm, f"Class: {class_code}")

    # Exhibitor number
    c.setFont("Helvetica", 9)
    c.drawString(x + pad, y + h - 21 * mm, f"ExhNo: {ticket['exh_no'] or ''}")

    # Exhibitor name (truncate to avoid overflow)
    name = (ticket['name'] or '')[:28]
    c.drawString(x + pad, y + h - 26 * mm, name)

    # Show name — small italic at bottom
    c.setFont("Helvetica-Oblique", 7)
    show = show_name[:38]
    c.drawString(x + pad, y + pad, show)
