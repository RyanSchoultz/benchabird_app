from models.exhibitor import Exhibitor
from models.show_entry import LateEntry, CalculatedEntry
from models.results import Result


def _seed(test_db):
    Exhibitor.create(exh_no=7, name="Alice Canary")
    LateEntry.create(auto_num=1, exh_no=7, name="Alice Canary", class_code="GL01")
    LateEntry.create(auto_num=2, exh_no=7, name="Alice Canary", class_code="RF01")


def test_bench_late_entries_creates_calculated_entries(test_db):
    from services.checkin_service import bench_late_entries
    _seed(test_db)
    result = bench_late_entries([1, 2])
    assert result.created == [1, 2]
    assert result.skipped == []
    rows = list(CalculatedEntry.select().order_by(CalculatedEntry.auto_num))
    assert [(r.auto_num, r.source_late_entry_auto_num, r.class_code) for r in rows] == [
        (1, 1, "GL01"),
        (2, 2, "RF01"),
    ]


def test_bench_late_entries_skips_already_benched(test_db):
    from services.checkin_service import bench_late_entries
    _seed(test_db)
    CalculatedEntry.create(auto_num=10, source_late_entry_auto_num=1, exh_no=7, class_code="GL01")
    result = bench_late_entries([1, 2])
    assert result.created == [11]
    assert result.skipped == [1]


def test_unbench_late_entries_removes_safe_row(test_db):
    from services.checkin_service import unbench_late_entries
    _seed(test_db)
    CalculatedEntry.create(auto_num=10, source_late_entry_auto_num=1, exh_no=7, class_code="GL01")
    result = unbench_late_entries([1])
    assert result.removed == [10]
    assert CalculatedEntry.get_or_none(CalculatedEntry.auto_num == 10) is None


def test_unbench_late_entries_blocks_when_result_exists(test_db):
    from services.checkin_service import unbench_late_entries
    _seed(test_db)
    CalculatedEntry.create(auto_num=10, source_late_entry_auto_num=1, exh_no=7, class_code="GL01")
    Result.create(exhibit_no=10, result="1st")
    result = unbench_late_entries([1])
    assert result.blocked == {1: "Has result"}
    assert CalculatedEntry.get_or_none(CalculatedEntry.auto_num == 10) is not None
