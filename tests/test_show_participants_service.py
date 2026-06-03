from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, LateEntry, CalculatedEntry


def _seed(test_db):
    Exhibitor.create(id=1, exh_no=1, name="Adams, A.", email="a@test.com", town="Cape Town")
    Exhibitor.create(id=2, exh_no=2, name="Botha, B.", email="b@test.com", town="Durban")
    Exhibitor.create(id=3, exh_no=None, name="Cupido, C.", email="c@test.com")
    ShowEntry.create(auto_num=10, exh_no=1, class_code="SC01")
    ShowEntry.create(auto_num=11, exh_no=1, class_code="SC02")
    ShowEntry.create(auto_num=12, exh_no=2, class_code="SC01")
    LateEntry.create(auto_num=1, exh_no=2, name="Botha, B.", class_code="SC03")


def test_get_participants_returns_exhibitors_with_exh_no(test_db):
    from services.show_participants_service import get_participants
    _seed(test_db)
    # exh_no=1 has entries, exh_no=2 has entries. Cupido (exh_no=None) must NOT appear.
    rows = get_participants()
    exh_nos = [r.exh_no for r in rows]
    assert 1 in exh_nos
    assert 2 in exh_nos
    assert None not in exh_nos


def test_get_participants_includes_exhibitor_with_no_entries(test_db):
    from services.show_participants_service import get_participants
    Exhibitor.create(id=10, exh_no=5, name="Zero Entry Person")
    rows = get_participants()
    assert any(r.exh_no == 5 for r in rows)
    zero = next(r for r in rows if r.exh_no == 5)
    assert zero.entry_count == 0
    assert zero.benched_count == 0


def test_get_participants_counts_entries_and_late(test_db):
    from services.show_participants_service import get_participants
    _seed(test_db)
    rows = get_participants()
    a = next(r for r in rows if r.exh_no == 1)
    b = next(r for r in rows if r.exh_no == 2)
    assert a.entry_count == 2 and a.late_count == 0
    assert b.entry_count == 2 and b.late_count == 1


def test_get_participants_counts_benched(test_db):
    from services.show_participants_service import get_participants
    _seed(test_db)
    CalculatedEntry.create(auto_num=100, source_entry_auto_num=10, exh_no=1, class_code="SC01")
    rows = get_participants()
    a = next(r for r in rows if r.exh_no == 1)
    assert a.benched_count == 1


def test_get_participants_filter_unbenched(test_db):
    from services.show_participants_service import get_participants
    _seed(test_db)
    CalculatedEntry.create(auto_num=100, source_entry_auto_num=10, exh_no=1, class_code="SC01")
    CalculatedEntry.create(auto_num=101, source_entry_auto_num=11, exh_no=1, class_code="SC02")
    rows = get_participants(filter="unbenched")
    assert [r.exh_no for r in rows] == [2]


def test_get_participants_filter_late(test_db):
    from services.show_participants_service import get_participants
    _seed(test_db)
    rows = get_participants(filter="late")
    assert [r.exh_no for r in rows] == [2]


def test_search_registry_finds_by_name(test_db):
    from services.show_participants_service import search_registry
    _seed(test_db)
    results = search_registry("Cupido")
    assert len(results) == 1 and results[0].name == "Cupido, C."


def test_get_orphaned_exh_nos_detects_missing_exhibitor(test_db):
    from services.show_participants_service import get_orphaned_exh_nos
    _seed(test_db)
    ShowEntry.create(auto_num=99, exh_no=99, class_code="SC01")
    orphans = get_orphaned_exh_nos()
    assert 99 in orphans
    assert 1 not in orphans


def test_next_available_exh_no(test_db):
    from services.show_participants_service import next_available_exh_no
    _seed(test_db)
    assert next_available_exh_no() == 3


def test_assign_exh_no_sets_and_validates_uniqueness(test_db):
    import pytest
    from services.show_participants_service import assign_exh_no
    _seed(test_db)
    assign_exh_no(exhibitor_id=3, exh_no=5)
    assert Exhibitor.get_by_id(3).exh_no == 5
    with pytest.raises(ValueError, match="already assigned"):
        assign_exh_no(exhibitor_id=3, exh_no=1)


# ── Task 4: per-exhibitor entries ────────────────────────────────────────────

from models.class_glossary import ClassGlossary
from models.results import Result


def test_get_participant_entries_show_entry_not_benched(test_db):
    from services.show_participants_service import get_participant_entries
    Exhibitor.create(exh_no=1, name="Adams, A.")
    ShowEntry.create(auto_num=10, exh_no=1, class_code="SC01")
    rows = get_participant_entries(1)
    assert len(rows) == 1
    assert rows[0].source_auto_num == 10
    assert rows[0].is_late is False
    assert rows[0].auto_num is None
    assert rows[0].status == "Not benched"


def test_get_participant_entries_show_entry_benched(test_db):
    from services.show_participants_service import get_participant_entries
    Exhibitor.create(exh_no=1, name="Adams, A.")
    ShowEntry.create(auto_num=10, exh_no=1, class_code="SC01")
    CalculatedEntry.create(auto_num=55, source_entry_auto_num=10, exh_no=1, class_code="SC01")
    rows = get_participant_entries(1)
    assert rows[0].auto_num == 55
    assert rows[0].status == "Benched #55"


def test_get_participant_entries_late_entry_not_benched(test_db):
    from services.show_participants_service import get_participant_entries
    Exhibitor.create(exh_no=1, name="Adams, A.")
    LateEntry.create(auto_num=1, exh_no=1, name="Adams, A.", class_code="SC02")
    rows = get_participant_entries(1)
    assert rows[0].is_late is True
    assert rows[0].status == "LATE · Not benched"


def test_get_participant_entries_late_entry_benched(test_db):
    from services.show_participants_service import get_participant_entries
    Exhibitor.create(exh_no=1, name="Adams, A.")
    LateEntry.create(auto_num=1, exh_no=1, name="Adams, A.", class_code="SC02")
    CalculatedEntry.create(auto_num=77, source_late_entry_auto_num=1, exh_no=1, class_code="SC02")
    rows = get_participant_entries(1)
    assert rows[0].auto_num == 77
    assert rows[0].status == "LATE · Benched #77"


def test_get_participant_entries_blocked_by_result(test_db):
    from services.show_participants_service import get_participant_entries
    Exhibitor.create(exh_no=1, name="Adams, A.")
    ShowEntry.create(auto_num=10, exh_no=1, class_code="SC01")
    CalculatedEntry.create(auto_num=55, source_entry_auto_num=10, exh_no=1, class_code="SC01")
    Result.create(exhibit_no=55, result="1st")
    rows = get_participant_entries(1)
    assert rows[0].blocked_reason == "Has result"
    assert rows[0].status == "Has result"


def test_get_participant_entries_includes_class_description(test_db):
    from services.show_participants_service import get_participant_entries
    Exhibitor.create(exh_no=1, name="Adams, A.")
    ShowEntry.create(auto_num=10, exh_no=1, class_code="SC01")
    ClassGlossary.create(class_code="SC01", description="Open Cock")
    rows = get_participant_entries(1)
    assert rows[0].class_desc == "Open Cock"


# ── Task 2: unenrolled + enrol ────────────────────────────────────────────────

def test_get_unenrolled_exhibitors_returns_only_null_exh_no(test_db):
    from services.show_participants_service import get_unenrolled_exhibitors
    _seed(test_db)
    results = get_unenrolled_exhibitors()
    assert all(e.exh_no is None for e in results)
    assert any(e.name == "Cupido, C." for e in results)


def test_get_unenrolled_exhibitors_filters_by_name(test_db):
    from services.show_participants_service import get_unenrolled_exhibitors
    _seed(test_db)
    results = get_unenrolled_exhibitors("Cupido")
    assert len(results) == 1
    assert results[0].name == "Cupido, C."


def test_get_unenrolled_exhibitors_empty_when_all_enrolled(test_db):
    from services.show_participants_service import get_unenrolled_exhibitors
    Exhibitor.create(exh_no=1, name="Only One")
    assert get_unenrolled_exhibitors() == []


def test_enrol_exhibitors_assigns_sequential_exh_nos_alphabetically(test_db):
    from services.show_participants_service import enrol_exhibitors
    z = Exhibitor.create(exh_no=None, name="Zulu, Z.")
    a = Exhibitor.create(exh_no=None, name="Adams, A.")
    m = Exhibitor.create(exh_no=None, name="Meyer, M.")
    count = enrol_exhibitors([z.id, a.id, m.id])
    assert count == 3
    assert Exhibitor.get_by_id(a.id).exh_no == 1
    assert Exhibitor.get_by_id(m.id).exh_no == 2
    assert Exhibitor.get_by_id(z.id).exh_no == 3


def test_enrol_exhibitors_starts_after_existing_exh_nos(test_db):
    from services.show_participants_service import enrol_exhibitors
    Exhibitor.create(exh_no=5, name="Existing")
    new = Exhibitor.create(exh_no=None, name="New Person")
    enrol_exhibitors([new.id])
    assert Exhibitor.get_by_id(new.id).exh_no == 6


def test_enrol_exhibitors_empty_list_returns_zero(test_db):
    from services.show_participants_service import enrol_exhibitors
    assert enrol_exhibitors([]) == 0


def test_get_unenrolled_exhibitors_flagged_only_excludes_unflagged(test_db):
    from services.show_participants_service import get_unenrolled_exhibitors
    Exhibitor.create(exh_no=None, name="Flagged", is_entrant=True)
    Exhibitor.create(exh_no=None, name="Unflagged", is_entrant=False)
    results = get_unenrolled_exhibitors(flagged_only=True)
    assert len(results) == 1
    assert results[0].name == "Flagged"


def test_get_unenrolled_exhibitors_flagged_only_false_returns_all(test_db):
    from services.show_participants_service import get_unenrolled_exhibitors
    Exhibitor.create(exh_no=None, name="Flagged", is_entrant=True)
    Exhibitor.create(exh_no=None, name="Unflagged", is_entrant=False)
    results = get_unenrolled_exhibitors(flagged_only=False)
    assert len(results) == 2
