# services/show_participants_service.py
from __future__ import annotations
from dataclasses import dataclass
from peewee import fn
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, LateEntry, CalculatedEntry


@dataclass(frozen=True)
class ParticipantRow:
    exhibitor_id: int
    exh_no: int | None
    name: str
    email: str | None
    entry_count: int
    benched_count: int
    late_count: int


@dataclass(frozen=True)
class ParticipantEntryRow:
    source_auto_num: int
    is_late: bool
    class_code: str | None
    class_desc: str | None
    auto_num: int | None
    status: str
    blocked_reason: str | None


def get_participants(filter: str = "all") -> list[ParticipantRow]:
    db = Exhibitor._meta.database
    cursor = db.execute_sql("""
        SELECT
            e.id,
            e.exh_no,
            e.name,
            e.email,
            (SELECT COUNT(*) FROM show_entry WHERE exh_no = e.exh_no) +
            (SELECT COUNT(*) FROM late_entry  WHERE exh_no = e.exh_no) AS entry_count,
            (SELECT COUNT(*) FROM calculated_entry
                WHERE source_entry_auto_num IN
                    (SELECT auto_num FROM show_entry WHERE exh_no = e.exh_no)) +
            (SELECT COUNT(*) FROM calculated_entry
                WHERE source_late_entry_auto_num IN
                    (SELECT auto_num FROM late_entry WHERE exh_no = e.exh_no)) AS benched_count,
            (SELECT COUNT(*) FROM late_entry WHERE exh_no = e.exh_no) AS late_count
        FROM exhibitor e
        WHERE e.exh_no IS NOT NULL
        ORDER BY e.exh_no
    """)
    rows = [
        ParticipantRow(
            exhibitor_id=r[0], exh_no=r[1], name=r[2] or "",
            email=r[3], entry_count=r[4], benched_count=r[5], late_count=r[6],
        )
        for r in cursor.fetchall()
    ]
    if filter == "unbenched":
        return [r for r in rows if r.entry_count > r.benched_count]
    if filter == "late":
        return [r for r in rows if r.late_count > 0]
    return rows


def search_registry(query: str) -> list[Exhibitor]:
    """Search the full Exhibitor master registry (all members, not just current show)."""
    q = (query or "").strip()
    if not q:
        return []
    return list(
        Exhibitor.select().where(
            Exhibitor.name.contains(q) | Exhibitor.email.contains(q)
        ).order_by(Exhibitor.name).limit(20)
    )


def get_orphaned_exh_nos() -> list[int]:
    """ExhNos in ShowEntry that have no matching Exhibitor record."""
    db = ShowEntry._meta.database
    cursor = db.execute_sql("""
        SELECT DISTINCT se.exh_no
        FROM show_entry se
        LEFT JOIN exhibitor e ON se.exh_no = e.exh_no
        WHERE e.id IS NULL AND se.exh_no IS NOT NULL
    """)
    return [row[0] for row in cursor.fetchall()]


def next_available_exh_no() -> int:
    max_no = Exhibitor.select(fn.MAX(Exhibitor.exh_no)).scalar() or 0
    return max_no + 1


def assign_exh_no(exhibitor_id: int, exh_no: int) -> None:
    if Exhibitor.select().where(
        (Exhibitor.exh_no == exh_no) & (Exhibitor.id != exhibitor_id)
    ).exists():
        raise ValueError(f"ExhNo {exh_no} is already assigned to another exhibitor.")
    exhibitor = Exhibitor.get_by_id(exhibitor_id)
    exhibitor.exh_no = exh_no
    exhibitor.save()


def get_unenrolled_exhibitors(query: str = "", flagged_only: bool = False) -> list[Exhibitor]:
    """All exhibitors with no ExhNo assigned, optionally filtered by name or entrant flag."""
    q = (query or "").strip()
    base = Exhibitor.select().where(Exhibitor.exh_no.is_null(True))
    if flagged_only:
        base = base.where(Exhibitor.is_entrant == True)
    if q:
        base = base.where(Exhibitor.name.contains(q))
    return list(base.order_by(Exhibitor.name))


def enrol_exhibitors(exhibitor_ids: list[int]) -> int:
    """
    Assign sequential ExhNos to the given exhibitors in alphabetical name order.
    Starts from next_available_exh_no(). Returns count enrolled.
    """
    if not exhibitor_ids:
        return 0
    exhibitors = list(
        Exhibitor.select()
        .where(Exhibitor.id.in_(exhibitor_ids))
        .order_by(Exhibitor.name)
    )
    start = next_available_exh_no()
    db = Exhibitor._meta.database
    with db.atomic():
        for i, exhibitor in enumerate(exhibitors):
            exhibitor.exh_no = start + i
            exhibitor.save()
    return len(exhibitors)


def get_participant_entries(exh_no: int) -> list[ParticipantEntryRow]:
    from models.class_glossary import ClassGlossary
    from services.checkin_service import _blocked_reason

    class_desc_map = {
        g.class_code: g.description
        for g in ClassGlossary.select()
        if g.class_code
    }

    calc_by_source = {
        ce.source_entry_auto_num: ce
        for ce in CalculatedEntry.select().where(
            (CalculatedEntry.exh_no == exh_no)
            & CalculatedEntry.source_entry_auto_num.is_null(False)
        )
    }
    calc_by_late = {
        ce.source_late_entry_auto_num: ce
        for ce in CalculatedEntry.select().where(
            (CalculatedEntry.exh_no == exh_no)
            & CalculatedEntry.source_late_entry_auto_num.is_null(False)
        )
    }

    rows: list[ParticipantEntryRow] = []

    for entry in ShowEntry.select().where(ShowEntry.exh_no == exh_no).order_by(ShowEntry.auto_num):
        ce = calc_by_source.get(entry.auto_num)
        auto_num = ce.auto_num if ce else None
        blocked = _blocked_reason(auto_num) if auto_num else None
        if auto_num is None:
            status = "Not benched"
        elif blocked:
            status = blocked
        else:
            status = f"Benched #{auto_num}"
        rows.append(ParticipantEntryRow(
            source_auto_num=entry.auto_num,
            is_late=False,
            class_code=entry.class_code,
            class_desc=class_desc_map.get(entry.class_code or "", "") or "",
            auto_num=auto_num,
            status=status,
            blocked_reason=blocked,
        ))

    for entry in LateEntry.select().where(LateEntry.exh_no == exh_no).order_by(LateEntry.auto_num):
        ce = calc_by_late.get(entry.auto_num)
        auto_num = ce.auto_num if ce else None
        blocked = _blocked_reason(auto_num) if auto_num else None
        if auto_num:
            status = f"LATE · Benched #{auto_num}"
        else:
            status = "LATE · Not benched"
        rows.append(ParticipantEntryRow(
            source_auto_num=entry.auto_num,
            is_late=True,
            class_code=entry.class_code,
            class_desc=class_desc_map.get(entry.class_code or "", "") or "",
            auto_num=auto_num,
            status=status,
            blocked_reason=blocked,
        ))

    return rows
