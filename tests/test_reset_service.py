# tests/test_reset_service.py
import pytest
from models.exhibitor import Exhibitor
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


def test_reset_clears_exh_nos_from_exhibitors(test_db):
    Exhibitor.create(exh_no=1, name="Adams, A.")
    Exhibitor.create(exh_no=2, name="Botha, B.")
    Exhibitor.create(exh_no=None, name="Cupido, C.")

    reset_show_data()

    exh_nos = [e.exh_no for e in Exhibitor.select()]
    assert all(n is None for n in exh_nos)


def test_reset_returns_counts(test_db):
    Exhibitor.create(exh_no=5, name="Adams, A.")
    ShowEntry.create(auto_num=1, exh_no=5, class_code="SC01")
    Result.create(exhibit_no=1, result="1st")
    counts = reset_show_data()
    assert counts['entries'] == 1
    assert counts['results'] == 1
    assert counts['exh_nos_cleared'] == 1
    assert set(counts.keys()) == {'entries', 'calculated', 'late_entries', 'results', 'not_benched', 'special_winners', 'exh_nos_cleared', 'entrants_cleared'}


def test_reset_on_empty_db_is_noop(test_db):
    counts = reset_show_data()
    assert sum(counts.values()) == 0


def test_reset_clears_is_entrant(test_db):
    Exhibitor.create(name="Flagged Person", is_entrant=True)
    Exhibitor.create(name="Unflagged Person", is_entrant=False)
    reset_show_data()
    assert all(not e.is_entrant for e in Exhibitor.select())


def test_reset_returns_entrants_cleared_count(test_db):
    Exhibitor.create(name="A", is_entrant=True)
    Exhibitor.create(name="B", is_entrant=True)
    Exhibitor.create(name="C", is_entrant=False)
    counts = reset_show_data()
    assert counts['entrants_cleared'] == 2
    assert 'entrants_cleared' in counts
