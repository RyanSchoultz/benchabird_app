"""Service helpers for steward/operator Judge Mode."""

from __future__ import annotations

from dataclasses import dataclass

from models.results import Result
from models.show_entry import CalculatedEntry
from services.not_benched_service import (
    is_not_benched,
    mark_not_benched,
    unmark_not_benched,
)
from services.results_service import record_result
from services.scan_parser_service import ScanParseError, parse_scan_to_auto_num


class JudgeModeError(ValueError):
    pass


@dataclass(frozen=True)
class JudgeEntryContext:
    auto_num: int
    exh_no: int | None
    name: str | None
    class_code: str | None
    result: str | None
    not_benched: bool


def _context_for_auto_num(auto_num: int) -> JudgeEntryContext:
    entry = CalculatedEntry.get_or_none(CalculatedEntry.auto_num == auto_num)
    if entry is None:
        raise JudgeModeError(f"No calculated entry found for exhibit #{auto_num}.")
    result_row = Result.get_or_none(Result.exhibit_no == auto_num)
    return JudgeEntryContext(
        auto_num=entry.auto_num,
        exh_no=entry.exh_no,
        name=entry.name,
        class_code=entry.class_code,
        result=result_row.result if result_row else None,
        not_benched=is_not_benched(auto_num),
    )


def resolve_judge_entry(text: str, class_filter: str | None = None) -> JudgeEntryContext:
    try:
        auto_num = parse_scan_to_auto_num(text)
    except ScanParseError as exc:
        raise JudgeModeError(str(exc)) from exc
    ctx = _context_for_auto_num(auto_num)
    selected = (class_filter or "").strip()
    if selected and (ctx.class_code or "") != selected:
        raise JudgeModeError(
            f"Exhibit #{ctx.auto_num} is outside selected class {selected}."
        )
    return ctx


def save_judge_result(auto_num: int, result: str) -> JudgeEntryContext:
    _context_for_auto_num(auto_num)
    record_result(auto_num, result)
    if is_not_benched(auto_num):
        unmark_not_benched(auto_num)
    return _context_for_auto_num(auto_num)


def toggle_judge_not_benched(auto_num: int) -> JudgeEntryContext:
    _context_for_auto_num(auto_num)
    if is_not_benched(auto_num):
        unmark_not_benched(auto_num)
    else:
        mark_not_benched(auto_num)
    return _context_for_auto_num(auto_num)
