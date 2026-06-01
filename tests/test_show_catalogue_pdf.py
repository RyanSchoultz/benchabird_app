# tests/test_show_catalogue_pdf.py
import pytest
from models.show_entry import CalculatedEntry
from models.class_def import ClassDef
from services.reports.show_catalogue import generate_show_catalogue


def test_generate_show_catalogue_empty(test_db):
    pdf = generate_show_catalogue()
    assert pdf[:4] == b'%PDF'


def test_generate_show_catalogue_with_data(test_db):
    ClassDef.create(class_code="SC01", bird_type="Canary", class_seq=1)
    ClassDef.create(class_code="SC02", bird_type="Budgie", class_seq=2)
    CalculatedEntry.create(auto_num=1, exh_no=10, name="Alice", class_code="SC01")
    CalculatedEntry.create(auto_num=2, exh_no=11, name="Bob", class_code="SC02")
    CalculatedEntry.create(auto_num=3, exh_no=10, name="Alice", class_code="SC02")
    pdf = generate_show_catalogue()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 2000
