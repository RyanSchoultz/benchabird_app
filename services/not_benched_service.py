# services/not_benched_service.py
"""0070 Not_Benched_M — mark entries as not physically benched."""
from repository.results_repo import ResultsRepo

_repo = ResultsRepo()


def mark_not_benched(exhibit_no: int):
    return _repo.mark_not_benched(exhibit_no)


def unmark_not_benched(exhibit_no: int):
    _repo.unmark_not_benched(exhibit_no)
