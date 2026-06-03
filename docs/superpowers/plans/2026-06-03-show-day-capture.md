# Show Day Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a top-level Show Day Capture workspace that unifies judging capture, special winner assignment, validation, and final report publishing while keeping existing Results and Special Winners screens as fallbacks.

**Architecture:** Add a focused `show_day_capture_service` for summary counters, category statuses, special assignment rows, candidate search, and validation issues. Add `ShowDayCaptureView` as a staged CustomTkinter workspace that composes existing judging capture, special assignment, and report preview behavior instead of duplicating those engines. Update navigation, dashboard, README, and Help to make the new workspace the primary show-day result workflow.

**Tech Stack:** Python, CustomTkinter, Peewee, SQLite, ReportLab-backed existing PDF services, pytest.

---

## File Structure

- Create `services/show_day_capture_service.py`: read-only workflow summary, category status, special rows/candidates, validation checks, next-action message.
- Create `views/show_day_capture_view.py`: staged workspace UI with `Judging Capture`, `Special Winners`, `Validation`, and `Publish` stages.
- Create `tests/test_show_day_capture_service.py`: service summary, category status, validation, and candidate search coverage.
- Create `tests/test_show_day_capture_view_imports.py`: view import and publish report map smoke coverage.
- Modify `views/main_window.py`: add `Show Day Capture` nav key and view mapping, keep `Results` and `Special Winners`.
- Modify `views/dashboard.py`: point the result quick action at `capture`.
- Modify `views/welcome_view.py`: point show-day/result quick action text at `capture` if present in that file.
- Modify `views/help_view.py`: document the new workspace and retain fallback-screen wording.
- Modify `README.md`: update feature list and workflow documentation.

---

### Task 1: Show Day Capture Service

**Files:**
- Create: `services/show_day_capture_service.py`
- Test: `tests/test_show_day_capture_service.py`

- [ ] **Step 1: Write failing summary and validation tests**

Create `tests/test_show_day_capture_service.py` with:

```python
from models.class_def import ClassDef, MainClass, Species
from models.results import NotBenched, Result
from models.show_entry import CalculatedEntry
from models.special import SpecialList, SpecialWinner


def seed_capture_data():
    Species.create(seq=1, bird_type="Gloster", type2="Gloster")
    Species.create(seq=2, bird_type="Red Factor", type2="Red Factor")
    MainClass.create(main_class="Open", mc_seq=1)
    ClassDef.create(
        class_code="GL01",
        bird_type="Gloster",
        main_class="Open",
        colour="Corona hen",
        class_seq=1,
    )
    ClassDef.create(
        class_code="GL02",
        bird_type="Gloster",
        main_class="Open",
        colour="Consort cock",
        class_seq=2,
    )
    ClassDef.create(
        class_code="RF01",
        bird_type="Red Factor",
        main_class="Open",
        colour="Red cock",
        class_seq=1,
    )
    CalculatedEntry.create(auto_num=1, exh_no=10, name="Alice", class_code="GL01")
    CalculatedEntry.create(auto_num=2, exh_no=11, name="Bob", class_code="GL01")
    CalculatedEntry.create(auto_num=3, exh_no=12, name="Cara", class_code="GL02")
    CalculatedEntry.create(auto_num=4, exh_no=13, name="Dan", class_code="RF01")
    SpecialList.create(special_nr="S001", description="Best Gloster", prize1="Rosette")
    SpecialList.create(special_nr="S002", description="Best Red Factor", prize1="Medal")


def test_get_capture_summary_counts_and_next_action(test_db):
    from services.show_day_capture_service import get_capture_summary

    seed_capture_data()
    Result.create(exhibit_no=1, result="1st")
    NotBenched.create(exhibit_no=2, not_benched="Not Benched", nb="NB")
    SpecialWinner.create(special_nr="S001", exhibit_no=1, result="Special")

    summary = get_capture_summary()

    assert summary.total_categories == 2
    assert summary.results_entered == 1
    assert summary.not_benched == 1
    assert summary.specials_assigned == 1
    assert summary.issue_count >= 1
    assert summary.next_action


def test_get_category_statuses_tracks_not_started_in_progress_and_complete(test_db):
    from services.show_day_capture_service import get_category_statuses

    seed_capture_data()
    Result.create(exhibit_no=1, result="1st")
    NotBenched.create(exhibit_no=2, not_benched="Not Benched", nb="NB")
    Result.create(exhibit_no=3, result="2nd")

    rows = get_category_statuses()

    assert [(row.category, row.entry_count, row.completed_count, row.status) for row in rows] == [
        ("Gloster", 3, 3, "Complete"),
        ("Red Factor", 1, 0, "Not started"),
    ]


def test_validate_capture_detects_duplicates_missing_specials_and_orphans(test_db):
    from services.show_day_capture_service import validate_capture

    seed_capture_data()
    Result.create(exhibit_no=1, result="1st")
    Result.create(exhibit_no=2, result="1st")
    Result.create(exhibit_no=999, result="BOB")
    NotBenched.create(exhibit_no=1, not_benched="Not Benched", nb="NB")
    SpecialWinner.create(special_nr="S001", exhibit_no=1, result="Special")

    issues = validate_capture()
    issue_keys = {issue.kind for issue in issues}

    assert "duplicate-placing" in issue_keys
    assert "special-missing-winner" in issue_keys
    assert "special-assigned-nb" in issue_keys
    assert "result-unbenched" in issue_keys
    assert "category-incomplete" in issue_keys


def test_search_special_candidates_prefers_result_rows(test_db):
    from services.show_day_capture_service import search_special_candidates

    seed_capture_data()
    Result.create(exhibit_no=1, result="1st")

    rows = search_special_candidates("alice")

    assert rows[0].auto_num == 1
    assert rows[0].name == "Alice"
    assert rows[0].result == "1st"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_show_day_capture_service.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'services.show_day_capture_service'`.

- [ ] **Step 3: Implement service dataclasses and summary functions**

Create `services/show_day_capture_service.py` with:

```python
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
```

- [ ] **Step 4: Implement validation, special rows, and candidate search**

Append to `services/show_day_capture_service.py`:

```python

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
```

- [ ] **Step 5: Run service tests**

Run: `python -m pytest tests/test_show_day_capture_service.py -q`

Expected: PASS.

- [ ] **Step 6: Commit service slice**

Run:

```bash
git add services/show_day_capture_service.py tests/test_show_day_capture_service.py
git commit -m "feat: add show day capture service"
```

---

### Task 2: Show Day Capture View

**Files:**
- Create: `views/show_day_capture_view.py`
- Test: `tests/test_show_day_capture_view_imports.py`

- [ ] **Step 1: Write failing view import and report map tests**

Create `tests/test_show_day_capture_view_imports.py` with:

```python
def test_show_day_capture_view_imports(test_db):
    from views.show_day_capture_view import ShowDayCaptureView

    assert ShowDayCaptureView.__name__ == "ShowDayCaptureView"


def test_show_day_capture_publish_reports_are_declared(test_db):
    from views.show_day_capture_view import PUBLISH_REPORTS

    labels = [row[0] for row in PUBLISH_REPORTS]

    assert labels == [
        "Marked Catalogue",
        "Results Sheet",
        "Special Winners",
        "Prize Money",
        "Results by Exhibitor",
        "4.4 Marked Catalogue",
    ]
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_show_day_capture_view_imports.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'views.show_day_capture_view'`.

- [ ] **Step 3: Create the staged workspace view**

Create `views/show_day_capture_view.py` with:

```python
import threading

import customtkinter as ctk

from models.reference import ShowDetails
from services.show_day_capture_service import (
    get_capture_summary,
    get_category_statuses,
    list_special_assignment_rows,
    validate_capture,
)


PUBLISH_REPORTS = [
    ("Marked Catalogue", "benchabird_marked_catalogue.pdf", "services.reports.marked_catalogue", "generate_marked_catalogue"),
    ("Results Sheet", "benchabird_results_sheet.pdf", "services.reports.results_sheet", "generate_results_sheet"),
    ("Special Winners", "benchabird_special_winners.pdf", "services.reports.special_winners", "generate_special_winners"),
    ("Prize Money", "benchabird_prize_money.pdf", "services.reports.prize_money", "generate_prize_money"),
    ("Results by Exhibitor", "benchabird_results_by_exhibitor.pdf", "services.reports.results_by_exhibitor", "generate_results_by_exhibitor"),
    ("4.4 Marked Catalogue", "benchabird_4_4_marked_catalogue.pdf", "services.reports.marked_catalogue", "generate_marked_catalogue"),
]


class ShowDayCaptureView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._active_stage = "judging"
        self._stage_buttons: dict[str, ctk.CTkButton] = {}
        self._content = None
        self._status = None
        self._summary_labels: dict[str, ctk.CTkLabel] = {}
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 6))
        ctk.CTkLabel(
            header,
            text="Show Day Capture",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")
        ctk.CTkButton(
            header,
            text="Refresh",
            width=90,
            fg_color=("gray80", "gray30"),
            text_color=("gray10", "gray90"),
            command=self._refresh,
        ).pack(side="right")

        self._status = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
            anchor="w",
        )
        self._status.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))

        strip = ctk.CTkFrame(self, fg_color="transparent")
        strip.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))
        strip.grid_columnconfigure((0, 1, 2, 3), weight=1)
        for col, (key, label) in enumerate([
            ("judging", "Judging Capture"),
            ("specials", "Special Winners"),
            ("validation", "Validation"),
            ("publish", "Publish"),
        ]):
            btn = ctk.CTkButton(
                strip,
                text=label,
                height=34,
                fg_color="transparent",
                text_color=("gray20", "gray80"),
                command=lambda k=key: self._show_stage(k),
            )
            btn.grid(row=0, column=col, sticky="ew", padx=4)
            self._stage_buttons[key] = btn

        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        self._refresh()

    def _refresh(self):
        summary = get_capture_summary()
        self._status.configure(
            text=(
                f"{summary.categories_complete}/{summary.total_categories} categories complete | "
                f"{summary.results_entered} results | {summary.not_benched} NB | "
                f"{summary.specials_assigned} specials | {summary.issue_count} issues | "
                f"{summary.next_action}"
            )
        )
        self._show_stage(self._active_stage)

    def _show_stage(self, key: str):
        self._active_stage = key
        for stage_key, button in self._stage_buttons.items():
            button.configure(
                fg_color=("gray78", "gray28") if stage_key == key else "transparent",
                text_color=("gray5", "white") if stage_key == key else ("gray20", "gray80"),
            )
        for child in self._content.winfo_children():
            child.destroy()
        {
            "judging": self._build_judging_stage,
            "specials": self._build_specials_stage,
            "validation": self._build_validation_stage,
            "publish": self._build_publish_stage,
        }[key]()
```

- [ ] **Step 4: Add Judging Capture and Special Winners stages**

Append to `ShowDayCaptureView` in `views/show_day_capture_view.py`:

```python
    def _build_judging_stage(self):
        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(frame, fg_color=("gray88", "gray20"), corner_radius=8)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ctk.CTkLabel(
            top,
            text="Capture completed Judges Catalogue sheets by category.",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=12, pady=10)
        ctk.CTkButton(
            top,
            text="Open Judging Capture",
            width=160,
            command=self._open_judging_capture,
        ).pack(side="right", padx=12, pady=8)

        for row_i, status in enumerate(get_category_statuses(), start=1):
            row = ctk.CTkFrame(frame, fg_color=("gray92", "gray17") if row_i % 2 else ("gray88", "gray20"), corner_radius=6)
            row.grid(row=row_i, column=0, sticky="ew", pady=2)
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row, text=status.category, anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=6)
            ctk.CTkLabel(row, text=f"{status.completed_count}/{status.entry_count}", width=80).grid(row=0, column=1, padx=6)
            ctk.CTkLabel(row, text=status.status, width=110).grid(row=0, column=2, padx=10)

    def _open_judging_capture(self):
        from views._judging_capture_dialog import JudgingCaptureDialog

        JudgingCaptureDialog(self, on_saved=self._refresh)

    def _build_specials_stage(self):
        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        rows = list_special_assignment_rows()
        if not rows:
            ctk.CTkLabel(frame, text="No special prizes found. Add them in Special Prizes.").grid(row=0, column=0, sticky="w", pady=8)
            return

        for row_i, item in enumerate(rows):
            row = ctk.CTkFrame(frame, fg_color=("gray92", "gray17") if row_i % 2 else ("gray88", "gray20"), corner_radius=6)
            row.grid(row=row_i, column=0, sticky="ew", pady=2)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text=item.special_nr, width=70, anchor="w").grid(row=0, column=0, padx=10, pady=7)
            detail = item.description or item.prize
            winner = f"#{item.exhibit_no} {item.winner_name} {item.result}".strip() if item.exhibit_no else "Missing winner"
            ctk.CTkLabel(row, text=detail, anchor="w").grid(row=0, column=1, sticky="ew", padx=6)
            ctk.CTkLabel(row, text=winner, width=190, anchor="w").grid(row=0, column=2, padx=6)
            ctk.CTkButton(
                row,
                text="Assign",
                width=76,
                height=26,
                command=lambda nr=item.special_nr, desc=item.description, exh=item.exhibit_no: self._open_special_assign(nr, desc, exh),
            ).grid(row=0, column=3, padx=8)

    def _open_special_assign(self, special_nr: str, description: str, current_exhibit_no):
        from views._special_dialog import SpecialAssignDialog

        dialog = SpecialAssignDialog(self, special_nr, description, current_exhibit_no)
        self.wait_window(dialog)
        self._refresh()
```

- [ ] **Step 5: Add Validation and Publish stages**

Append to `ShowDayCaptureView` in `views/show_day_capture_view.py`:

```python
    def _build_validation_stage(self):
        frame = ctk.CTkScrollableFrame(self._content, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(1, weight=1)
        issues = validate_capture()
        if not issues:
            ctk.CTkLabel(frame, text="No validation issues found.").grid(row=0, column=0, sticky="w", pady=8)
            return
        for row_i, issue in enumerate(issues):
            row = ctk.CTkFrame(frame, fg_color=("gray92", "gray17") if row_i % 2 else ("gray88", "gray20"), corner_radius=6)
            row.grid(row=row_i, column=0, sticky="ew", pady=2)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text=issue.severity.upper(), width=70).grid(row=0, column=0, padx=8, pady=7)
            ctk.CTkLabel(row, text=issue.message, anchor="w").grid(row=0, column=1, sticky="ew", padx=6)
            ctk.CTkButton(
                row,
                text=issue.action,
                width=140,
                height=26,
                command=lambda target=issue.action: self._jump_for_issue(target),
            ).grid(row=0, column=2, padx=8)

    def _jump_for_issue(self, action: str):
        if "special" in action.lower():
            self._show_stage("specials")
        else:
            self._show_stage("judging")

    def _build_publish_stage(self):
        frame = ctk.CTkFrame(self._content, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nw")
        for i, (label, default_name, module_name, function_name) in enumerate(PUBLISH_REPORTS):
            row, col = divmod(i, 3)
            ctk.CTkButton(
                frame,
                text=label,
                width=190,
                height=52,
                command=lambda m=module_name, f=function_name, n=default_name: self._generate_report(m, f, n),
            ).grid(row=row, column=col, padx=8, pady=8)

    def _get_sd(self):
        return ShowDetails.select().first()

    def _generate_report(self, module_name: str, function_name: str, default_name: str):
        self._status.configure(text=f"Generating {default_name}...")
        sd = self._get_sd()

        def run():
            try:
                module = __import__(module_name, fromlist=[function_name])
                gen_fn = getattr(module, function_name)
                pdf_bytes = gen_fn(sd=sd)
                self.after(0, lambda: self._show_preview(pdf_bytes, default_name))
            except Exception as exc:
                self.after(0, lambda: self._status.configure(text=f"Error: {str(exc)[:80]}"))

        threading.Thread(target=run, daemon=True).start()

    def _show_preview(self, pdf_bytes: bytes, default_name: str):
        self._refresh()
        from views.pdf_preview_window import PDFPreviewWindow

        title = default_name.replace("benchabird_", "").replace(".pdf", "").replace("_", " ").title()
        PDFPreviewWindow(self, pdf_bytes, title, default_name)
```

- [ ] **Step 6: Run view tests**

Run: `python -m pytest tests/test_show_day_capture_view_imports.py -q`

Expected: PASS.

- [ ] **Step 7: Commit view slice**

Run:

```bash
git add views/show_day_capture_view.py tests/test_show_day_capture_view_imports.py
git commit -m "feat: add show day capture workspace"
```

---

### Task 3: Navigation and Dashboard Wiring

**Files:**
- Modify: `views/main_window.py`
- Modify: `views/dashboard.py`
- Modify: `views/welcome_view.py`
- Test: `tests/test_show_day_capture_view_imports.py`

- [ ] **Step 1: Add failing navigation assertion**

Append to `tests/test_show_day_capture_view_imports.py`:

```python
def test_main_window_nav_exposes_show_day_capture_without_removing_fallbacks(test_db):
    from views.main_window import NAV

    labels = [label for label, _ in NAV]
    keys = [key for _, key in NAV]

    assert "Show Day Capture" in labels
    assert "Results" in labels
    assert "Special Winners" in labels
    assert keys.index("capture") < keys.index("results")
```

- [ ] **Step 2: Run navigation test to verify failure**

Run: `python -m pytest tests/test_show_day_capture_view_imports.py::test_main_window_nav_exposes_show_day_capture_without_removing_fallbacks -q`

Expected: FAIL because `capture` is not in `NAV`.

- [ ] **Step 3: Wire main navigation**

In `views/main_window.py`, update `NAV`:

```python
    ("Show Participants", "participants"),
    ("Show Day Capture",  "capture"),
    ("Results",           "results"),
```

In `_make_view`, add import:

```python
        from views.show_day_capture_view import ShowDayCaptureView
```

In `view_map`, add:

```python
            "capture":       ShowDayCaptureView,
```

Leave `Ctrl+R` bound to `"results"` for this rollout.

- [ ] **Step 4: Update dashboard quick action**

In `views/dashboard.py`, replace the quick action:

```python
            ("Enter Results",   "results",      "Record judging results"),
```

with:

```python
            ("Show Day Capture", "capture",     "Capture results and awards"),
```

If `views/welcome_view.py` contains a quick action tuple for `"Enter Results"` with key `"results"`, replace only that quick action with key `"capture"` and label `"Show Day Capture"`. Keep shortcut text that explicitly says `Ctrl+R` points to Results until the fallback period ends.

- [ ] **Step 5: Run navigation tests**

Run: `python -m pytest tests/test_show_day_capture_view_imports.py -q`

Expected: PASS.

- [ ] **Step 6: Commit navigation slice**

Run:

```bash
git add views/main_window.py views/dashboard.py views/welcome_view.py tests/test_show_day_capture_view_imports.py
git commit -m "feat: wire show day capture navigation"
```

---

### Task 4: Documentation Updates

**Files:**
- Modify: `README.md`
- Modify: `views/help_view.py`

- [ ] **Step 1: Update README feature list and workflow**

In `README.md`, change the feature table area so the result-related rows read:

```markdown
| **Show Day Capture** | Unified show-day result workflow: Judging Capture, Special Winners, Validation, and Publish stages for completed paper Judges Catalogue sheets |
| **Results** | Temporary fallback rapid-entry screen for manual result corrections, scanner entry, and Not Benched changes |
| **Special Winners** | Temporary fallback assignment screen for special prize winners by exhibit number |
| **Special Prizes** | Setup/reference screen for the prize list: description, trophy type, cash amounts |
```

In the show workflow list, replace the results/special winners steps with:

```markdown
6. **Show Day Capture** - capture completed Judges Catalogue sheets, assign special winners, review validation, and publish final outputs
7. **Reports** - generate any remaining Results Sheet, Show Catalogue, Prize Money, Address Tags, etc.
8. **Archive** (optional) - save a snapshot before resetting for next season
```

- [ ] **Step 2: Update Help navigation and workflow wording**

In `views/help_view.py`, update the Main section string to include:

```python
            "  Show Day Capture  - capture judging sheets, specials, validation, and final outputs\n"
```

Place it after `Show Participants`.

Update recommended workflow strings so result capture uses:

```python
            "7. Show Day Capture - capture completed Judges Catalogue sheets, assign specials, validate, and publish\n"
```

Add a new `SECTIONS` entry before `"Results"`:

```python
    "Show Day Capture": [
        ("Overview", (
            "Show Day Capture is the primary show-day result workflow. Use it after "
            "judges complete the printed Judges Catalogue sheets.\n\n"
            "The workspace has four stages: Judging Capture, Special Winners, "
            "Validation, and Publish. Results and Special Winners remain available "
            "as fallback screens during rollout."
        )),
        ("Recommended Flow", (
            "1. Open Judging Capture and save each completed category/page\n"
            "2. Assign Special Winners from captured exhibit numbers\n"
            "3. Review Validation for missing results, duplicate placings, and special-winner issues\n"
            "4. Use Publish to generate marked catalogue, results, specials, prize money, and exhibitor result reports"
        )),
    ],
```

- [ ] **Step 3: Run import smoke tests**

Run: `python -m pytest tests/test_show_day_capture_view_imports.py tests/test_judging_capture_imports.py -q`

Expected: PASS.

- [ ] **Step 4: Commit documentation slice**

Run:

```bash
git add README.md views/help_view.py
git commit -m "docs: document show day capture workflow"
```

---

### Task 5: Full Verification and Build

**Files:**
- No planned code edits.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/test_show_day_capture_service.py tests/test_show_day_capture_view_imports.py tests/test_judging_capture_imports.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full test suite**

Run:

```bash
python -m pytest tests
```

Expected: PASS. A `.pytest_cache` warning is acceptable if it matches the existing permission warning and no tests fail.

- [ ] **Step 3: Build packaged exe**

Run:

```bash
python -m PyInstaller benchabird.spec --clean
```

Expected: build completes successfully and writes `dist\benchabird.exe`.

- [ ] **Step 4: Inspect final diff**

Run:

```bash
git status --short
git diff --stat
```

Expected: show only the intended Show Day Capture changes plus the existing unrelated dirty worktree items. Do not revert unrelated files.

- [ ] **Step 5: Final handoff**

Report:

- New screen and route: `Show Day Capture` / `capture`.
- Old `Results` and `Special Winners` screens are still present as fallbacks.
- Verification commands and outcomes.
- Packaged exe location if build passed: `dist\benchabird.exe`.
