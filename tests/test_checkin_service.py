from models.class_def import ClassDef
from models.exhibitor import Exhibitor
from models.results import NotBenched, Result
from models.show_entry import CalculatedEntry, ShowEntry
from models.special import SpecialWinner


def seed_checkin_data():
    Exhibitor.create(exh_no=7, name="Alice Canary", email="alice@example.com", town="Cape Town", club="ABC")
    Exhibitor.create(exh_no=8, name="Bob Finch", email="bob@example.com", town="Durban", club="DEF")
    ClassDef.create(class_code="GL01", colour="Corona hen", bird_type="Gloster")
    ClassDef.create(class_code="RF01", colour="Red cock", bird_type="Red Factor")
    ShowEntry.create(auto_num=100, exh_no=7, class_code="GL01")
    ShowEntry.create(auto_num=101, exh_no=7, class_code="RF01")
    ShowEntry.create(auto_num=102, exh_no=8, class_code="GL01")


def test_search_checkin_exhibitors_by_name_email_number_class_and_autonum(test_db):
    from services.checkin_service import search_checkin_exhibitors

    seed_checkin_data()
    CalculatedEntry.create(auto_num=55, source_entry_auto_num=101, exh_no=7, name="Alice Canary", class_code="RF01")

    assert [m.exh_no for m in search_checkin_exhibitors("alice")] == [7]
    assert [m.exh_no for m in search_checkin_exhibitors("alice@example")] == [7]
    assert [m.exh_no for m in search_checkin_exhibitors("7")] == [7]
    assert [m.exh_no for m in search_checkin_exhibitors("RF01")] == [7]
    assert [m.exh_no for m in search_checkin_exhibitors("55")] == [7]


def test_get_checkin_entries_includes_benched_status(test_db):
    from services.checkin_service import get_checkin_entries

    seed_checkin_data()
    CalculatedEntry.create(auto_num=55, source_entry_auto_num=100, exh_no=7, name="Alice Canary", class_code="GL01")

    rows = get_checkin_entries(7)

    assert [(r.source_entry_auto_num, r.class_code, r.auto_num, r.status) for r in rows] == [
        (100, "GL01", 55, "Benched #55"),
        (101, "RF01", None, "Not benched"),
    ]


def test_get_checkin_entries_shows_legacy_allocation_without_source_link(test_db):
    from services.checkin_service import get_checkin_entries

    seed_checkin_data()
    CalculatedEntry.create(auto_num=55, exh_no=7, name="Alice Canary", class_code="GL01")

    rows = get_checkin_entries(7)

    assert rows[0].source_entry_auto_num == 100
    assert rows[0].auto_num == 55
    assert rows[0].status == "Legacy allocation #55"
    assert rows[0].blocked_reason == "Legacy allocation"


def test_bench_entries_allocates_next_autonums_and_source_links(test_db):
    from services.checkin_service import bench_entries

    seed_checkin_data()
    CalculatedEntry.create(auto_num=10, source_entry_auto_num=102, exh_no=8, name="Bob Finch", class_code="GL01")

    result = bench_entries([100, 101])

    rows = list(CalculatedEntry.select().where(CalculatedEntry.exh_no == 7).order_by(CalculatedEntry.auto_num))
    assert result.created == [11, 12]
    assert [(r.auto_num, r.source_entry_auto_num, r.name, r.class_code) for r in rows] == [
        (11, 100, "Alice Canary", "GL01"),
        (12, 101, "Alice Canary", "RF01"),
    ]


def test_bench_entries_allocates_selected_entries_by_class_sequence(test_db):
    from services.checkin_service import bench_entries

    Exhibitor.create(exh_no=9, name="Sorted Exhibitor")
    ClassDef.create(class_code="LATE", class_seq=20)
    ClassDef.create(class_code="EARLY", class_seq=5)
    ShowEntry.create(auto_num=200, exh_no=9, class_code="LATE")
    ShowEntry.create(auto_num=201, exh_no=9, class_code="EARLY")

    result = bench_entries([200, 201])

    rows = list(CalculatedEntry.select().order_by(CalculatedEntry.auto_num))
    assert result.created == [1, 2]
    assert [(row.auto_num, row.source_entry_auto_num, row.class_code) for row in rows] == [
        (1, 201, "EARLY"),
        (2, 200, "LATE"),
    ]


def test_bench_entries_skips_already_benched(test_db):
    from services.checkin_service import bench_entries

    seed_checkin_data()
    CalculatedEntry.create(auto_num=10, source_entry_auto_num=100, exh_no=7, name="Alice Canary", class_code="GL01")

    result = bench_entries([100, 101])

    assert result.created == [11]
    assert result.skipped == [100]
    assert CalculatedEntry.select().where(CalculatedEntry.exh_no == 7).count() == 2


def test_unbench_entry_removes_safe_calculated_row(test_db):
    from services.checkin_service import unbench_entries

    seed_checkin_data()
    CalculatedEntry.create(auto_num=10, source_entry_auto_num=100, exh_no=7, name="Alice Canary", class_code="GL01")

    result = unbench_entries([100])

    assert result.removed == [10]
    assert CalculatedEntry.get_or_none(CalculatedEntry.auto_num == 10) is None


def test_unbench_entry_blocks_dependent_rows(test_db):
    from services.checkin_service import unbench_entries

    seed_checkin_data()
    CalculatedEntry.create(auto_num=10, source_entry_auto_num=100, exh_no=7, name="Alice Canary", class_code="GL01")
    CalculatedEntry.create(auto_num=11, source_entry_auto_num=101, exh_no=7, name="Alice Canary", class_code="RF01")
    Result.create(exhibit_no=10, result="1st")
    NotBenched.create(exhibit_no=11, not_benched="Not Benched", nb="NB")

    result = unbench_entries([100, 101])

    assert result.removed == []
    assert result.blocked == {100: "Has result", 101: "Marked NB"}
    assert CalculatedEntry.select().where(CalculatedEntry.exh_no == 7).count() == 2


def test_unbench_entry_blocks_special_winner(test_db):
    from services.checkin_service import unbench_entries

    seed_checkin_data()
    CalculatedEntry.create(auto_num=10, source_entry_auto_num=100, exh_no=7, name="Alice Canary", class_code="GL01")
    SpecialWinner.create(special_nr="S1", exhibit_no=10, result="Winner")

    result = unbench_entries([100])

    assert result.blocked == {100: "Special winner"}
    assert CalculatedEntry.get_or_none(CalculatedEntry.auto_num == 10) is not None
