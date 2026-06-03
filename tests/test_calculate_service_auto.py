from models.show_entry import ShowEntry, CalculatedEntry
from models.class_def import ClassDef
from models.exhibitor import Exhibitor
from models.results import Result


def _seed(test_db):
    Exhibitor.create(exh_no=1, name="Adams, A.")
    ClassDef.create(class_code="SC01", class_seq=10)
    ShowEntry.create(auto_num=10, exh_no=1, class_code="SC01")


def test_auto_calculate_runs_silently_when_no_calculated_entries(test_db):
    from services.calculate_service import auto_calculate_if_safe
    _seed(test_db)
    result = auto_calculate_if_safe()
    assert result == "done"
    assert CalculatedEntry.select().count() == 1


def test_auto_calculate_runs_silently_when_only_full_calculate_rows_exist(test_db):
    from services.calculate_service import auto_calculate_if_safe
    _seed(test_db)
    # Full calculate row has source_entry_auto_num = NULL
    CalculatedEntry.create(auto_num=1, exh_no=1, class_code="SC01")
    result = auto_calculate_if_safe()
    assert result == "done"


def test_auto_calculate_warns_when_individual_benching_started(test_db):
    from services.calculate_service import auto_calculate_if_safe
    _seed(test_db)
    CalculatedEntry.create(auto_num=1, source_entry_auto_num=10, exh_no=1, class_code="SC01")
    result = auto_calculate_if_safe()
    assert result == "warning"
    # Should NOT have recalculated
    assert CalculatedEntry.select().count() == 1


def test_auto_calculate_blocked_when_results_recorded(test_db):
    from services.calculate_service import auto_calculate_if_safe
    _seed(test_db)
    CalculatedEntry.create(auto_num=1, source_entry_auto_num=10, exh_no=1, class_code="SC01")
    Result.create(exhibit_no=1, result="1st")
    result = auto_calculate_if_safe()
    assert result == "blocked"
