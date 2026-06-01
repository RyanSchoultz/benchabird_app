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


def _faded_image_reader(logo_source, opacity: float = 0.12):
    """
    Return (ImageReader, (orig_w, orig_h)) for a logo rendered at reduced opacity,
    composited correctly over a white background.  Returns None on any failure.
    """
    from PIL import Image
    from reportlab.lib.utils import ImageReader
    import io as _io
    try:
        if isinstance(logo_source, (bytes, bytearray)):
            img = Image.open(_io.BytesIO(bytes(logo_source))).convert("RGBA")
        else:
            from pathlib import Path as _Path
            p = _Path(str(logo_source))
            if not p.exists():
                return None
            img = Image.open(str(p)).convert("RGBA")

        orig_size = img.size

        # Scale each pixel's alpha to the desired opacity — preserves colour fidelity
        r, g, b, a = img.split()
        a_faded = a.point(lambda v: int(v * opacity))
        img_faded = Image.merge("RGBA", (r, g, b, a_faded))

        # Alpha-composite onto a pure-white background so transparent areas become
        # white (matching the PDF page colour) instead of muddy grey.
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        composited = Image.alpha_composite(bg, img_faded)

        out = _io.BytesIO()
        composited.convert("RGB").save(out, format="PNG")
        out.seek(0)
        return ImageReader(out), orig_size
    except Exception:
        return None


def _draw_watermark(c: canvas.Canvas, sd) -> None:
    """Draw a centred, faded club-logo watermark behind page content."""
    if not sd:
        return
    logo_source = getattr(sd, 'logo_data', None) or getattr(sd, 'logo_path', None)
    if not logo_source:
        return

    result = _faded_image_reader(logo_source, opacity=0.12)
    if not result:
        return

    reader, (orig_w, orig_h) = result
    pts_w = 110 * mm
    pts_h = pts_w * orig_h / orig_w
    x = (PAGE_W - pts_w) / 2
    y = (PAGE_H - pts_h) / 2
    c.drawImage(reader, x, y, width=pts_w, height=pts_h)


def draw_page_header(c: canvas.Canvas, title: str, sd=None) -> float:
    """
    Draw watermark + header (show name, report title, date/club) at top of page.
    Returns the y coordinate of the content start line (below the rule).
    """
    _draw_watermark(c, sd)

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
    """Draw centred page number at the bottom of the current page."""
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(PAGE_W / 2, MARGIN - 4, f"Page {page_num}")
    c.setFillColorRGB(0, 0, 0)
