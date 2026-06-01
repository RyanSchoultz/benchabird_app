# tests/test_entries_received_pdf.py
import pytest
from models.show_entry import CalculatedEntry
from services.reports.entries_received import generate_entries_received


def test_generate_entries_received_empty(test_db):
    pdf = generate_entries_received()
    assert pdf[:4] == b'%PDF'


def test_generate_entries_received_with_data(test_db):
    for i in range(1, 6):
        CalculatedEntry.create(auto_num=i, exh_no=i, name=f"Exhibitor {i}", class_code=f"SC0{i}")
    pdf = generate_entries_received()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 1000


def test_generate_entries_received_multipage(test_db):
    for i in range(1, 152):
        CalculatedEntry.create(auto_num=i, exh_no=(i % 10) + 1,
                               name=f"Exhibitor {i % 10 + 1}", class_code=f"SC{i:03d}")
    pdf = generate_entries_received()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 5000
