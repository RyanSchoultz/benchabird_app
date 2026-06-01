# repository/results_repo.py
from models.results import Result, NotBenched
from models.special import SpecialList, SpecialWinner

class ResultsRepo:
    def get_result(self, exhibit_no: int):
        return Result.get_or_none(Result.exhibit_no == exhibit_no)

    def set_result(self, exhibit_no: int, result: str) -> Result:
        obj, _ = Result.get_or_create(exhibit_no=exhibit_no)
        obj.result = result
        obj.save()
        return obj

    def clear_results(self) -> int:
        return Result.update(result=None).execute()

    def get_all_results(self) -> list:
        return list(Result.select().where(Result.result.is_null(False)).order_by(Result.exhibit_no))

    def mark_not_benched(self, exhibit_no: int) -> NotBenched:
        return NotBenched.get_or_create(
            exhibit_no=exhibit_no,
            defaults={'not_benched': 'Not Benched', 'nb': 'NB'}
        )[0]

    def unmark_not_benched(self, exhibit_no: int) -> None:
        NotBenched.delete().where(NotBenched.exhibit_no == exhibit_no).execute()

    def get_not_benched_set(self) -> set:
        """Return set of exhibit numbers marked as not benched."""
        return {nb.exhibit_no for nb in NotBenched.select()}

    def is_not_benched(self, exhibit_no: int) -> bool:
        """Check if an exhibit number is marked as not benched."""
        return NotBenched.get_or_none(NotBenched.exhibit_no == exhibit_no) is not None

    def get_special_winners(self) -> list:
        return list(SpecialWinner.select().order_by(SpecialWinner.special_nr))

    def set_special_winner(self, special_nr: str, exhibit_no: int) -> SpecialWinner:
        obj, _ = SpecialWinner.get_or_create(special_nr=special_nr)
        obj.exhibit_no = exhibit_no
        obj.result = 'Special'
        obj.save()
        return obj

    def get_special_lists(self) -> list:
        return list(SpecialList.select().order_by(SpecialList.special_nr))
