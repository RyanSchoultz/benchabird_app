# tests/test_repository.py
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry
from models.class_def import ClassDef
from models.results import NotBenched
from repository.exhibitor_repo import ExhibitorRepo
from repository.entry_repo import EntryRepo
from repository.class_repo import ClassRepo
from repository.results_repo import ResultsRepo

def test_exhibitor_crud(test_db):
    repo = ExhibitorRepo()
    e = repo.create(name="Jones, M.", exh_no=5, town="Durban")
    assert repo.count() == 1
    assert repo.get_by_exh_no(5).name == "Jones, M."
    repo.update(e, town="Pretoria")
    assert repo.get_by_exh_no(5).town == "Pretoria"
    repo.delete(e)
    assert repo.count() == 0

def test_exhibitor_search(test_db):
    repo = ExhibitorRepo()
    repo.create(name="Adams, A.", exh_no=1)
    repo.create(name="Baker, B.", exh_no=2)
    results = repo.search("adams")
    assert len(results) == 1
    assert results[0].name == "Adams, A."

def test_entry_replace_all(test_db):
    repo = EntryRepo()
    rows = [{"auto_num": i, "exh_no": 1, "class_code": f"SC{i:02d}"} for i in range(1, 6)]
    repo.replace_all(rows)
    assert repo.count() == 5

def test_entry_replace_all_is_idempotent(test_db):
    repo = EntryRepo()
    first = [{"auto_num": 1, "exh_no": 1, "class_code": "SC01"}]
    second = [{"auto_num": i, "exh_no": 2, "class_code": f"SC{i:02d}"} for i in range(1, 4)]
    repo.replace_all(first)
    repo.replace_all(second)
    assert repo.count() == 3

def test_entry_by_exhibitor(test_db):
    repo = EntryRepo()
    repo.replace_all([
        {"auto_num": 1, "exh_no": 10, "class_code": "SC01"},
        {"auto_num": 2, "exh_no": 10, "class_code": "SC02"},
        {"auto_num": 3, "exh_no": 99, "class_code": "SC03"},
    ])
    assert len(repo.by_exhibitor(10)) == 2

def test_class_get_by_code(test_db):
    ClassDef.create(class_code="SC01", bird_type="Softbill", class_seq=1)
    repo = ClassRepo()
    result = repo.get_by_code("SC01")
    assert result is not None
    assert result.bird_type == "Softbill"
    assert repo.get_by_code("NOPE") is None

def test_class_count_and_all_codes(test_db):
    ClassDef.create(class_code="A01", bird_type="Finch", class_seq=1)
    ClassDef.create(class_code="B02", bird_type="Finch", class_seq=2)
    repo = ClassRepo()
    assert repo.count() == 2
    codes = repo.all_codes()
    assert "A01" in codes and "B02" in codes

def test_results_set_and_clear(test_db):
    repo = ResultsRepo()
    repo.set_result(exhibit_no=42, result="1st")
    assert repo.get_result(42).result == "1st"
    cleared = repo.clear_results()
    assert cleared == 1
    assert repo.get_result(42).result is None

def test_results_not_benched(test_db):
    repo = ResultsRepo()
    repo.mark_not_benched(7)
    assert NotBenched.get_or_none(NotBenched.exhibit_no == 7) is not None
    repo.unmark_not_benched(7)
    assert NotBenched.get_or_none(NotBenched.exhibit_no == 7) is None
