# tests/test_calculate_service.py
from models.show_entry import ShowEntry, CalculatedEntry
from models.class_def import ClassDef
from models.exhibitor import Exhibitor
from services.calculate_service import calculate_entries


def _seed(test_db):
    Exhibitor.create(exh_no=2, name="Smith, J.")
    Exhibitor.create(exh_no=1, name="Adams, A.")
    ClassDef.create(class_code="SC01", class_seq=10)
    ClassDef.create(class_code="SC02", class_seq=20)
    ClassDef.create(class_code="SC03", class_seq=5)
    ShowEntry.create(auto_num=10, exh_no=2, class_code="SC01")
    ShowEntry.create(auto_num=11, exh_no=2, class_code="SC02")
    ShowEntry.create(auto_num=12, exh_no=1, class_code="SC03")


def test_calculate_returns_correct_count(test_db):
    _seed(test_db)
    count = calculate_entries()
    assert count == 3


def test_calculate_assigns_sequential_autonums(test_db):
    _seed(test_db)
    calculate_entries()
    rows = list(CalculatedEntry.select().order_by(CalculatedEntry.auto_num))
    assert [r.auto_num for r in rows] == [1, 2, 3]


def test_calculate_sorted_by_exhno_then_classseq(test_db):
    _seed(test_db)
    calculate_entries()
    rows = list(CalculatedEntry.select().order_by(CalculatedEntry.auto_num))
    # exh_no 1 (Adams) + SC03 (seq=5) comes first
    assert rows[0].exh_no == 1
    assert rows[0].class_code == "SC03"
    # exh_no 2 (Smith): SC01 (seq=10) then SC02 (seq=20)
    assert rows[1].exh_no == 2 and rows[1].class_code == "SC01"
    assert rows[2].exh_no == 2 and rows[2].class_code == "SC02"


def test_calculate_populates_name(test_db):
    _seed(test_db)
    calculate_entries()
    rows = list(CalculatedEntry.select().order_by(CalculatedEntry.auto_num))
    assert rows[0].name == "Adams, A."


def test_calculate_is_idempotent(test_db):
    _seed(test_db)
    calculate_entries()
    calculate_entries()
    assert CalculatedEntry.select().count() == 3
