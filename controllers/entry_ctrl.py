# controllers/entry_ctrl.py
from repository.entry_repo import EntryRepo
from services.calculate_service import calculate_entries as _calculate
from services.entry_service import add_entry, remove_entry, EntryValidationError

_repo = EntryRepo()


def get_all_entries():
    return _repo.get_all()


def get_calculated():
    return _repo.get_calculated()


def run_calculate() -> int:
    return _calculate()


def add(exh_no: int, class_code: str):
    return add_entry(exh_no, class_code)


def remove(auto_num: int):
    remove_entry(auto_num)
