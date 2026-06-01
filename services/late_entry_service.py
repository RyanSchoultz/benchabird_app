# services/late_entry_service.py
"""0050 Late_Entries — manage late entries separate from main show entries."""
from models.show_entry import LateEntry
from models.class_def import ClassDef


class LateEntryValidationError(ValueError):
    pass


def add_late_entry(exh_no: int, name: str, class_code: str) -> LateEntry:
    if not ClassDef.get_or_none(ClassDef.class_code == class_code):
        raise LateEntryValidationError(f"Class code '{class_code}' not found.")
    existing = LateEntry.select().order_by(LateEntry.auto_num.desc()).first()
    next_num = (existing.auto_num + 1) if existing else 1
    return LateEntry.create(auto_num=next_num, exh_no=exh_no, name=name, class_code=class_code)


def remove_late_entry(auto_num: int) -> None:
    LateEntry.delete().where(LateEntry.auto_num == auto_num).execute()
