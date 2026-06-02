import pytest

from models.class_def import ClassDef
from models.show_entry import LateEntry
from services.entry_service import EntryValidationError, add_entry
from services.late_entry_service import LateEntryValidationError, add_late_entry


def test_late_entry_respects_limit_filled_by_normal_entries(test_db):
    ClassDef.create(class_code="SC01", entry_limit=1)
    add_entry(exh_no=1, class_code="SC01")

    with pytest.raises(LateEntryValidationError, match="limit of 1"):
        add_late_entry(exh_no=2, name="Late Bird", class_code="SC01")


def test_normal_entry_respects_limit_filled_by_late_entries(test_db):
    ClassDef.create(class_code="SC01", entry_limit=1)
    LateEntry.create(auto_num=1, exh_no=2, name="Late Bird", class_code="SC01")

    with pytest.raises(EntryValidationError, match="limit of 1"):
        add_entry(exh_no=1, class_code="SC01")
