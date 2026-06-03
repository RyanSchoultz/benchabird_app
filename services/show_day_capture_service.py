from __future__ import annotations

from dataclasses import dataclass

from models.results import NotBenched, Result
from models.show_entry import CalculatedEntry
from models.special import SpecialList, SpecialWinner
from services.judging_catalogue_service import get_judging_entries, list_judging_categories


@dataclass(frozen=True)
class CaptureSummary:
    total_categories: int
    categories_complete: int
    results_entered: int
    not_benched: int
    specials_assigned: int
    issue_count: int
    next_action: str


@dataclass(frozen=True)
class CategoryStatus:
    category: str
    entry_count: int
    completed_count: int
    status: str


@dataclass(frozen=True)
class ValidationIssue:
    kind: str
    severity: str
    message: str
    action: str
    target: str


@dataclass(frozen=True)
class SpecialAssignmentRow:
    special_nr: str
    description: str
    prize: str
    exhibit_no: int | None
    winner_name: str
    class_code: str
    result: str
    status: str


@dataclass(frozen=True)
class SpecialCandidate:
    auto_num: int
    exh_no: int | None
    name: str
    class_code: str
    result: str
    not_benched: bool


def _normal_result(value: str | None) -> str:
    return (value or "").strip()


def _completed_exhibit_numbers() -> set[int]:
    result_nums = {
        row.exhibit_no
        for row in Result.select().where(Result.result.is_null(False))
        if row.exhibit_no is not None and _normal_result(row.result)
    }
    nb_nums = {row.exhibit_no for row in NotBenched.select()}
    return result_nums | nb_nums


def get_category_statuses() -> list[CategoryStatus]:
    completed = _completed_exhibit_numbers()
    rows: list[CategoryStatus] = []
    for category in list_judging_categories():
        entries = get_judging_entries(category.key)
        done = sum(1 for entry in entries if entry.auto_num in completed)
        if done == 0:
            status = "Not started"
        elif done >= len(entries):
            status = "Complete"
        else:
            status = "In progress"
        rows.append(CategoryStatus(category.label, len(entries), done, status))
    return rows


def _next_action(
    total_categories: int,
    categories_complete: int,
    specials_assigned: int,
    total_specials: int,
    issue_count: int,
) -> str:
    if total_categories == 0:
        return "Bench birds before capturing results"
    if categories_complete < total_categories:
        remaining = total_categories - categories_complete
        return f"{remaining} categories still need review"
    if total_specials and specials_assigned < total_specials:
        return "Special winners ready to assign"
    if issue_count:
        return f"{issue_count} validation issues need attention"
    return "Ready to publish final reports"


def get_capture_summary() -> CaptureSummary:
    categories = get_category_statuses()
    total_categories = len(categories)
    categories_complete = sum(1 for row in categories if row.status == "Complete")
    results_entered = Result.select().where(Result.result.is_null(False)).count()
    not_benched = NotBenched.select().count()
    specials_assigned = SpecialWinner.select().where(SpecialWinner.exhibit_no.is_null(False)).count()
    total_specials = SpecialList.select().count()
    issues = validate_capture()
    next_action = _next_action(
        total_categories,
        categories_complete,
        specials_assigned,
        total_specials,
        len(issues),
    )
    return CaptureSummary(
        total_categories=total_categories,
        categories_complete=categories_complete,
        results_entered=results_entered,
        not_benched=not_benched,
        specials_assigned=specials_assigned,
        issue_count=len(issues),
        next_action=next_action,
    )


def validate_capture() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    calculated_nums = {row.auto_num for row in CalculatedEntry.select(CalculatedEntry.auto_num)}
    completed = _completed_exhibit_numbers()

    for status in get_category_statuses():
        if status.entry_count == 0:
            continue
        if status.completed_count == 0:
            issues.append(ValidationIssue(
                "category-not-started",
                "warning",
                f"{status.category} has not been captured.",
                "Open Judging Capture",
                status.category,
            ))
        elif status.completed_count < status.entry_count:
            issues.append(ValidationIssue(
                "category-incomplete",
                "warning",
                f"{status.category} has {status.entry_count - status.completed_count} uncaptured birds.",
                "Open Judging Capture",
                status.category,
            ))

    db = CalculatedEntry._meta.database
    duplicate_sql = """
        SELECT ce.class_code, r.result, COUNT(*)
        FROM result r
        JOIN calculated_entry ce ON ce.auto_num = r.exhibit_no
        WHERE r.result IS NOT NULL AND TRIM(r.result) <> ''
        GROUP BY ce.class_code, r.result
        HAVING COUNT(*) > 1
    """
    for class_code, result, count in db.execute_sql(duplicate_sql).fetchall():
        issues.append(ValidationIssue(
            "duplicate-placing",
            "error",
            f"{class_code} has {count} entries marked {result}.",
            "Review class",
            str(class_code or ""),
        ))

    winner_map = {
        row.special_nr: row.exhibit_no
        for row in SpecialWinner.select()
        if row.special_nr
    }
    nb_set = {row.exhibit_no for row in NotBenched.select()}
    for special in SpecialList.select().order_by(SpecialList.special_nr):
        exhibit_no = winner_map.get(special.special_nr)
        if not exhibit_no:
            issues.append(ValidationIssue(
                "special-missing-winner",
                "warning",
                f"{special.special_nr} has no winner assigned.",
                "Assign special winner",
                special.special_nr or "",
            ))
        elif exhibit_no in nb_set:
            issues.append(ValidationIssue(
                "special-assigned-nb",
                "error",
                f"{special.special_nr} is assigned to NB exhibit #{exhibit_no}.",
                "Review special winner",
                special.special_nr or "",
            ))
        elif exhibit_no not in calculated_nums:
            issues.append(ValidationIssue(
                "special-unbenched",
                "error",
                f"{special.special_nr} is assigned to unknown exhibit #{exhibit_no}.",
                "Review special winner",
                special.special_nr or "",
            ))

    for result in Result.select().where(Result.result.is_null(False)):
        if result.exhibit_no not in calculated_nums:
            issues.append(ValidationIssue(
                "result-unbenched",
                "error",
                f"Result {result.result} is recorded for unknown exhibit #{result.exhibit_no}.",
                "Review result",
                str(result.exhibit_no or ""),
            ))

    for row in CalculatedEntry.select(CalculatedEntry.auto_num):
        if row.auto_num not in completed:
            issues.append(ValidationIssue(
                "benched-uncaptured",
                "info",
                f"Exhibit #{row.auto_num} has neither result nor NB.",
                "Capture result",
                str(row.auto_num),
            ))
    return issues


def list_special_assignment_rows() -> list[SpecialAssignmentRow]:
    db = SpecialList._meta.database
    sql = """
        SELECT sl.special_nr, COALESCE(sl.description, ''), COALESCE(sl.prize1, ''),
               sw.exhibit_no, COALESCE(ce.name, ''), COALESCE(ce.class_code, ''),
               COALESCE(r.result, '')
        FROM special_list sl
        LEFT JOIN special_winner sw ON sw.special_nr = sl.special_nr
        LEFT JOIN calculated_entry ce ON ce.auto_num = sw.exhibit_no
        LEFT JOIN result r ON r.exhibit_no = sw.exhibit_no
        ORDER BY sl.kind_sequence, sl.special_nr
    """
    rows = []
    for row in db.execute_sql(sql).fetchall():
        status = "Assigned" if row[3] else "Missing"
        rows.append(SpecialAssignmentRow(
            special_nr=row[0] or "",
            description=row[1] or "",
            prize=row[2] or "",
            exhibit_no=row[3],
            winner_name=row[4] or "",
            class_code=row[5] or "",
            result=row[6] or "",
            status=status,
        ))
    return rows


def search_special_candidates(query: str = "") -> list[SpecialCandidate]:
    q = query.strip().lower()
    nb_set = {row.exhibit_no for row in NotBenched.select()}
    result_map = {
        row.exhibit_no: row.result or ""
        for row in Result.select().where(Result.result.is_null(False))
    }
    rows = []
    for entry in CalculatedEntry.select().order_by(CalculatedEntry.auto_num):
        result = result_map.get(entry.auto_num, "")
        haystack = " ".join([
            str(entry.auto_num or ""),
            str(entry.exh_no or ""),
            entry.name or "",
            entry.class_code or "",
            result,
        ]).lower()
        if q and q not in haystack:
            continue
        rows.append(SpecialCandidate(
            auto_num=entry.auto_num,
            exh_no=entry.exh_no,
            name=entry.name or "",
            class_code=entry.class_code or "",
            result=result,
            not_benched=entry.auto_num in nb_set,
        ))
    return sorted(rows, key=lambda row: (not bool(row.result), row.auto_num))
