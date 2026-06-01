# tests/test_reset_service.py
import pytest
from models.show_entry import ShowEntry, CalculatedEntry, LateEntry
from models.results import Result, NotBenched
from models.special import SpecialWinner
from models.class_def import ClassDef
from services.reset_service import reset_show_data


def test_reset_clears_all_show_data(test_db):
    ClassDef.create(class_code="SC01", class_seq=10)
    ShowEntry.create(auto_num=1, exh_no=1, class_code="SC01")
    CalculatedEntry.create(auto_num=1, exh_no=1, name="Test", class_code="SC01")
    LateEntry.create(auto_num=1, exh_no=2, name="Late", class_code="SC01")
    Result.create(exhibit_no=1, result="1st")
    NotBenched.create(exhibit_no=2)
    SpecialWinner.create(special_nr="S1", exhibit_no=1)

    counts = reset_show_data()

    assert ShowEntry.select().count() == 0
    assert CalculatedEntry.select().count() == 0
    assert LateEntry.select().count() == 0
    assert Result.select().count() == 0
    assert NotBenched.select().count() == 0
    assert SpecialWinner.select().count() == 0
    assert ClassDef.select().count() == 1  # NOT cleared


def test_reset_returns_counts(test_db):
    ShowEntry.create(auto_num=1, exh_no=1, class_code="SC01")
    Result.create(exhibit_no=1, result="1st")
    counts = reset_show_data()
    assert counts['entries'] == 1
    assert counts['results'] == 1
    assert set(counts.keys()) == {'entries', 'calculated', 'late_entries', 'results', 'not_benched', 'special_winners'}


def test_reset_on_empty_db_is_noop(test_db):
    counts = reset_show_data()
    assert sum(counts.values()) == 0
