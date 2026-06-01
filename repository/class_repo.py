# repository/class_repo.py
from models.class_def import ClassDef, Species, MainClass

class ClassRepo:
    def get_by_code(self, code: str):
        return ClassDef.get_or_none(ClassDef.class_code == code)

    def all_codes(self) -> list:
        return [r.class_code for r in ClassDef.select(ClassDef.class_code).order_by(ClassDef.class_code)]

    def by_type(self, bird_type: str) -> list:
        return list(ClassDef.select().where(ClassDef.bird_type == bird_type).order_by(ClassDef.class_seq))

    def all_species(self) -> list:
        return list(Species.select().order_by(Species.seq))

    def species_by_tcode(self, tcode: str):
        return Species.get_or_none(Species.tcode == tcode)

    def count(self) -> int:
        return ClassDef.select().count()
