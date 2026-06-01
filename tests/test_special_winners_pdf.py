# tests/test_special_winners_pdf.py
import pytest
from models.special import SpecialList, SpecialWinner
from models.show_entry import CalculatedEntry
from services.reports.special_winners import generate_special_winners


def test_generate_special_winners_empty(test_db):
    pdf = generate_special_winners()
    assert pdf[:4] == b'%PDF'


def test_generate_special_winners_with_data(test_db):
    SpecialList.create(special_nr="S001", description="Best in Show",
                       prize1="Trophy", cash=0, kind="Open", kind_sequence="1")
    SpecialList.create(special_nr="S002", description="Best Canary",
                       prize1="Medal", cash=200, kind="Open", kind_sequence="2")
    CalculatedEntry.create(auto_num=1, exh_no=10, name="Alice", class_code="SC01")
    SpecialWinner.create(special_nr="S001", exhibit_no=1)
    pdf = generate_special_winners()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 2000
