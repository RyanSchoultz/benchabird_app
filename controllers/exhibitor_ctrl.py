# controllers/exhibitor_ctrl.py
from repository.exhibitor_repo import ExhibitorRepo

_repo = ExhibitorRepo()


def get_all() -> list:
    return _repo.get_all()


def search(query: str) -> list:
    return _repo.search(query) if query.strip() else _repo.get_all()


def save(pk, data: dict):
    if pk:
        e = _repo.get_by_id(pk)
        return _repo.update(e, **data)
    return _repo.create(**data)


def delete(pk: int) -> None:
    e = _repo.get_by_id(pk)
    if e:
        _repo.delete(e)
