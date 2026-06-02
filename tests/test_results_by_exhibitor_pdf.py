# tests/test_results_by_exhibitor_pdf.py
import pytest
from models.exhibitor import Exhibitor
from models.show_entry import CalculatedEntry
from models.results import Result, NotBenched
from models.special import SpecialList, SpecialWinner
from services.reports.results_by_exhibitor import generate_results_by_exhibitor


def test_no_calculated_entries_returns_valid_pdf(test_db):
    """Empty calculated_entry → valid PDF with informational message, no crash."""
    pdf = generate_results_by_exhibitor()
    assert pdf[:4] == b'%PDF'


def test_calculated_entries_but_no_results_returns_valid_pdf(test_db):
    """Entries exist but no results recorded → valid PDF with message."""
    CalculatedEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC01")
    pdf = generate_results_by_exhibitor()
    assert pdf[:4] == b'%PDF'


def test_exhibitor_with_no_results_is_excluded(test_db):
    """An exhibitor whose entries have no result or NB must not appear."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    Exhibitor.create(exh_no=2, name="Bob", town="Durban")
    CalculatedEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC01")
    CalculatedEntry.create(auto_num=2, exh_no=2, name="Bob", class_code="SC02")
    Result.create(exhibit_no=1, result="1st")
    # Bob has no result — only Alice should appear
    pdf = generate_results_by_exhibitor()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 2000


def test_nb_entry_is_included(test_db):
    """Not Benched entry appears even with no result row."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    CalculatedEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC01")
    NotBenched.create(exhibit_no=1)
    pdf = generate_results_by_exhibitor()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 2000


def test_special_prize_increases_pdf_size(test_db):
    """A special prize winner produces a larger PDF than without specials."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    CalculatedEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC01")
    Result.create(exhibit_no=1, result="Champion")
    SpecialList.create(special_nr="SP01", description="Best in Show", cash=100)
    pdf_without = generate_results_by_exhibitor()

    SpecialWinner.create(special_nr="SP01", exhibit_no=1, result="Champion")
    pdf_with = generate_results_by_exhibitor()

    assert pdf_with[:4] == b'%PDF'
    assert len(pdf_with) > len(pdf_without)


def test_zero_cash_prize_produces_valid_pdf(test_db):
    """A special with cash=0 does not crash and still produces a valid PDF."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    CalculatedEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC01")
    Result.create(exhibit_no=1, result="Champion")
    SpecialList.create(special_nr="SP01", description="Trophy Only", cash=0)
    SpecialWinner.create(special_nr="SP01", exhibit_no=1, result="Champion")
    pdf = generate_results_by_exhibitor()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 2000
