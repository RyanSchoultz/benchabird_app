# tests/test_prize_money_pdf.py
import pytest
from models.special import SpecialList, SpecialWinner
from models.show_entry import CalculatedEntry
from services.reports.prize_money import generate_prize_money


def test_generate_prize_money_empty(test_db):
    pdf = generate_prize_money()
    assert pdf[:4] == b'%PDF'


def test_generate_prize_money_with_cash_prizes(test_db):
    SpecialList.create(special_nr="S001", description="Best in Show",
                       prize1="Trophy", cash=0)
    SpecialList.create(special_nr="S002", description="Cash Prize",
                       prize1="R500", cash=500)
    CalculatedEntry.create(auto_num=5, exh_no=10, name="Alice", class_code="SC01")
    SpecialWinner.create(special_nr="S002", exhibit_no=5)
    pdf = generate_prize_money()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 1000


def test_generate_prize_money_no_cash_prizes(test_db):
    SpecialList.create(special_nr="S001", description="Trophy only",
                       prize1="Trophy", cash=0)
    pdf = generate_prize_money()
    assert pdf[:4] == b'%PDF'
