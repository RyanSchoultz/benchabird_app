# services/not_benched_service.py
"""0070 Not_Benched_M — mark entries as not physically benched."""
from repository.results_repo import ResultsRepo
from models.results import NotBenched

_repo = ResultsRepo()


def mark_not_benched(exhibit_no: int):
    return _repo.mark_not_benched(exhibit_no)


def unmark_not_benched(exhibit_no: int):
    _repo.unmark_not_benched(exhibit_no)


def get_not_benched_set() -> set:
    """Return set of exhibit numbers marked as not benched."""
    return {nb.exhibit_no for nb in NotBenched.select()}


def is_not_benched(exhibit_no: int) -> bool:
    """Check if an exhibit number is marked as not benched."""
    return NotBenched.get_or_none(NotBenched.exhibit_no == exhibit_no) is not None
