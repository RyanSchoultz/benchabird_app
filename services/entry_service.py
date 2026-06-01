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


def bulk_add_entries(exh_no: int, class_codes: list) -> tuple:
    """Add multiple entries for one exhibitor. Returns (success_count, error_list)."""
    successes = 0
    errors = []
    for code in class_codes:
        code = code.strip().upper()
        if not code:
            continue
        try:
            add_entry(exh_no=exh_no, class_code=code)
            successes += 1
        except EntryValidationError as e:
            errors.append(str(e))
    return successes, errors


def rename_class_code(old_code: str, new_code: str) -> int:
    """Rename all ShowEntry rows with old_code to new_code. Returns rows affected."""
    if not ClassDef.get_or_none(ClassDef.class_code == new_code):
        raise EntryValidationError(f"Class code '{new_code}' not found in class schedule.")
    return (
        ShowEntry.update(class_code=new_code)
        .where(ShowEntry.class_code == old_code)
        .execute()
    )


def delete_entries_for_exhibitor(exh_no: int) -> int:
    """Delete all ShowEntry rows for an exhibitor. Returns count deleted."""
    return ShowEntry.delete().where(ShowEntry.exh_no == exh_no).execute()


def reassign_exhibitor(from_no: int, to_no: int) -> int:
    """Move all ShowEntry rows from one exhibitor to another. Returns count updated."""
    return (
        ShowEntry.update(exh_no=to_no)
        .where(ShowEntry.exh_no == from_no)
        .execute()
    )
