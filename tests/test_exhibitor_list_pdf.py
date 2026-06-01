# tests/test_exhibitor_list_pdf.py
import pytest
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, LateEntry
from services.reports.exhibitor_list import generate_exhibitor_list


def test_generate_exhibitor_list_empty(test_db):
    pdf = generate_exhibitor_list()
    assert pdf[:4] == b'%PDF'


def test_generate_exhibitor_list_with_data(test_db):
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    Exhibitor.create(exh_no=2, name="Bob", town="Durban")
    ShowEntry.create(auto_num=1, exh_no=1, class_code="SC01")
    ShowEntry.create(auto_num=2, exh_no=1, class_code="SC02")
    LateEntry.create(auto_num=1, exh_no=2, name="Bob", class_code="SC01")
    pdf = generate_exhibitor_list()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 2000
