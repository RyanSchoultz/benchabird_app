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


def _faded_image_reader(logo_data, opacity: float = 0.14):
    """
    Return (ImageReader, (orig_w, orig_h)) for a logo at reduced opacity,
    correctly alpha-composited onto white.  Returns None on failure.
    """
    if not logo_data:
        return None
    from PIL import Image
    from reportlab.lib.utils import ImageReader
    import io as _io
    try:
        img = Image.open(_io.BytesIO(bytes(logo_data))).convert("RGBA")
        orig_size = img.size
        r, g, b, a = img.split()
        a_faded = a.point(lambda v: int(v * opacity))
        img_faded = Image.merge("RGBA", (r, g, b, a_faded))
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        composited = Image.alpha_composite(bg, img_faded)
        out = _io.BytesIO()
        composited.convert("RGB").save(out, format="PNG")
        out.seek(0)
        return ImageReader(out), orig_size
    except Exception:
        return None


def _ticket_qr_payload(ticket: dict) -> str:
    return (
        f"AutoNum:{ticket.get('auto_num') or ticket.get('ticket_no') or ''} "
        f"ExhNo:{ticket.get('exh_no') or ''} "
        f"Class:{ticket.get('class_code') or ''}"
    )


def _make_qr_reader(ticket: dict):
    """Generate a QR code image reader for ReportLab embedding."""
    import qrcode
    from qrcode.image.pil import PilImage
    from reportlab.lib.utils import ImageReader
    import io as _io
    data = _ticket_qr_payload(ticket)
    qr = qrcode.QRCode(box_size=3, border=2,
                       error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(image_factory=PilImage,
                        fill_color="black", back_color="white")
    buf = _io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def generate_ticket_pdf(tickets: list, show_name: str = "Bird Show",
                        logo_data: bytes = None) -> bytes:
    """
    Generate an A4 PDF of cage tickets.

    Args:
        tickets:    list of dicts with keys ticket_no, auto_num, exh_no, name, class_code
        show_name:  printed at the bottom of each ticket
        logo_data:  raw PNG/JPG bytes for the club-logo watermark (optional)
    """
    buf = io.BytesIO()
    page_w, page_h = A4

    ticket_w = (page_w - 2 * MARGIN) / COLS
    ticket_h = (page_h - 2 * MARGIN) / ROWS_PER_PAGE

    c = canvas.Canvas(buf, pagesize=A4)

    # Pre-compute faded logo reader once — reused for every ticket
    logo_reader = _faded_image_reader(logo_data, opacity=0.14) if logo_data else None

    tickets_per_page = COLS * ROWS_PER_PAGE

    for i, ticket in enumerate(tickets):
        pos = i % tickets_per_page
        if pos == 0 and i > 0:
            c.showPage()

        col = pos % COLS
        row = pos // COLS

        x = MARGIN + col * ticket_w
        y = page_h - MARGIN - (row + 1) * ticket_h

        _draw_ticket(c, x, y, ticket_w, ticket_h, ticket, show_name, logo_reader)

    if not tickets:
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN, page_h / 2, "No tickets to print.")

    c.save()
    return buf.getvalue()


def _draw_ticket(c, x: float, y: float, w: float, h: float,
                 ticket: dict, show_name: str,
                 logo_reader=None) -> None:
    """Draw a single ticket cell at (x, y) with dimensions (w × h)."""
    pad = 3 * mm
    qr_size = 19 * mm

    # Ticket border
    c.rect(x, y, w, h)

    # ── Club logo watermark — centred inside the ticket ───────────
    if logo_reader:
        reader, (orig_w, orig_h) = logo_reader
        wm_w = w * 0.44
        wm_h = wm_w * orig_h / orig_w
        wx = x + (w - wm_w) / 2
        wy = y + (h - wm_h) / 2
        c.drawImage(reader, wx, wy, width=wm_w, height=wm_h)

    # ── QR code — top-right corner ───────────────────────────────
    try:
        qr_img = _make_qr_reader(ticket)
        c.drawImage(qr_img, x + w - qr_size - pad,
                    y + h - qr_size - pad,
                    width=qr_size, height=qr_size, mask='auto')
    except Exception:
        pass

    # ── Ticket number — large and prominent ──────────────────────
    c.setFont("Helvetica-Bold", 20)
    c.drawString(x + pad, y + h - 10 * mm, f"#{ticket['ticket_no']:03d}")

    # ── Class code ───────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 9)
    class_code = (ticket['class_code'] or '')[:12]
    c.drawString(x + pad, y + h - 16 * mm, f"Class: {class_code}")

    # ── Exhibitor number ─────────────────────────────────────────
    c.setFont("Helvetica", 9)
    c.drawString(x + pad, y + h - 21 * mm, f"ExhNo: {ticket['exh_no'] or ''}")

    # ── Exhibitor name ───────────────────────────────────────────
    name = (ticket['name'] or '')[:28]
    c.drawString(x + pad, y + h - 26 * mm, name)

    # ── Show name — small italic at bottom ───────────────────────
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(x + pad, y + pad, show_name[:38])
