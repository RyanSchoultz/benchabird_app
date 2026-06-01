# tests/test_results_sheet_pdf.py
import pytest
from models.results import Result, NotBenched
from models.show_entry import CalculatedEntry
from services.reports.results_sheet import generate_results_sheet


def test_generate_results_sheet_empty(test_db):
    pdf = generate_results_sheet()
    assert pdf[:4] == b'%PDF'


def test_generate_results_sheet_with_data(test_db):
    CalculatedEntry.create(auto_num=1, exh_no=10, name="Alice", class_code="SC01")
    CalculatedEntry.create(auto_num=2, exh_no=11, name="Bob", class_code="SC02")
    Result.create(exhibit_no=1, result="1st")
    Result.create(exhibit_no=2, result="BOB")
    NotBenched.create(exhibit_no=2)
    pdf = generate_results_sheet()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 2000
