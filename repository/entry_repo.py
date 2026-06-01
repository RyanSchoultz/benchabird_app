# repository/entry_repo.py
from models.show_entry import ShowEntry, CalculatedEntry, LateEntry
from repository import _chunks

class EntryRepo:
    def get_all(self) -> list:
        return list(ShowEntry.select().order_by(ShowEntry.auto_num))

    def by_exhibitor(self, exh_no: int) -> list:
        return list(ShowEntry.select().where(ShowEntry.exh_no == exh_no))

    def count(self) -> int:
        return ShowEntry.select().count()

    def add(self, auto_num: int, exh_no: int, class_code: str) -> ShowEntry:
        return ShowEntry.create(auto_num=auto_num, exh_no=exh_no, class_code=class_code)

    def remove(self, entry) -> None:
        entry.delete_instance()

    def replace_all(self, rows: list) -> None:
        """Wipe all ShowEntry rows and replace with rows. Import use only."""
        with ShowEntry._meta.database.atomic():
            ShowEntry.delete().execute()
            for batch in _chunks(rows, 200):
                ShowEntry.insert_many(batch).execute()

    def next_auto_num(self) -> int:
        result = ShowEntry.select(ShowEntry.auto_num).order_by(ShowEntry.auto_num.desc()).first()
        return (result.auto_num + 1) if result else 1

    def get_calculated(self) -> list:
        return list(CalculatedEntry.select().order_by(CalculatedEntry.auto_num))

    def calculated_count(self) -> int:
        return CalculatedEntry.select().count()

    def get_late(self) -> list:
        return list(LateEntry.select().order_by(LateEntry.auto_num))

    def late_count(self) -> int:
        return LateEntry.select().count()
