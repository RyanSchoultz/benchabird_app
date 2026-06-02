"""Generate one-exhibitor document bundles."""

from __future__ import annotations

from dataclasses import dataclass

from models.exhibitor import Exhibitor
from models.results import NotBenched, Result
from models.show_entry import CalculatedEntry, LateEntry, ShowEntry
from services.reports.base import (
    MARGIN,
    PAGE_W,
    ROW_H,
    draw_footer,
    draw_page_header,
    new_canvas,
)
from services.ticket_service import get_ticket_assignments


class ExhibitorBundleError(ValueError):
    pass


@dataclass(frozen=True)
class BundleEntry:
    ticket_no: int | None
    auto_num: int | None
    class_code: str | None
    source: str
    result: str | None = None
    not_benched: bool = False


@dataclass(frozen=True)
class BundleExhibitorMatch:
    exhibitor: Exhibitor
    matching_exhibit_no: int | None
    entry_count: int


def _exhibitor_or_error(exh_no: int) -> Exhibitor:
    exhibitor = Exhibitor.get_or_none(Exhibitor.exh_no == exh_no)
    if exhibitor is None:
        raise ExhibitorBundleError(f"No exhibitor found for #{exh_no}.")
    return exhibitor


def _exhibitor_id_or_error(exhibitor_id: int) -> Exhibitor:
    exhibitor = Exhibitor.get_or_none(Exhibitor.id == exhibitor_id)
    if exhibitor is None:
        raise ExhibitorBundleError(f"No exhibitor found for row #{exhibitor_id}.")
    return exhibitor


def _name_matches(entry_name: str | None, exhibitor: Exhibitor) -> bool:
    if not entry_name or not exhibitor.name:
        return False
    return entry_name.strip().lower() == exhibitor.name.strip().lower()


def _calculated_entries_for(exhibitor: Exhibitor) -> list[CalculatedEntry]:
    rows = list(CalculatedEntry.select().order_by(CalculatedEntry.auto_num))
    return [
        entry
        for entry in rows
        if (
            exhibitor.exh_no is not None
            and entry.exh_no == exhibitor.exh_no
        )
        or _name_matches(entry.name, exhibitor)
    ]


def _show_entries_for(exhibitor: Exhibitor) -> list[ShowEntry]:
    if exhibitor.exh_no is None:
        return []
    return list(
        ShowEntry.select()
        .where(ShowEntry.exh_no == exhibitor.exh_no)
        .order_by(ShowEntry.auto_num)
    )


def _late_entries_for(exhibitor: Exhibitor) -> list[LateEntry]:
    rows = list(LateEntry.select().order_by(LateEntry.auto_num))
    return [
        entry
        for entry in rows
        if (
            exhibitor.exh_no is not None
            and entry.exh_no == exhibitor.exh_no
        )
        or _name_matches(entry.name, exhibitor)
    ]


def _regular_entries(exhibitor: Exhibitor) -> list[BundleEntry]:
    ticket_by_auto = {
        row["auto_num"]: row["ticket_no"]
        for row in get_ticket_assignments()
        if (
            exhibitor.exh_no is not None
            and row["exh_no"] == exhibitor.exh_no
        )
        or _name_matches(row.get("name"), exhibitor)
    }
    calculated = _calculated_entries_for(exhibitor)
    if calculated:
        return [
            BundleEntry(
                ticket_no=ticket_by_auto.get(entry.auto_num, entry.auto_num),
                auto_num=entry.auto_num,
                class_code=entry.class_code,
                source="Calculated",
            )
            for entry in calculated
        ]
    raw = _show_entries_for(exhibitor)
    return [
        BundleEntry(
            ticket_no=None,
            auto_num=entry.auto_num,
            class_code=entry.class_code,
            source="Raw",
        )
        for entry in raw
    ]


def _late_entries(exhibitor: Exhibitor) -> list[BundleEntry]:
    return [
        BundleEntry(
            ticket_no=None,
            auto_num=entry.auto_num,
            class_code=entry.class_code,
            source="Late",
        )
        for entry in _late_entries_for(exhibitor)
    ]


def _entry_count_for(exhibitor: Exhibitor) -> int:
    return (
        len(_calculated_entries_for(exhibitor))
        or len(_show_entries_for(exhibitor))
    ) + len(_late_entries_for(exhibitor))


def _matching_exhibit_for_query(exhibitor: Exhibitor, query: str) -> int | None:
    if not query.isdigit():
        return None
    for entry in [
        *_calculated_entries_for(exhibitor),
        *_show_entries_for(exhibitor),
        *_late_entries_for(exhibitor),
    ]:
        if query in str(entry.auto_num):
            return entry.auto_num
    return None


def search_exhibitors_for_bundle(query: str = "", limit: int = 100) -> list[BundleExhibitorMatch]:
    q = query.strip().lower()
    matches: list[BundleExhibitorMatch] = []
    for exhibitor in Exhibitor.select().order_by(Exhibitor.name):
        text_match = (
            not q
            or q in str(exhibitor.exh_no or "").lower()
            or q in (exhibitor.name or "").lower()
            or q in (exhibitor.email or "").lower()
            or q in (exhibitor.club or "").lower()
        )
        matching_exhibit = _matching_exhibit_for_query(exhibitor, q) if q else None
        if text_match or matching_exhibit is not None:
            matches.append(
                BundleExhibitorMatch(
                    exhibitor=exhibitor,
                    matching_exhibit_no=matching_exhibit,
                    entry_count=_entry_count_for(exhibitor),
                )
            )
        if len(matches) >= limit:
            break
    return matches


def _line(c, y: float, text: str, font: str = "Helvetica", size: int = 9) -> float:
    if y < MARGIN + ROW_H:
        return y
    c.setFont(font, size)
    c.drawString(MARGIN, y, text[:110])
    return y - ROW_H


def _section(c, y: float, title: str) -> float:
    y -= ROW_H * 0.5
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN, y, title)
    y -= ROW_H * 0.35
    c.setLineWidth(0.3)
    c.line(MARGIN, y, PAGE_W - MARGIN, y)
    return y - ROW_H


def _draw_entries(c, y: float, title: str, entries: list[BundleEntry]) -> float:
    y = _section(c, y, title)
    if not entries:
        return _line(c, y, "No entries found.")
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGIN, y, "Ticket")
    c.drawString(MARGIN + 26, y, "AutoNum")
    c.drawString(MARGIN + 70, y, "Class")
    c.drawString(MARGIN + 130, y, "Source")
    y -= ROW_H
    for entry in entries:
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN, y, str(entry.ticket_no or "-"))
        c.drawString(MARGIN + 26, y, str(entry.auto_num or "-"))
        c.drawString(MARGIN + 70, y, entry.class_code or "")
        c.drawString(MARGIN + 130, y, entry.source)
        y -= ROW_H
    return y


def generate_exhibitor_bundle(
    exh_no: int,
    sd=None,
    include_tickets: bool = True,
    include_late: bool = True,
    include_results: bool = True,
    include_address_label: bool = True,
) -> bytes:
    exhibitor = _exhibitor_or_error(exh_no)
    return _generate_exhibitor_bundle_for_row(
        exhibitor,
        sd=sd,
        include_tickets=include_tickets,
        include_late=include_late,
        include_results=include_results,
        include_address_label=include_address_label,
    )


def generate_exhibitor_bundle_for_exhibitor(
    exhibitor_id: int,
    sd=None,
    include_tickets: bool = True,
    include_late: bool = True,
    include_results: bool = True,
    include_address_label: bool = True,
) -> bytes:
    exhibitor = _exhibitor_id_or_error(exhibitor_id)
    return _generate_exhibitor_bundle_for_row(
        exhibitor,
        sd=sd,
        include_tickets=include_tickets,
        include_late=include_late,
        include_results=include_results,
        include_address_label=include_address_label,
    )


def _generate_exhibitor_bundle_for_row(
    exhibitor: Exhibitor,
    sd=None,
    include_tickets: bool = True,
    include_late: bool = True,
    include_results: bool = True,
    include_address_label: bool = True,
) -> bytes:
    regular = _regular_entries(exhibitor)
    late = _late_entries(exhibitor) if include_late else []

    result_by_auto = {
        row.exhibit_no: row.result
        for row in Result.select().where(Result.result.is_null(False))
    }
    nb_set = {row.exhibit_no for row in NotBenched.select()}

    buf, c = new_canvas()
    page_num = 1
    bundle_label = (
        f"#{exhibitor.exh_no}"
        if exhibitor.exh_no is not None
        else exhibitor.name or f"row {exhibitor.id}"
    )
    y = draw_page_header(c, f"Exhibitor Bundle {bundle_label}", sd)

    y = _section(c, y, "Exhibitor Summary")
    y = _line(c, y, f"Name: {exhibitor.name or ''}", "Helvetica-Bold", 10)
    y = _line(c, y, f"Exhibitor #: {exhibitor.exh_no if exhibitor.exh_no is not None else 'not assigned'}")
    y = _line(c, y, f"Club: {exhibitor.club or ''}")
    y = _line(c, y, f"Phone: {exhibitor.cell_no or exhibitor.tel_home or ''}")
    y = _line(c, y, f"Email: {exhibitor.email or ''}")

    y = _draw_entries(
        c,
        y,
        "Entry Confirmation",
        regular
        if include_tickets
        else [BundleEntry(None, e.auto_num, e.class_code, e.source) for e in regular],
    )

    if include_late:
        y = _draw_entries(c, y, "Late Entries", late)

    if include_results:
        result_entries = []
        for entry in regular:
            result_entries.append(
                BundleEntry(
                    ticket_no=entry.ticket_no,
                    auto_num=entry.auto_num,
                    class_code=entry.class_code,
                    source="Result",
                    result=result_by_auto.get(entry.auto_num),
                    not_benched=entry.auto_num in nb_set,
                )
            )
        y = _section(c, y, "Results")
        if not result_entries or not any(e.result or e.not_benched for e in result_entries):
            y = _line(c, y, "No results recorded yet.")
        else:
            for entry in result_entries:
                status = "NB" if entry.not_benched else (entry.result or "")
                y = _line(
                    c,
                    y,
                    f"#{entry.auto_num or '-'}  {entry.class_code or ''}  {status}",
                )

    if include_address_label and exhibitor.print_address:
        y = _section(c, y, "Address Label")
        for part in [
            exhibitor.name,
            exhibitor.address,
            exhibitor.suburb,
            exhibitor.town,
            exhibitor.zip_code,
        ]:
            if part:
                y = _line(c, y, str(part), "Helvetica", 10)

    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()
