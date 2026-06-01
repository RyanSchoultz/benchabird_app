# services/entry_service.py
"""0030 Show_Entries_M — add, remove, and validate show entries."""
from models.show_entry import ShowEntry
from models.class_def import ClassDef
from repository.entry_repo import EntryRepo

_repo = EntryRepo()


class EntryValidationError(ValueError):
    pass


def add_entry(exh_no: int, class_code: str) -> ShowEntry:
    if not ClassDef.get_or_none(ClassDef.class_code == class_code):
        raise EntryValidationError(f"Class code '{class_code}' not found in class schedule.")
    existing = ShowEntry.get_or_none(
        (ShowEntry.exh_no == exh_no) & (ShowEntry.class_code == class_code)
    )
    if existing:
        raise EntryValidationError(
            f"Exhibitor {exh_no} already has an entry for class {class_code}."
        )
    next_num = _repo.next_auto_num()
    return _repo.add(next_num, exh_no, class_code)


def remove_entry(auto_num: int) -> None:
    entry = ShowEntry.get_or_none(ShowEntry.auto_num == auto_num)
    if entry:
        entry.delete_instance()
