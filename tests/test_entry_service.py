# tests/test_entry_service.py
import pytest
from models.show_entry import ShowEntry, LateEntry
from models.class_def import ClassDef
from services.entry_service import add_entry, bulk_add_entries, remove_entry, EntryValidationError

def test_add_entry(test_db):
    ClassDef.create(class_code="SC01", class_seq=10)
    entry = add_entry(exh_no=1, class_code="SC01")
    assert ShowEntry.select().count() == 1
    assert entry.exh_no == 1

def test_add_entry_unknown_class_raises(test_db):
    with pytest.raises(EntryValidationError, match="Class code"):
        add_entry(exh_no=1, class_code="BADCODE")

def test_remove_entry(test_db):
    ClassDef.create(class_code="SC01", class_seq=10)
    entry = add_entry(exh_no=1, class_code="SC01")
    remove_entry(entry.auto_num)
    assert ShowEntry.select().count() == 0

def test_add_entry_duplicate_raises(test_db):
    ClassDef.create(class_code="SC01", class_seq=10)
    add_entry(exh_no=1, class_code="SC01")
    with pytest.raises(EntryValidationError, match="already has an entry"):
        add_entry(exh_no=1, class_code="SC01")

def test_unlimited_class_allows_multiple_entries(test_db):
    ClassDef.create(class_code="SC01", class_seq=10, entry_limit=None)
    add_entry(exh_no=1, class_code="SC01")
    add_entry(exh_no=2, class_code="SC01")
    assert ShowEntry.select().count() == 2

def test_class_limit_blocks_second_normal_entry(test_db):
    ClassDef.create(class_code="SC01", class_seq=10, entry_limit=1)
    add_entry(exh_no=1, class_code="SC01")
    with pytest.raises(EntryValidationError, match="limit of 1"):
        add_entry(exh_no=2, class_code="SC01")

def test_duplicate_error_appears_before_limit_error(test_db):
    ClassDef.create(class_code="SC01", class_seq=10, entry_limit=1)
    add_entry(exh_no=1, class_code="SC01")
    with pytest.raises(EntryValidationError, match="already has an entry"):
        add_entry(exh_no=1, class_code="SC01")

def test_bulk_add_reports_limit_error(test_db):
    ClassDef.create(class_code="SC01", class_seq=10, entry_limit=1)
    ClassDef.create(class_code="SC02", class_seq=20, entry_limit=None)
    LateEntry.create(auto_num=1, exh_no=99, name="Late", class_code="SC01")
    successes, errors = bulk_add_entries(exh_no=1, class_codes=["SC01", "SC02"])
    assert successes == 1
    assert len(errors) == 1
    assert "limit of 1" in errors[0]
