# services/special_service.py
"""0080 Specialwin_M + 0140 Special_Lists_M — special award management."""
from repository.results_repo import ResultsRepo
from models.special import SpecialList

_repo = ResultsRepo()


def assign_special_winner(special_nr: str, exhibit_no: int):
    if not SpecialList.get_or_none(SpecialList.special_nr == special_nr):
        raise ValueError(f"Special prize '{special_nr}' not found.")
    return _repo.set_special_winner(special_nr, exhibit_no)


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
