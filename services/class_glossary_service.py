from __future__ import annotations

from dataclasses import dataclass

from models.class_def import ClassDef, Species
from models.class_glossary import ClassGlossary


@dataclass(frozen=True)
class ClassGlossaryRow:
    class_code: str
    bird_type: str
    species_heading: str
    species_subheading: str
    main_class: str
    description: str
    extra: str
    class_seq: int


def class_description(colour: str | None, afrbesk: str | None) -> str:
    return " ".join(part.strip() for part in [colour or "", afrbesk or ""] if part and part.strip())


def _search_text(parts: list[str | None]) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip()).lower()


def _species_map() -> dict[str, Species]:
    return {row.bird_type or "": row for row in Species.select() if row.bird_type}


def seed_class_glossary() -> int:
    species_by_type = _species_map()
    data = []
    for item in ClassDef.select().order_by(
        ClassDef.bird_type,
        ClassDef.main_class,
        ClassDef.class_seq,
        ClassDef.class_code,
    ):
        species = species_by_type.get(item.bird_type or "")
        heading = (species.type2 if species else None) or item.bird_type or ""
        subheading = (species.type3 if species else None) or item.bird_type or ""
        description = class_description(item.colour, item.afrbesk)
        data.append(
            {
                "class_code": item.class_code or "",
                "bird_type": item.bird_type or "",
                "species_seq": (species.seq if species else None) or 999999,
                "species_heading": heading,
                "species_subheading": subheading,
                "main_class": item.main_class or "",
                "description": description,
                "extra": item.type_b or "",
                "class_seq": item.class_seq or 999999,
                "search_text": _search_text(
                    [
                        item.class_code,
                        item.bird_type,
                        heading,
                        subheading,
                        item.main_class,
                        description,
                        item.type_b,
                    ]
                ),
            }
        )

    db = ClassGlossary._meta.database
    with db.atomic():
        ClassGlossary.delete().execute()
        for i in range(0, len(data), 200):
            ClassGlossary.insert_many(data[i : i + 200]).execute()
    return len(data)


def _ensure_seeded():
    if ClassGlossary.select().count() == 0 and ClassDef.select().count() > 0:
        seed_class_glossary()


def list_species_filters() -> list[str]:
    _ensure_seeded()
    rows = (
        ClassGlossary.select(ClassGlossary.species_heading)
        .where(ClassGlossary.species_heading.is_null(False))
        .group_by(ClassGlossary.species_heading)
        .order_by(ClassGlossary.species_seq, ClassGlossary.species_heading)
    )
    return [row.species_heading for row in rows if row.species_heading]


def list_class_glossary(query: str = "", species_heading: str = "") -> list[ClassGlossaryRow]:
    _ensure_seeded()
    q = (query or "").strip().lower()
    select = ClassGlossary.select()
    if species_heading:
        select = select.where(ClassGlossary.species_heading == species_heading)
    if q:
        select = select.where(ClassGlossary.search_text.contains(q))
    select = select.order_by(
        ClassGlossary.species_seq,
        ClassGlossary.species_heading,
        ClassGlossary.main_class,
        ClassGlossary.class_seq,
        ClassGlossary.class_code,
    )
    return [
        ClassGlossaryRow(
            class_code=row.class_code or "",
            bird_type=row.bird_type or "",
            species_heading=row.species_heading or "",
            species_subheading=row.species_subheading or "",
            main_class=row.main_class or "",
            description=row.description or "",
            extra=row.extra or "",
            class_seq=row.class_seq or 999999,
        )
        for row in select
    ]
