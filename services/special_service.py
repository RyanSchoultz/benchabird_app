# services/special_service.py
"""0080 Specialwin_M + 0140 Special_Lists_M — special award management."""
from repository.results_repo import ResultsRepo
from models.special import SpecialList

_repo = ResultsRepo()


def assign_special_winner(special_nr: str, exhibit_no: int):
    if not SpecialList.get_or_none(SpecialList.special_nr == special_nr):
        raise ValueError(f"Special prize '{special_nr}' not found.")
    return _repo.set_special_winner(special_nr, exhibit_no)


def clear_special_winner(special_nr: str) -> None:
    _repo.clear_special_winner(special_nr)


def get_winners_with_details() -> list:
    winners = _repo.get_special_winners()
    out = []
    for w in winners:
        sp = SpecialList.get_or_none(SpecialList.special_nr == w.special_nr)
        out.append({
            'special_nr':  w.special_nr,
            'exhibit_no':  w.exhibit_no,
            'description': sp.description if sp else '',
            'prize':       sp.prize1 if sp else '',
            'cash':        sp.cash if sp else None,
        })
    return out


def get_all_special_lists() -> list:
    return list(SpecialList.select().order_by(
        SpecialList.kind_sequence, SpecialList.special_nr
    ))


def save_special_list(
    special_nr: str, description: str, prize: str, cash: int = None
) -> SpecialList:
    with SpecialList._meta.database.atomic():
        sp, _ = SpecialList.get_or_create(special_nr=special_nr)
        sp.description = description
        sp.prize1 = prize
        sp.cash = cash
        sp.save()
        return sp


def delete_special_list(special_nr: str) -> None:
    sp = SpecialList.get_or_none(SpecialList.special_nr == special_nr)
    if sp:
        sp.delete_instance()
