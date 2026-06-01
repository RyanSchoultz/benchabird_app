# services/results_service.py
"""
0130 Results_M — record and clear results.
The 0051T Results_Clear_T pattern (3000-row template of NULLs) is
replicated here by clear_results(), which resets all results to NULL.
"""
from repository.results_repo import ResultsRepo

_repo = ResultsRepo()


def record_result(exhibit_no: int, result: str):
    return _repo.set_result(exhibit_no, result)


def clear_results() -> int:
    """Reset all result values to NULL. Returns rows affected."""
    return _repo.clear_results()


def get_results_summary() -> dict:
    results = _repo.get_all_results()
    return {r.exhibit_no: r.result for r in results}
