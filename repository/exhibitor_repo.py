# repository/exhibitor_repo.py
from models.exhibitor import Exhibitor

class ExhibitorRepo:
    def get_all(self) -> list:
        return list(Exhibitor.select().order_by(Exhibitor.name))

    def get_by_id(self, pk: int):
        return Exhibitor.get_or_none(Exhibitor.id == pk)

    def get_by_exh_no(self, exh_no: int):
        return Exhibitor.get_or_none(Exhibitor.exh_no == exh_no)

    def search(self, query: str) -> list:
        q = query.lower()
        return list(
            Exhibitor.select()
            .where(Exhibitor.name.contains(q) | Exhibitor.email.contains(q))
            .order_by(Exhibitor.name)
        )

    def create(self, **data) -> Exhibitor:
        return Exhibitor.create(**data)

    def update(self, exhibitor, **data) -> Exhibitor:
        for k, v in data.items():
            setattr(exhibitor, k, v)
        exhibitor.save()
        return exhibitor

    def delete(self, exhibitor) -> None:
        exhibitor.delete_instance()

    def bulk_insert(self, rows: list) -> None:
        with Exhibitor._meta.database.atomic():
            for batch in _chunks(rows, 100):
                Exhibitor.insert_many(batch).on_conflict_ignore().execute()

    def count(self) -> int:
        return Exhibitor.select().count()


def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
