# tests/test_repository.py
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry
from repository.exhibitor_repo import ExhibitorRepo
from repository.entry_repo import EntryRepo

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

def test_entry_bulk_insert(test_db):
    repo = EntryRepo()
    rows = [{"auto_num": i, "exh_no": 1, "class_code": f"SC{i:02d}"} for i in range(1, 6)]
    repo.bulk_insert(rows)
    assert repo.count() == 5

def test_entry_by_exhibitor(test_db):
    repo = EntryRepo()
    repo.bulk_insert([
        {"auto_num": 1, "exh_no": 10, "class_code": "SC01"},
        {"auto_num": 2, "exh_no": 10, "class_code": "SC02"},
        {"auto_num": 3, "exh_no": 99, "class_code": "SC03"},
    ])
    assert len(repo.by_exhibitor(10)) == 2
