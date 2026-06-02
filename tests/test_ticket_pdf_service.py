# tests/test_ticket_pdf_service.py
# No DB access — pure PDF generation test
from services.ticket_pdf_service import _ticket_qr_payload, generate_ticket_pdf

SAMPLE_TICKETS = [
    {'ticket_no': 1, 'auto_num': 1, 'exh_no': 5,  'name': 'Adams, A.', 'class_code': 'SC01'},
    {'ticket_no': 2, 'auto_num': 2, 'exh_no': 5,  'name': 'Adams, A.', 'class_code': 'SC02'},
    {'ticket_no': 3, 'auto_num': 3, 'exh_no': 10, 'name': 'Smith, J.', 'class_code': 'FB01'},
]


def test_generate_ticket_pdf_returns_valid_pdf():
    pdf = generate_ticket_pdf(SAMPLE_TICKETS, show_name="Test Show 2024")
    assert isinstance(pdf, bytes)
    assert pdf[:4] == b'%PDF'


def test_ticket_qr_payload_includes_auto_num():
    payload = _ticket_qr_payload(SAMPLE_TICKETS[0])
    assert "AutoNum:1" in payload
    assert "ExhNo:5" in payload
    assert "Class:SC01" in payload


def test_generate_ticket_pdf_empty_list():
    pdf = generate_ticket_pdf([], show_name="Empty Show")
    assert isinstance(pdf, bytes)
    assert pdf[:4] == b'%PDF'


def test_generate_ticket_pdf_large_set():
    tickets = [
        {'ticket_no': i, 'auto_num': i, 'exh_no': i % 50,
         'name': f'Exhibitor {i}', 'class_code': f'SC{i:02d}'}
        for i in range(1, 560)
    ]
    pdf = generate_ticket_pdf(tickets, show_name="Open Show 2023")
    assert isinstance(pdf, bytes)
    assert pdf[:4] == b'%PDF'
    # 559 tickets / 21 per page = 27 pages (rough check via file size)
    assert len(pdf) > 44_000
