# tests/test_entry_service.py
import pytest
from models.show_entry import ShowEntry
from models.class_def import ClassDef
from services.entry_service import add_entry, remove_entry, EntryValidationError

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
