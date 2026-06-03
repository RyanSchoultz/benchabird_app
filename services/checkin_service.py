from __future__ import annotations

from dataclasses import dataclass, field

from peewee import fn

from models.class_def import ClassDef
from models.exhibitor import Exhibitor
from models.results import NotBenched, Result
from models.show_entry import CalculatedEntry, LateEntry, ShowEntry
from models.special import SpecialWinner


@dataclass(frozen=True)
class CheckinExhibitorMatch:
    exh_no: int | None
    name: str
    email: str | None
    town: str | None
    club: str | None
    entry_count: int
    benched_count: int


@dataclass(frozen=True)
class CheckinEntryRow:
    source_entry_auto_num: int
    exh_no: int | None
    class_code: str | None
    colour: str
    category: str
    auto_num: int | None
    status: str
    blocked_reason: str | None = None


@dataclass(frozen=True)
class BenchResult:
    created: list[int] = field(default_factory=list)
    skipped: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class UnbenchResult:
    removed: list[int] = field(default_factory=list)
    blocked: dict[int, str] = field(default_factory=dict)
    missing: list[int] = field(default_factory=list)


def _is_int(value: str) -> bool:
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        return False


def _counts_for(exh_no: int | None) -> tuple[int, int]:
    if exh_no is None:
        return 0, 0
    entries = ShowEntry.select().where(ShowEntry.exh_no == exh_no).count()
    benched = CalculatedEntry.select().where(CalculatedEntry.exh_no == exh_no).count()
    return entries, benched


def _match_from_exhibitor(exhibitor: Exhibitor) -> CheckinExhibitorMatch:
    entry_count, benched_count = _counts_for(exhibitor.exh_no)
    return CheckinExhibitorMatch(
        exh_no=exhibitor.exh_no,
        name=exhibitor.name,
        email=exhibitor.email,
        town=exhibitor.town,
        club=exhibitor.club,
        entry_count=entry_count,
        benched_count=benched_count,
    )


def search_checkin_exhibitors(query: str, limit: int = 25) -> list[CheckinExhibitorMatch]:
    q = (query or "").strip()
    if not q:
        rows = Exhibitor.select().order_by(Exhibitor.name).limit(limit)
        return [_match_from_exhibitor(row) for row in rows]

    matched_exh_nos: set[int] = set()
    text_filter = (
        (Exhibitor.name.contains(q))
        | (Exhibitor.email.contains(q))
        | (Exhibitor.club.contains(q))
    )
    if _is_int(q):
        text_filter = text_filter | (Exhibitor.exh_no == int(q))

    for exhibitor in Exhibitor.select().where(text_filter):
        if exhibitor.exh_no is not None:
            matched_exh_nos.add(exhibitor.exh_no)

    for entry in ShowEntry.select().where(ShowEntry.class_code.contains(q)):
        if entry.exh_no is not None:
            matched_exh_nos.add(entry.exh_no)

    calc_filter = CalculatedEntry.class_code.contains(q)
    if _is_int(q):
        calc_filter = calc_filter | (CalculatedEntry.auto_num == int(q))
    for entry in CalculatedEntry.select().where(calc_filter):
        if entry.exh_no is not None:
            matched_exh_nos.add(entry.exh_no)

    if not matched_exh_nos:
        return []

    rows = (
        Exhibitor.select()
        .where(Exhibitor.exh_no.in_(matched_exh_nos))
        .order_by(Exhibitor.name)
        .limit(limit)
    )
    return [_match_from_exhibitor(row) for row in rows]


def _calculated_by_source(exh_no: int | None) -> dict[int, CalculatedEntry]:
    if exh_no is None:
        return {}
    rows = (
        CalculatedEntry.select()
        .where(
            (CalculatedEntry.exh_no == exh_no)
            & CalculatedEntry.source_entry_auto_num.is_null(False)
        )
    )
    return {row.source_entry_auto_num: row for row in rows}


def _legacy_calculated_by_class(exh_no: int | None) -> dict[str, list[CalculatedEntry]]:
    if exh_no is None:
        return {}
    rows = (
        CalculatedEntry.select()
        .where(
            (CalculatedEntry.exh_no == exh_no)
            & CalculatedEntry.source_entry_auto_num.is_null(True)
        )
        .order_by(CalculatedEntry.auto_num)
    )
    grouped: dict[str, list[CalculatedEntry]] = {}
    for row in rows:
        grouped.setdefault(row.class_code or "", []).append(row)
    return grouped


def _blocked_reason(auto_num: int | None) -> str | None:
    if auto_num is None:
        return None
    result = Result.get_or_none((Result.exhibit_no == auto_num) & Result.result.is_null(False))
    if result is not None:
        return "Has result"
    nb = NotBenched.get_or_none(NotBenched.exhibit_no == auto_num)
    if nb is not None:
        return "Marked NB"
    winner = SpecialWinner.get_or_none(SpecialWinner.exhibit_no == auto_num)
    if winner is not None:
        return "Special winner"
    return None


def get_checkin_entries(exh_no: int) -> list[CheckinEntryRow]:
    calculated = _calculated_by_source(exh_no)
    legacy_by_class = _legacy_calculated_by_class(exh_no)
    class_map = {
        row.class_code: row
        for row in ClassDef.select()
        if row.class_code
    }
    rows = ShowEntry.select().where(ShowEntry.exh_no == exh_no).order_by(ShowEntry.auto_num)
    result: list[CheckinEntryRow] = []
    for entry in rows:
        calc = calculated.get(entry.auto_num)
        legacy = None
        if calc is None:
            legacy_rows = legacy_by_class.get(entry.class_code or "", [])
            if legacy_rows:
                legacy = legacy_rows.pop(0)
        auto_num = calc.auto_num if calc is not None else None
        if legacy is not None:
            auto_num = legacy.auto_num
        blocked = "Legacy allocation" if legacy is not None else _blocked_reason(auto_num)
        if auto_num is None:
            status = "Not benched"
        elif legacy is not None:
            status = f"Legacy allocation #{auto_num}"
        elif blocked:
            status = blocked
        else:
            status = f"Benched #{auto_num}"
        class_def = class_map.get(entry.class_code)
        result.append(
            CheckinEntryRow(
                source_entry_auto_num=entry.auto_num,
                exh_no=entry.exh_no,
                class_code=entry.class_code,
                colour=(class_def.colour if class_def else "") or "",
                category=(class_def.bird_type if class_def else "") or "",
                auto_num=auto_num,
                status=status,
                blocked_reason=blocked,
            )
        )
    return result


def bench_entries(source_entry_auto_nums: list[int]) -> BenchResult:
    if not source_entry_auto_nums:
        return BenchResult()

    db = CalculatedEntry._meta.database
    created: list[int] = []
    skipped: list[int] = []
    with db.atomic():
        max_auto_num = CalculatedEntry.select(fn.MAX(CalculatedEntry.auto_num)).scalar() or 0
        pending: list[ShowEntry] = []
        for source_auto_num in source_entry_auto_nums:
            existing = CalculatedEntry.get_or_none(
                CalculatedEntry.source_entry_auto_num == source_auto_num
            )
            if existing is not None:
                skipped.append(source_auto_num)
                continue
            entry = ShowEntry.get_or_none(ShowEntry.auto_num == source_auto_num)
            if entry is None:
                skipped.append(source_auto_num)
                continue
            pending.append(entry)

        class_order = {
            row.class_code: row.class_seq if row.class_seq is not None else 999999
            for row in ClassDef.select()
            if row.class_code
        }
        pending.sort(
            key=lambda entry: (
                class_order.get(entry.class_code, 999999),
                entry.auto_num or 999999,
            )
        )

        for entry in pending:
            exhibitor = Exhibitor.get_or_none(Exhibitor.exh_no == entry.exh_no)
            max_auto_num += 1
            CalculatedEntry.create(
                auto_num=max_auto_num,
                source_entry_auto_num=entry.auto_num,
                exh_no=entry.exh_no,
                name=exhibitor.name if exhibitor else None,
                class_code=entry.class_code,
            )
            created.append(max_auto_num)
    return BenchResult(created=created, skipped=skipped)


def unbench_entries(source_entry_auto_nums: list[int]) -> UnbenchResult:
    removed: list[int] = []
    blocked: dict[int, str] = {}
    missing: list[int] = []
    db = CalculatedEntry._meta.database
    with db.atomic():
        for source_auto_num in source_entry_auto_nums:
            calc = CalculatedEntry.get_or_none(
                CalculatedEntry.source_entry_auto_num == source_auto_num
            )
            if calc is None:
                missing.append(source_auto_num)
                continue
            reason = _blocked_reason(calc.auto_num)
            if reason:
                blocked[source_auto_num] = reason
                continue
            auto_num = calc.auto_num
            calc.delete_instance()
            removed.append(auto_num)
    return UnbenchResult(removed=removed, blocked=blocked, missing=missing)


def bench_late_entries(late_entry_auto_nums: list[int]) -> BenchResult:
    if not late_entry_auto_nums:
        return BenchResult()
    db = CalculatedEntry._meta.database
    created: list[int] = []
    skipped: list[int] = []
    with db.atomic():
        max_auto_num = CalculatedEntry.select(fn.MAX(CalculatedEntry.auto_num)).scalar() or 0
        for source_auto_num in late_entry_auto_nums:
            existing = CalculatedEntry.get_or_none(
                CalculatedEntry.source_late_entry_auto_num == source_auto_num
            )
            if existing is not None:
                skipped.append(source_auto_num)
                continue
            entry = LateEntry.get_or_none(LateEntry.auto_num == source_auto_num)
            if entry is None:
                skipped.append(source_auto_num)
                continue
            exhibitor = Exhibitor.get_or_none(Exhibitor.exh_no == entry.exh_no)
            max_auto_num += 1
            CalculatedEntry.create(
                auto_num=max_auto_num,
                source_late_entry_auto_num=entry.auto_num,
                exh_no=entry.exh_no,
                name=exhibitor.name if exhibitor else entry.name,
                class_code=entry.class_code,
            )
            created.append(max_auto_num)
    return BenchResult(created=created, skipped=skipped)


def unbench_late_entries(late_entry_auto_nums: list[int]) -> UnbenchResult:
    removed: list[int] = []
    blocked: dict[int, str] = {}
    missing: list[int] = []
    db = CalculatedEntry._meta.database
    with db.atomic():
        for source_auto_num in late_entry_auto_nums:
            calc = CalculatedEntry.get_or_none(
                CalculatedEntry.source_late_entry_auto_num == source_auto_num
            )
            if calc is None:
                missing.append(source_auto_num)
                continue
            reason = _blocked_reason(calc.auto_num)
            if reason:
                blocked[source_auto_num] = reason
                continue
            auto_num = calc.auto_num
            calc.delete_instance()
            removed.append(auto_num)
    return UnbenchResult(removed=removed, blocked=blocked, missing=missing)
