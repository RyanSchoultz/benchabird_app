# Judge Mode QOL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a steward/operator Judge Mode for fast, scan-first result entry during judging.

**Architecture:** Add a focused service that resolves scanned entries into display context and records judge actions. Add a Results-launched Judge Mode dialog that uses the service, existing QR scan parser, existing webcam/mobile scanner flows where practical, and existing result/NB persistence.

**Tech Stack:** Python, Peewee, CustomTkinter, pytest

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `tests/test_judge_mode_service.py` | Create | Service tests for scan context, class filter, result save, NB toggling |
| `services/judge_mode_service.py` | Create | Resolve scanned entries and save Judge Mode actions |
| `views/_judge_mode_dialog.py` | Create | Operational Judge Mode UI launched from Results |
| `views/results_view.py` | Modify | Add `Judge Mode` button |
| `views/help_view.py` | Modify | Document Judge Mode |
| `README.md` | Modify | Document Judge Mode |

---

## Task 1: RED Service Tests

**Files:**
- Create: `tests/test_judge_mode_service.py`

- [ ] **Step 1: Add failing service tests**

Create `tests/test_judge_mode_service.py`:

```python
import pytest

from models.results import Result
from models.show_entry import CalculatedEntry
from services.judge_mode_service import (
    JudgeModeError,
    resolve_judge_entry,
    save_judge_result,
    toggle_judge_not_benched,
)


def test_resolve_judge_entry_returns_context(test_db):
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")

    ctx = resolve_judge_entry("AutoNum:42 ExhNo:7 Class:A1")

    assert ctx.auto_num == 42
    assert ctx.exh_no == 7
    assert ctx.name == "Alice Bird"
    assert ctx.class_code == "A1"
    assert ctx.result is None
    assert ctx.not_benched is False


def test_resolve_judge_entry_includes_existing_result_and_nb(test_db):
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")
    save_judge_result(42, "1st")
    toggle_judge_not_benched(42)

    ctx = resolve_judge_entry("42")

    assert ctx.result == "1st"
    assert ctx.not_benched is True


def test_resolve_judge_entry_rejects_unknown_calculated_entry(test_db):
    with pytest.raises(JudgeModeError, match="No calculated entry"):
        resolve_judge_entry("42")


def test_resolve_judge_entry_blocks_class_filter_mismatch(test_db):
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")

    with pytest.raises(JudgeModeError, match="outside selected class"):
        resolve_judge_entry("42", class_filter="B2")


def test_save_judge_result_records_and_clears_not_benched(test_db):
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")
    toggle_judge_not_benched(42)

    ctx = save_judge_result(42, "BOB")

    assert Result.get(Result.exhibit_no == 42).result == "BOB"
    assert ctx.result == "BOB"
    assert ctx.not_benched is False


def test_toggle_judge_not_benched_marks_then_unmarks(test_db):
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")

    marked = toggle_judge_not_benched(42)
    unmarked = toggle_judge_not_benched(42)

    assert marked.not_benched is True
    assert unmarked.not_benched is False
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_judge_mode_service.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'services.judge_mode_service'`.

- [ ] **Step 3: Commit RED tests**

Run:

```bash
git add tests/test_judge_mode_service.py
git commit -m "test: add judge mode service coverage"
```

---

## Task 2: Judge Mode Service

**Files:**
- Create: `services/judge_mode_service.py`
- Test: `tests/test_judge_mode_service.py`

- [ ] **Step 1: Implement service**

Create `services/judge_mode_service.py`:

```python
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
```

- [ ] **Step 2: Run focused tests**

Run:

```bash
python -m pytest tests/test_judge_mode_service.py -v
```

Expected: PASS.

- [ ] **Step 3: Commit service**

Run:

```bash
git add services/judge_mode_service.py tests/test_judge_mode_service.py
git commit -m "feat: add judge mode service"
```

---

## Task 3: Judge Mode Dialog

**Files:**
- Create: `views/_judge_mode_dialog.py`
- Modify: `tests/test_judge_mode_service.py`

- [ ] **Step 1: Add dialog import smoke test**

Append to `tests/test_judge_mode_service.py`:

```python
def test_judge_mode_dialog_imports():
    from views._judge_mode_dialog import JudgeModeDialog

    assert JudgeModeDialog.__name__ == "JudgeModeDialog"
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_judge_mode_service.py::test_judge_mode_dialog_imports -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'views._judge_mode_dialog'`.

- [ ] **Step 3: Create dialog**

Create `views/_judge_mode_dialog.py`:

```python
import customtkinter as ctk

from services.judge_mode_service import (
    JudgeModeError,
    resolve_judge_entry,
    save_judge_result,
    toggle_judge_not_benched,
)
from views._mobile_scanner_dialog import MobileScannerDialog
from views._webcam_scanner_dialog import WebcamScannerDialog

RESULT_OPTIONS = ["1st", "2nd", "3rd", "4th", "5th", "BOB", "R/U BOB", "Champion", "Reserve"]


class JudgeModeDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_changed=None):
        super().__init__(parent)
        self._on_changed = on_changed
        self._current_auto_num = None
        self._recent = []
        self.title("Judge Mode")
        self.geometry("720x540")
        self.minsize(560, 420)
        self._build()
        self._scan_entry.focus()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            self,
            text="Judge Mode",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        top = ctk.CTkFrame(self, fg_color=("gray88", "gray20"), corner_radius=8)
        top.grid(row=1, column=0, sticky="ew", padx=16, pady=8)

        ctk.CTkLabel(top, text="Class filter").pack(side="left", padx=(12, 4), pady=10)
        self._class_entry = ctk.CTkEntry(top, width=100, placeholder_text="optional")
        self._class_entry.pack(side="left", padx=4, pady=10)

        ctk.CTkLabel(top, text="Scan / Exhibit #").pack(side="left", padx=(16, 4), pady=10)
        self._scan_entry = ctk.CTkEntry(top, width=180)
        self._scan_entry.pack(side="left", padx=4, pady=10)
        self._scan_entry.bind("<Return>", lambda _e: self._resolve_scan())

        ctk.CTkButton(top, text="Accept", width=80, command=self._resolve_scan).pack(
            side="left", padx=8, pady=10
        )
        ctk.CTkButton(
            top,
            text="Scan QR",
            width=82,
            fg_color=("gray75", "gray35"),
            text_color=("gray10", "gray90"),
            command=self._open_webcam_scanner,
        ).pack(side="left", padx=4, pady=10)
        ctk.CTkButton(
            top,
            text="Mobile Scan",
            width=105,
            fg_color=("gray75", "gray35"),
            text_color=("gray10", "gray90"),
            command=self._open_mobile_scanner,
        ).pack(side="left", padx=4, pady=10)

        self._context = ctk.CTkLabel(
            self,
            text="Scan a ticket QR or type an exhibit number.",
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=13),
        )
        self._context.grid(row=2, column=0, sticky="ew", padx=16, pady=8)

        result_panel = ctk.CTkFrame(self, fg_color="transparent")
        result_panel.grid(row=3, column=0, sticky="nsew", padx=16, pady=8)

        for index, result in enumerate(RESULT_OPTIONS):
            ctk.CTkButton(
                result_panel,
                text=result,
                width=110,
                command=lambda value=result: self._save(value),
            ).grid(row=index // 3, column=index % 3, padx=5, pady=5)

        ctk.CTkButton(
            result_panel,
            text="Not Benched",
            width=110,
            fg_color=("gray75", "gray35"),
            text_color=("gray10", "gray90"),
            command=self._toggle_nb,
        ).grid(row=3, column=0, padx=5, pady=5)

        self._recent_label = ctk.CTkLabel(
            self,
            text="Recent: none",
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._recent_label.grid(row=4, column=0, sticky="ew", padx=16, pady=(4, 16))

    def _resolve_scan(self):
        try:
            ctx = resolve_judge_entry(
                self._scan_entry.get(),
                class_filter=self._class_entry.get(),
            )
        except JudgeModeError as exc:
            self._context.configure(text=str(exc))
            return "break"
        self._show_context(ctx)
        return "break"

    def _accept_payload(self, payload):
        self._scan_entry.delete(0, "end")
        self._scan_entry.insert(0, payload)
        self._resolve_scan()
        return self._current_auto_num is not None

    def _open_webcam_scanner(self):
        WebcamScannerDialog(self, self._accept_payload)

    def _open_mobile_scanner(self):
        MobileScannerDialog(self, self._accept_payload)

    def _show_context(self, ctx):
        self._current_auto_num = ctx.auto_num
        status = "NB" if ctx.not_benched else (ctx.result or "No result yet")
        self._context.configure(
            text=(
                f"Exhibit #{ctx.auto_num}  Class: {ctx.class_code or ''}\n"
                f"Exhibitor #{ctx.exh_no or ''}  {ctx.name or ''}\n"
                f"Current: {status}"
            )
        )

    def _save(self, result):
        if self._current_auto_num is None:
            self._context.configure(text="Scan an exhibit before saving a result.")
            return
        ctx = save_judge_result(self._current_auto_num, result)
        self._after_change(ctx, result)

    def _toggle_nb(self):
        if self._current_auto_num is None:
            self._context.configure(text="Scan an exhibit before marking Not Benched.")
            return
        ctx = toggle_judge_not_benched(self._current_auto_num)
        self._after_change(ctx, "NB" if ctx.not_benched else "NB removed")

    def _after_change(self, ctx, label):
        self._show_context(ctx)
        self._recent.insert(0, f"#{ctx.auto_num} {ctx.class_code or ''}: {label}")
        self._recent = self._recent[:6]
        self._recent_label.configure(text="Recent:\n" + "\n".join(self._recent))
        self._scan_entry.delete(0, "end")
        self._scan_entry.focus()
        if self._on_changed:
            self._on_changed()
```

- [ ] **Step 4: Run import test and compile**

Run:

```bash
python -m py_compile views/_judge_mode_dialog.py services/judge_mode_service.py
python -m pytest tests/test_judge_mode_service.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit dialog**

Run:

```bash
git add views/_judge_mode_dialog.py tests/test_judge_mode_service.py
git commit -m "feat: add judge mode dialog"
```

---

## Task 4: Results Wiring

**Files:**
- Modify: `views/results_view.py`
- Modify: `tests/test_judge_mode_service.py`

- [ ] **Step 1: Add Results import guard**

Append to `tests/test_judge_mode_service.py`:

```python
def test_results_view_imports_with_judge_mode():
    from views.results_view import ResultsView

    assert ResultsView.__name__ == "ResultsView"
```

- [ ] **Step 2: Add import and toolbar button**

In `views/results_view.py`, add:

```python
from views._judge_mode_dialog import JudgeModeDialog
```

near the other dialog imports.

In the toolbar after `Clear All Results`, add:

```python
        ctk.CTkButton(toolbar, text="Judge Mode",
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._open_judge_mode).pack(side="right", padx=(4, 4))
```

Add this method near the other dialog openers:

```python
    def _open_judge_mode(self):
        JudgeModeDialog(self, on_changed=self._reload_table)
```

- [ ] **Step 3: Verify focused tests**

Run:

```bash
python -m py_compile views/results_view.py views/_judge_mode_dialog.py services/judge_mode_service.py
python -m pytest tests/test_judge_mode_service.py tests/test_scan_parser_service.py -v
```

Expected: PASS.

- [ ] **Step 4: Commit wiring**

Run:

```bash
git add views/results_view.py tests/test_judge_mode_service.py
git commit -m "feat: launch judge mode from results"
```

---

## Task 5: Docs

**Files:**
- Modify: `README.md`
- Modify: `views/help_view.py`

- [ ] **Step 1: Update README**

In the Results section of `README.md`, add:

```markdown
**Judge Mode:**
- Click `Judge Mode` for a streamlined steward/operator entry screen
- Scan or type an exhibit, confirm the class/exhibitor context, then choose the placing
- Judge Mode keeps recent saves visible and avoids destructive actions like Clear All Results
- Results are still saved on the desktop; scanners only speed up exhibit selection
```

- [ ] **Step 2: Update in-app Help**

In `views/help_view.py`, add a Results topic:

```python
        ("Judge Mode", (
            "Judge Mode is for a steward or operator entering results while a judge works through birds.\n\n"
            "1. Open Results and click Judge Mode\n"
            "2. Optionally enter a class filter\n"
            "3. Scan a ticket QR or type an exhibit number\n"
            "4. Check the resolved exhibit context\n"
            "5. Click the placing or Not Benched\n\n"
            "Judge Mode keeps recent saves visible and returns focus to the scan field after each action. "
            "Normal Results remains available for review, filtering, export, and Clear All Results."
        )),
```

- [ ] **Step 3: Verify docs compile**

Run:

```bash
python -m py_compile views/help_view.py
```

Expected: PASS.

- [ ] **Step 4: Commit docs**

Run:

```bash
git add README.md views/help_view.py
git commit -m "docs: document judge mode"
```

---

## Task 6: Final Verification

**Files:**
- No planned edits

- [ ] **Step 1: Run full tests**

Run:

```bash
python -m pytest tests/ -v --tb=short
```

Expected: PASS.

- [ ] **Step 2: Check status**

Run:

```bash
git status --short --branch
```

Expected: clean working tree.
