# tests/test_entry_confirmation_pdf.py
import pytest
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, CalculatedEntry, LateEntry
from models.class_def import ClassDef
from services.reports.entry_confirmation import generate_entry_confirmation


def test_empty_state_returns_valid_pdf(test_db):
    """No exhibitors — still produces a valid PDF without crashing."""
    pdf = generate_entry_confirmation()
    assert pdf[:4] == b'%PDF'


def test_exhibitor_with_no_entries_is_skipped(test_db):
    """An exhibitor with no entries does not crash the generator."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    pdf = generate_entry_confirmation()
    assert pdf[:4] == b'%PDF'


def test_uses_calculated_entry_when_available(test_db):
    """When CalculatedEntry rows exist, ticket numbers come from there."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    CalculatedEntry.create(auto_num=42, exh_no=1, name="Alice", class_code="SC01")
    pdf = generate_entry_confirmation()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 2000


def test_falls_back_to_show_entry_when_not_calculated(test_db):
    """When CalculatedEntry is empty, ShowEntry rows are used instead."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    ShowEntry.create(auto_num=1, exh_no=1, class_code="SC01")
    pdf = generate_entry_confirmation()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 2000


def test_include_late_true_adds_late_entries(test_db):
    """include_late=True produces a larger PDF than include_late=False when late entries exist."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    CalculatedEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC01")
    LateEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC02")
    pdf_with = generate_entry_confirmation(include_late=True)
    pdf_without = generate_entry_confirmation(include_late=False)
    assert pdf_with[:4] == b'%PDF'
    assert pdf_without[:4] == b'%PDF'
    assert len(pdf_with) > len(pdf_without)


def test_multiple_exhibitors_produces_larger_pdf(test_db):
    """Multiple exhibitors each get their own section."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    Exhibitor.create(exh_no=2, name="Bob", town="Durban")
    CalculatedEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC01")
    CalculatedEntry.create(auto_num=2, exh_no=2, name="Bob", class_code="SC02")
    pdf = generate_entry_confirmation()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 3000
