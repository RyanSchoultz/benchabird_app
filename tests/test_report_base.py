# tests/test_report_base.py
from services.reports.base import new_canvas, draw_page_header, draw_footer, PAGE_W, PAGE_H, MARGIN


def test_new_canvas_returns_buffer_and_canvas(test_db):
    from reportlab.pdfgen.canvas import Canvas
    buf, c = new_canvas()
    assert isinstance(c, Canvas)


def test_draw_page_header_returns_y_below_top(test_db):
    buf, c = new_canvas()
    y = draw_page_header(c, "Test Report")
    assert y < PAGE_H - MARGIN
    assert isinstance(y, float)


def test_draw_page_header_with_show_details_does_not_raise(test_db):
    from models.reference import ShowDetails
    sd = ShowDetails.create(show_eng="Cape Bird Show", date_eng="2026-06-15",
                            club_eng_full="Cape Bird Club")
    buf, c = new_canvas()
    y = draw_page_header(c, "Test Report", sd=sd)
    assert isinstance(y, float)


def test_draw_footer_does_not_raise(test_db):
    buf, c = new_canvas()
    draw_footer(c, page_num=1)


def test_canvas_save_produces_pdf_bytes(test_db):
    buf, c = new_canvas()
    draw_page_header(c, "Test")
    draw_footer(c, 1)
    c.save()
    data = buf.getvalue()
    assert data[:4] == b'%PDF'
