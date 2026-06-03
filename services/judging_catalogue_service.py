from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.class_def import ClassDef
from models.show_entry import CalculatedEntry
from services.not_benched_service import (
    get_not_benched_set,
    mark_not_benched,
    unmark_not_benched,
)
from services.results_service import record_result

RESULT_OPTIONS = [
    "1st",
    "2nd",
    "3rd",
    "4th",
    "5th",
    "BOB",
    "R/U BOB",
    "Champion",
    "Reserve",
]
CLEAR_OPTION = "Clear"
NB_OPTION = "NB"


class JudgingCatalogueError(Exception):
    pass


@dataclass(frozen=True)
class JudgingCategory:
    key: str
    label: str
    seq: int
    entry_count: int


@dataclass(frozen=True)
class JudgingClassOption:
    class_code: str
    category: str
    category_seq: int
    main_class: str
    main_class_seq: int
    class_seq: int
    type_b: str
    colour: str

    @property
    def label(self) -> str:
        bits = [self.class_code]
        if self.colour:
            bits.append(self.colour)
        if self.category:
            bits.append(self.category)
        return " - ".join(bits)


@dataclass(frozen=True)
class JudgingEntry:
    auto_num: int
    exh_no: int | None
    name: str | None
    class_code: str | None
    category: str
    category_seq: int
    main_class: str
    main_class_seq: int
    class_seq: int
    type_b: str
    colour: str
    current_result: str | None
    not_benched: bool


def _rows() -> list[JudgingEntry]:
    db = CalculatedEntry._meta.database
    sql = """
        SELECT ce.auto_num, ce.exh_no, ce.name, ce.class_code,
               COALESCE(cd.bird_type, '(Unclassified)') AS category,
               COALESCE(sp.seq, 999999) AS category_seq,
               COALESCE(cd.main_class, '(Unknown)') AS main_class,
               COALESCE(mc.mc_seq, 999999) AS main_class_seq,
               COALESCE(cd.class_seq, 999999) AS class_seq,
               COALESCE(cd.type_b, '') AS type_b,
               COALESCE(cd.colour, '') AS colour,
               r.result
        FROM calculated_entry ce
        LEFT JOIN class_def cd ON ce.class_code = cd.class_code
        LEFT JOIN species sp ON cd.bird_type = sp.bird_type
        LEFT JOIN main_class mc ON cd.main_class = mc.main_class
        LEFT JOIN result r ON ce.auto_num = r.exhibit_no
        ORDER BY category_seq, category, main_class_seq, main_class,
                 class_seq, ce.class_code, ce.auto_num
    """
    nb_set = get_not_benched_set()
    return [
        JudgingEntry(
            auto_num=row[0],
            exh_no=row[1],
            name=row[2],
            class_code=row[3],
            category=row[4],
            category_seq=int(row[5] or 999999),
            main_class=row[6],
            main_class_seq=int(row[7] or 999999),
            class_seq=int(row[8] or 999999),
            type_b=row[9],
            colour=row[10],
            current_result=row[11],
            not_benched=row[0] in nb_set,
        )
        for row in db.execute_sql(sql).fetchall()
    ]


def list_class_options() -> list[JudgingClassOption]:
    db = ClassDef._meta.database
    sql = """
        SELECT cd.class_code,
               COALESCE(cd.bird_type, '(Unclassified)') AS category,
               COALESCE(sp.seq, 999999) AS category_seq,
               COALESCE(cd.main_class, '(Unknown)') AS main_class,
               COALESCE(mc.mc_seq, 999999) AS main_class_seq,
               COALESCE(cd.class_seq, 999999) AS class_seq,
               COALESCE(cd.type_b, '') AS type_b,
               COALESCE(cd.colour, '') AS colour
        FROM class_def cd
        LEFT JOIN species sp ON cd.bird_type = sp.bird_type
        LEFT JOIN main_class mc ON cd.main_class = mc.main_class
        WHERE cd.class_code IS NOT NULL AND TRIM(cd.class_code) <> ''
        ORDER BY category_seq, category, main_class_seq, main_class, class_seq, cd.class_code
    """
    return [
        JudgingClassOption(
            class_code=row[0],
            category=row[1],
            category_seq=int(row[2] or 999999),
            main_class=row[3],
            main_class_seq=int(row[4] or 999999),
            class_seq=int(row[5] or 999999),
            type_b=row[6],
            colour=row[7],
        )
        for row in db.execute_sql(sql).fetchall()
    ]


def list_judging_categories() -> list[JudgingCategory]:
    grouped: dict[str, JudgingCategory] = {}
    for row in _rows():
        existing = grouped.get(row.category)
        if existing is None:
            grouped[row.category] = JudgingCategory(
                key=row.category,
                label=row.category,
                seq=row.category_seq,
                entry_count=1,
            )
        else:
            grouped[row.category] = JudgingCategory(
                key=existing.key,
                label=existing.label,
                seq=existing.seq,
                entry_count=existing.entry_count + 1,
            )
    return sorted(grouped.values(), key=lambda category: (category.seq, category.label))


def get_judging_entries(category_key: str | None = None) -> list[JudgingEntry]:
    rows = _rows()
    if category_key:
        rows = [row for row in rows if row.category == category_key]
    return rows


def _normalise_selection(value: Any) -> tuple[str, str | None]:
    if isinstance(value, dict):
        result_value = (value.get("result") or "").strip()
        class_code = (value.get("class_code") or "").strip() or None
    else:
        result_value = (value or "").strip()
        class_code = None
    return result_value, class_code


def save_category_results(selections: dict[int, Any]) -> int:
    saved = 0
    valid = set(RESULT_OPTIONS + [NB_OPTION, CLEAR_OPTION])
    db = CalculatedEntry._meta.database

    with db.atomic():
        for auto_num, raw_value in selections.items():
            result_value, class_code = _normalise_selection(raw_value)
            if result_value and result_value not in valid:
                continue

            entry = CalculatedEntry.get_or_none(CalculatedEntry.auto_num == auto_num)
            if entry is None:
                continue

            changed = False
            if class_code and class_code != entry.class_code:
                exists = ClassDef.get_or_none(ClassDef.class_code == class_code)
                if exists is None:
                    raise JudgingCatalogueError(f"Select a valid class for exhibit #{auto_num}.")
                entry.class_code = class_code
                entry.save(only=[CalculatedEntry.class_code])
                changed = True

            if result_value:
                if result_value == NB_OPTION:
                    mark_not_benched(auto_num)
                    record_result(auto_num, None)
                elif result_value == CLEAR_OPTION:
                    unmark_not_benched(auto_num)
                    record_result(auto_num, None)
                else:
                    unmark_not_benched(auto_num)
                    record_result(auto_num, result_value)
                changed = True

            if changed:
                saved += 1
    return saved
