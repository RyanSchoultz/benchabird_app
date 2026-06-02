# Group A — New PDF Reports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two new PDF reports to Benchabird — an Exhibitor Entry Confirmation Sheet (pre-show check-in printout, per-exhibitor) and a Results by Exhibitor report (post-judging, per-exhibitor results with specials and prize money).

**Architecture:** Each report is a standalone `generate_X(sd=None) -> bytes` function in its own module under `services/reports/`, following the identical pattern used by all seven existing reports. Both use `new_canvas`, `draw_page_header`, and `draw_footer` from `services/reports/base.py`. A `CTkSwitch` toggle for "Include late entries" is added to `reports_view.py` above the existing button grid; two new buttons join that grid.

**Tech Stack:** Python, ReportLab (PDF), Peewee ORM (SQLite), CustomTkinter (UI), pytest (tests)

**Spec:** `docs/superpowers/specs/2026-06-02-group-a-new-pdf-reports-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `services/reports/entry_confirmation.py` | Create | Generate entry confirmation PDF |
| `services/reports/results_by_exhibitor.py` | Create | Generate results-by-exhibitor PDF |
| `views/reports_view.py` | Modify | Add toggle + 2 new report buttons |
| `tests/test_entry_confirmation_pdf.py` | Create | Tests for entry confirmation |
| `tests/test_results_by_exhibitor_pdf.py` | Create | Tests for results by exhibitor |

---

## Background: Existing Patterns

All tests use an autouse `test_db` fixture from `tests/conftest.py` that binds an in-memory SQLite database to all models:

```python
# tests/conftest.py (already exists — do not modify)
@pytest.fixture(autouse=True)
def test_db():
    db = SqliteDatabase(':memory:')
    with db.bind_ctx(ALL_MODELS):
        db.create_tables(ALL_MODELS)
        yield db
        db.drop_tables(ALL_MODELS)
```

Every report module follows this skeleton (see `services/reports/exhibitor_list.py` for a complete example):

```python
def generate_X(sd=None) -> bytes:
    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "Title", sd)
    # ... draw rows, call c.showPage() on overflow ...
    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()
```

`draw_page_header` returns the y-coordinate of the content start line (below the header rule). `MARGIN`, `PAGE_W`, `ROW_H` are constants from `base.py`.

---

## Task 1: Tests for `entry_confirmation`

**Files:**
- Create: `benchabird_app/tests/test_entry_confirmation_pdf.py`

- [ ] **Step 1: Create the test file**

```python
# tests/test_entry_confirmation_pdf.py
import pytest
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, CalculatedEntry, LateEntry
from models.class_def import ClassDef
from services.reports.entry_confirmation import generate_entry_confirmation


def test_empty_state_returns_valid_pdf(test_db):
    """No exhibitors — still produces a valid PDF without crashing."""
    pdf = generate_entry_confirmation()
    assert pdf[:4] == b'%PDF'


def test_exhibitor_with_no_entries_is_skipped(test_db):
    """An exhibitor with no entries does not crash the generator."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    pdf = generate_entry_confirmation()
    assert pdf[:4] == b'%PDF'


def test_uses_calculated_entry_when_available(test_db):
    """When CalculatedEntry rows exist, ticket numbers come from there."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    CalculatedEntry.create(auto_num=42, exh_no=1, name="Alice", class_code="SC01")
    pdf = generate_entry_confirmation()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 2000


def test_falls_back_to_show_entry_when_not_calculated(test_db):
    """When CalculatedEntry is empty, ShowEntry rows are used instead."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    ShowEntry.create(auto_num=1, exh_no=1, class_code="SC01")
    pdf = generate_entry_confirmation()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 2000


def test_include_late_true_adds_late_entries(test_db):
    """include_late=True produces a larger PDF than include_late=False when late entries exist."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    CalculatedEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC01")
    LateEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC02")
    pdf_with = generate_entry_confirmation(include_late=True)
    pdf_without = generate_entry_confirmation(include_late=False)
    assert pdf_with[:4] == b'%PDF'
    assert pdf_without[:4] == b'%PDF'
    assert len(pdf_with) > len(pdf_without)


def test_multiple_exhibitors_produces_larger_pdf(test_db):
    """Multiple exhibitors each get their own section."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    Exhibitor.create(exh_no=2, name="Bob", town="Durban")
    CalculatedEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC01")
    CalculatedEntry.create(auto_num=2, exh_no=2, name="Bob", class_code="SC02")
    pdf = generate_entry_confirmation()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 3000
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd benchabird_app
pytest tests/test_entry_confirmation_pdf.py -v
```

Expected: `ModuleNotFoundError: No module named 'services.reports.entry_confirmation'`

---

## Task 2: Implement `entry_confirmation.py`

**Files:**
- Create: `benchabird_app/services/reports/entry_confirmation.py`

- [ ] **Step 1: Create the module**

```python
# services/reports/entry_confirmation.py
"""Exhibitor Entry Confirmation Sheet — one section per exhibitor listing their entries."""
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, CalculatedEntry, LateEntry
from models.class_def import ClassDef
from services.reports.base import (
    new_canvas, draw_page_header, draw_footer,
    MARGIN, PAGE_W, ROW_H,
)

_LATE_COLOR = HexColor('#b45309')  # amber

_COL_TICKET = MARGIN
_COL_CLASS  = MARGIN + 22 * mm
_COL_DESC   = MARGIN + 44 * mm


def generate_entry_confirmation(sd=None, include_late: bool = True) -> bytes:
    use_calculated = CalculatedEntry.select().count() > 0

    class_desc = {
        cd.class_code: f"{cd.main_class or ''} {cd.colour or ''}".strip()
        for cd in ClassDef.select()
    }

    exhibitors = list(Exhibitor.select().order_by(Exhibitor.exh_no))

    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "Entry Confirmation", sd)
    first_section = True

    for exh in exhibitors:
        if use_calculated:
            regular = list(
                CalculatedEntry.select()
                .where(CalculatedEntry.exh_no == exh.exh_no)
                .order_by(CalculatedEntry.auto_num)
            )
        else:
            regular = list(
                ShowEntry.select()
                .where(ShowEntry.exh_no == exh.exh_no)
                .order_by(ShowEntry.auto_num)
            )

        late = (
            list(
                LateEntry.select()
                .where(LateEntry.exh_no == exh.exh_no)
                .order_by(LateEntry.auto_num)
            )
            if include_late else []
        )

        if not regular and not late:
            continue

        rows_needed = 4 + len(regular) + len(late)
        if not first_section:
            if y - rows_needed * ROW_H < MARGIN:
                draw_footer(c, page_num)
                c.showPage()
                page_num += 1
                y = draw_page_header(c, "Entry Confirmation", sd)
            else:
                y -= 4
                c.setLineWidth(1.0)
                c.line(MARGIN, y, PAGE_W - MARGIN, y)
                y -= 6

        first_section = False

        # Exhibitor header
        c.setFont("Helvetica-Bold", 10)
        header = f"Exhibitor #{exh.exh_no}  —  {exh.name or ''}"
        if exh.club:
            header += f"  [{exh.club}]"
        c.drawString(MARGIN, y, header)
        y -= ROW_H

        # Contact sub-line
        contact = "  |  ".join(p for p in [exh.cell_no, exh.tel_home] if p)
        if contact:
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(MARGIN, y, contact)
            c.setFillColorRGB(0, 0, 0)
            y -= ROW_H * 0.8

        # Column headers
        c.setLineWidth(0.3)
        c.line(MARGIN, y, PAGE_W - MARGIN, y)
        y -= ROW_H * 0.6
        c.setFont("Helvetica-Bold", 8)
        c.drawString(_COL_TICKET, y, "Ticket #")
        c.drawString(_COL_CLASS, y, "Class")
        c.drawString(_COL_DESC, y, "Description")
        y -= ROW_H

        # Regular entry rows
        for entry in regular:
            if y < MARGIN + ROW_H:
                draw_footer(c, page_num)
                c.showPage()
                page_num += 1
                y = draw_page_header(c, "Entry Confirmation", sd)

            c.setFont("Helvetica", 9)
            ticket = str(entry.auto_num) if use_calculated else "—"
            code = entry.class_code or ""
            desc = class_desc.get(code, "")[:48]
            c.drawString(_COL_TICKET, y, ticket)
            c.drawString(_COL_CLASS, y, code)
            c.drawString(_COL_DESC, y, desc)
            y -= ROW_H

        # Late entry rows
        for entry in late:
            if y < MARGIN + ROW_H:
                draw_footer(c, page_num)
                c.showPage()
                page_num += 1
                y = draw_page_header(c, "Entry Confirmation", sd)

            c.setFont("Helvetica", 9)
            code = entry.class_code or ""
            desc = class_desc.get(code, "")[:48]
            c.drawString(_COL_TICKET, y, "—")
            c.drawString(_COL_CLASS, y, code)
            c.drawString(_COL_DESC, y, desc)
            c.setFillColor(_LATE_COLOR)
            c.drawRightString(PAGE_W - MARGIN, y, "LATE")
            c.setFillColorRGB(0, 0, 0)
            y -= ROW_H

        # Entry count footer
        y -= 2
        c.setLineWidth(0.3)
        c.line(MARGIN, y, PAGE_W - MARGIN, y)
        y -= ROW_H * 0.7
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        parts = [f"{len(regular)} {'entry' if len(regular) == 1 else 'entries'}"]
        if late:
            parts.append(f"{len(late)} late {'entry' if len(late) == 1 else 'entries'}")
        c.drawString(MARGIN, y, "  +  ".join(parts))
        c.setFillColorRGB(0, 0, 0)
        y -= ROW_H * 0.5

    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()
```

- [ ] **Step 2: Run tests**

```bash
cd benchabird_app
pytest tests/test_entry_confirmation_pdf.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 3: Commit**

```bash
cd benchabird_app
git add services/reports/entry_confirmation.py tests/test_entry_confirmation_pdf.py
git commit -m "feat: add entry confirmation PDF report"
```

---

## Task 3: Tests for `results_by_exhibitor`

**Files:**
- Create: `benchabird_app/tests/test_results_by_exhibitor_pdf.py`

- [ ] **Step 1: Create the test file**

```python
# tests/test_results_by_exhibitor_pdf.py
import pytest
from models.exhibitor import Exhibitor
from models.show_entry import CalculatedEntry
from models.results import Result, NotBenched
from models.special import SpecialList, SpecialWinner
from services.reports.results_by_exhibitor import generate_results_by_exhibitor


def test_no_calculated_entries_returns_valid_pdf(test_db):
    """Empty calculated_entry → valid PDF with informational message, no crash."""
    pdf = generate_results_by_exhibitor()
    assert pdf[:4] == b'%PDF'


def test_calculated_entries_but_no_results_returns_valid_pdf(test_db):
    """Entries exist but no results recorded → valid PDF with message."""
    CalculatedEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC01")
    pdf = generate_results_by_exhibitor()
    assert pdf[:4] == b'%PDF'


def test_exhibitor_with_no_results_is_excluded(test_db):
    """An exhibitor whose entries have no result or NB must not appear."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    Exhibitor.create(exh_no=2, name="Bob", town="Durban")
    CalculatedEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC01")
    CalculatedEntry.create(auto_num=2, exh_no=2, name="Bob", class_code="SC02")
    Result.create(exhibit_no=1, result="1st")
    # Bob has no result — only Alice should appear
    pdf = generate_results_by_exhibitor()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 2000


def test_nb_entry_is_included(test_db):
    """Not Benched entry appears even with no result row."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    CalculatedEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC01")
    NotBenched.create(exhibit_no=1)
    pdf = generate_results_by_exhibitor()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 2000


def test_special_prize_increases_pdf_size(test_db):
    """A special prize winner produces a larger PDF than without specials."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    CalculatedEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC01")
    Result.create(exhibit_no=1, result="Champion")
    SpecialList.create(special_nr="SP01", description="Best in Show", cash=100)
    pdf_without = generate_results_by_exhibitor()

    SpecialWinner.create(special_nr="SP01", exhibit_no=1, result="Champion")
    pdf_with = generate_results_by_exhibitor()

    assert pdf_with[:4] == b'%PDF'
    assert len(pdf_with) > len(pdf_without)


def test_zero_cash_prize_produces_valid_pdf(test_db):
    """A special with cash=0 does not crash and still produces a valid PDF."""
    Exhibitor.create(exh_no=1, name="Alice", town="Cape Town")
    CalculatedEntry.create(auto_num=1, exh_no=1, name="Alice", class_code="SC01")
    Result.create(exhibit_no=1, result="Champion")
    SpecialList.create(special_nr="SP01", description="Trophy Only", cash=0)
    SpecialWinner.create(special_nr="SP01", exhibit_no=1, result="Champion")
    pdf = generate_results_by_exhibitor()
    assert pdf[:4] == b'%PDF'
    assert len(pdf) > 2000
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd benchabird_app
pytest tests/test_results_by_exhibitor_pdf.py -v
```

Expected: `ModuleNotFoundError: No module named 'services.reports.results_by_exhibitor'`

---

## Task 4: Implement `results_by_exhibitor.py`

**Files:**
- Create: `benchabird_app/services/reports/results_by_exhibitor.py`

- [ ] **Step 1: Create the module**

```python
# services/reports/results_by_exhibitor.py
"""Results by Exhibitor — all results grouped per exhibitor with specials and prize money."""
from collections import defaultdict
from reportlab.lib.units import mm
from models.show_entry import CalculatedEntry
from services.reports.base import (
    new_canvas, draw_page_header, draw_footer,
    MARGIN, PAGE_W, ROW_H,
)

_COL_TICKET = MARGIN
_COL_CLASS  = MARGIN + 22 * mm
_COL_RESULT = MARGIN + 50 * mm


def generate_results_by_exhibitor(sd=None) -> bytes:
    db = CalculatedEntry._meta.database

    if CalculatedEntry.select().count() == 0:
        buf, c = new_canvas()
        y = draw_page_header(c, "Results by Exhibitor", sd)
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN, y - ROW_H * 2,
                     "No calculated entries found. Run Calculate before generating this report.")
        draw_footer(c, 1)
        c.save()
        return buf.getvalue()

    sql = """
        SELECT ce.exh_no, COALESCE(e.name, ''),
               ce.auto_num,
               COALESCE(ce.class_code, ''),
               COALESCE(r.result, ''),
               CASE WHEN nb.exhibit_no IS NOT NULL THEN 1 ELSE 0 END
        FROM calculated_entry ce
        LEFT JOIN exhibitor e  ON ce.exh_no      = e.exh_no
        LEFT JOIN result r     ON ce.auto_num     = r.exhibit_no
        LEFT JOIN not_benched nb ON ce.auto_num   = nb.exhibit_no
        WHERE r.exhibit_no IS NOT NULL OR nb.exhibit_no IS NOT NULL
        ORDER BY ce.exh_no, ce.auto_num
    """
    rows = db.execute_sql(sql).fetchall()

    if not rows:
        buf, c = new_canvas()
        y = draw_page_header(c, "Results by Exhibitor", sd)
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN, y - ROW_H * 2, "No results recorded yet.")
        draw_footer(c, 1)
        c.save()
        return buf.getvalue()

    exhibitor_rows = defaultdict(list)
    exhibitor_names = {}
    for exh_no, name, ticket_no, class_code, result, is_nb in rows:
        exhibitor_rows[exh_no].append((ticket_no, class_code, result, bool(is_nb)))
        exhibitor_names[exh_no] = name

    specials_sql = """
        SELECT sw.special_nr, COALESCE(sl.description, ''), COALESCE(sl.cash, 0)
        FROM special_winner sw
        JOIN special_list sl ON sw.special_nr = sl.special_nr
        WHERE sw.exhibit_no IN (
            SELECT auto_num FROM calculated_entry WHERE exh_no = ?
        )
    """

    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "Results by Exhibitor", sd)
    first = True

    for exh_no in sorted(exhibitor_rows):
        entries = exhibitor_rows[exh_no]
        name = exhibitor_names[exh_no]
        specials = db.execute_sql(specials_sql, (exh_no,)).fetchall()
        prize_total = sum(cash for _, _, cash in specials)

        rows_needed = 3 + len(entries) + (len(specials) + 1 if specials else 0) + (1 if prize_total > 0 else 0)

        if not first:
            if y - rows_needed * ROW_H < MARGIN:
                draw_footer(c, page_num)
                c.showPage()
                page_num += 1
                y = draw_page_header(c, "Results by Exhibitor", sd)
            else:
                y -= 4
                c.setLineWidth(1.0)
                c.line(MARGIN, y, PAGE_W - MARGIN, y)
                y -= 6
        first = False

        # Exhibitor header
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN, y, f"Exhibitor #{exh_no}  —  {name}")
        y -= ROW_H

        # Column headers
        c.setLineWidth(0.3)
        c.line(MARGIN, y + 2, PAGE_W - MARGIN, y + 2)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(_COL_TICKET, y, "Ticket #")
        c.drawString(_COL_CLASS, y, "Class")
        c.drawString(_COL_RESULT, y, "Result")
        y -= ROW_H

        # Result rows
        for ticket_no, class_code, result, is_nb in entries:
            if y < MARGIN + ROW_H:
                draw_footer(c, page_num)
                c.showPage()
                page_num += 1
                y = draw_page_header(c, "Results by Exhibitor", sd)

            c.setFont("Helvetica", 9)
            c.drawString(_COL_TICKET, y, str(ticket_no))
            c.drawString(_COL_CLASS, y, class_code)

            if is_nb:
                c.setFillColorRGB(0.8, 0.1, 0.1)
                c.drawString(_COL_RESULT, y, "Not Benched")
                c.setFillColorRGB(0, 0, 0)
            else:
                c.drawString(_COL_RESULT, y, result)
            y -= ROW_H

        # Special prizes block
        if specials:
            y -= 2
            c.setFont("Helvetica-Bold", 8)
            c.drawString(MARGIN, y, "Special prizes:")
            y -= ROW_H
            for _, desc, _ in specials:
                if y < MARGIN + ROW_H:
                    draw_footer(c, page_num)
                    c.showPage()
                    page_num += 1
                    y = draw_page_header(c, "Results by Exhibitor", sd)
                c.setFont("Helvetica", 9)
                c.drawString(MARGIN + 6 * mm, y, desc[:60])
                y -= ROW_H

        # Prize money line
        if prize_total > 0:
            c.setFont("Helvetica-Bold", 9)
            c.drawString(MARGIN, y, f"Prize money: R {prize_total}")
            y -= ROW_H

    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()
```

- [ ] **Step 2: Run tests**

```bash
cd benchabird_app
pytest tests/test_results_by_exhibitor_pdf.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 3: Commit**

```bash
cd benchabird_app
git add services/reports/results_by_exhibitor.py tests/test_results_by_exhibitor_pdf.py
git commit -m "feat: add results-by-exhibitor PDF report"
```

---

## Task 5: Wire up `reports_view.py`

**Files:**
- Modify: `benchabird_app/views/reports_view.py`

The current file has `reports_view.py` with 7 report buttons in a 3-column grid and a status label. We add a `CTkSwitch` for the late-entries toggle above the grid, then append 2 new buttons to the reports list (giving 9 buttons — a clean 3×3 grid).

- [ ] **Step 1: Replace `reports_view.py` with the updated version**

```python
# views/reports_view.py
import threading
import customtkinter as ctk
from models.reference import ShowDetails


class ReportsView(ctk.CTkFrame):
    """Generate and open PDF reports."""

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._include_late = ctk.BooleanVar(value=True)
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Reports",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 4)
        )

        self._status = ctk.CTkLabel(self, text="",
                                    font=ctk.CTkFont(size=11),
                                    text_color=("gray40", "gray60"))
        self._status.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))

        # Late entries toggle (affects Entry Confirmation only)
        toggle_frame = ctk.CTkFrame(self, fg_color="transparent")
        toggle_frame.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))
        ctk.CTkSwitch(
            toggle_frame,
            text="Include late entries",
            variable=self._include_late,
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=0)

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.grid(row=3, column=0, padx=16)

        reports = [
            ("Entries Received",       "benchabird_entries_received.pdf",       self._gen_entries_received),
            ("Show Catalogue",         "benchabird_show_catalogue.pdf",         self._gen_show_catalogue),
            ("Results Sheet",          "benchabird_results_sheet.pdf",          self._gen_results_sheet),
            ("Special Winners",        "benchabird_special_winners.pdf",        self._gen_special_winners),
            ("Prize Money",            "benchabird_prize_money.pdf",            self._gen_prize_money),
            ("Address Tags",           "benchabird_address_tags.pdf",           self._gen_address_tags),
            ("Exhibitor List",         "benchabird_exhibitor_list.pdf",         self._gen_exhibitor_list),
            ("Entry Confirmation",     "benchabird_entry_confirmation.pdf",     self._gen_entry_confirmation),
            ("Results by Exhibitor",   "benchabird_results_by_exhibitor.pdf",   self._gen_results_by_exhibitor),
        ]

        for i, (label, _, cmd) in enumerate(reports):
            row, col = divmod(i, 3)
            ctk.CTkButton(
                grid, text=label, width=190, height=52,
                command=cmd,
            ).grid(row=row, column=col, padx=8, pady=8)

        self._reports = reports

    def _get_sd(self):
        return ShowDetails.select().first()

    def _save_and_open(self, gen_fn, default_name: str):
        self._status.configure(text=f"Generating {default_name}…")
        sd = self._get_sd()

        def run():
            try:
                pdf_bytes = gen_fn(sd=sd)
                self.after(0, lambda: self._show_preview(pdf_bytes, default_name))
            except Exception as e:
                self.after(0, lambda: self._on_error(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _show_preview(self, pdf_bytes: bytes, default_name: str):
        self._status.configure(text="")
        from views.pdf_preview_window import PDFPreviewWindow
        title = default_name.replace("benchabird_", "").replace(".pdf", "").replace("_", " ").title()
        PDFPreviewWindow(self, pdf_bytes, title, default_name)

    def _on_error(self, msg: str):
        self._status.configure(text=f"Error: {msg[:80]}")

    def _gen_entries_received(self):
        from services.reports.entries_received import generate_entries_received
        self._save_and_open(generate_entries_received, "benchabird_entries_received.pdf")

    def _gen_show_catalogue(self):
        from services.reports.show_catalogue import generate_show_catalogue
        self._save_and_open(generate_show_catalogue, "benchabird_show_catalogue.pdf")

    def _gen_results_sheet(self):
        from services.reports.results_sheet import generate_results_sheet
        self._save_and_open(generate_results_sheet, "benchabird_results_sheet.pdf")

    def _gen_special_winners(self):
        from services.reports.special_winners import generate_special_winners
        self._save_and_open(generate_special_winners, "benchabird_special_winners.pdf")

    def _gen_prize_money(self):
        from services.reports.prize_money import generate_prize_money
        self._save_and_open(generate_prize_money, "benchabird_prize_money.pdf")

    def _gen_address_tags(self):
        from services.reports.address_tags import generate_address_tags
        self._save_and_open(generate_address_tags, "benchabird_address_tags.pdf")

    def _gen_exhibitor_list(self):
        from services.reports.exhibitor_list import generate_exhibitor_list
        self._save_and_open(generate_exhibitor_list, "benchabird_exhibitor_list.pdf")

    def _gen_entry_confirmation(self):
        from services.reports.entry_confirmation import generate_entry_confirmation
        include_late = self._include_late.get()
        gen_fn = lambda sd: generate_entry_confirmation(sd=sd, include_late=include_late)
        self._save_and_open(gen_fn, "benchabird_entry_confirmation.pdf")

    def _gen_results_by_exhibitor(self):
        from services.reports.results_by_exhibitor import generate_results_by_exhibitor
        self._save_and_open(generate_results_by_exhibitor, "benchabird_results_by_exhibitor.pdf")
```

- [ ] **Step 2: Run the full test suite**

```bash
cd benchabird_app
pytest tests/ -v
```

Expected: All tests pass. No regressions.

- [ ] **Step 3: Commit**

```bash
cd benchabird_app
git add views/reports_view.py
git commit -m "feat: wire entry confirmation and results-by-exhibitor into reports view"
```

---

## Task 6: Full run and smoke test

- [ ] **Step 1: Run all tests one final time**

```bash
cd benchabird_app
pytest tests/ -v --tb=short
```

Expected: All tests PASS. Note total count — should be previous count + 12 new tests.

- [ ] **Step 2: Launch the app and verify manually**

```bash
cd benchabird_app
python main.py
```

Navigate to **Reports**. Verify:
- The "Include late entries" toggle appears above the button grid
- "Entry Confirmation" and "Results by Exhibitor" buttons appear as the 8th and 9th buttons (completing a 3×3 grid)
- Clicking "Entry Confirmation" generates a PDF preview (even with no data — should open without crashing)
- Clicking "Results by Exhibitor" generates a PDF preview (should show the "Run Calculate first" message if no calculated entries)
- Toggle the switch OFF and regenerate Entry Confirmation — late entries should be excluded

- [ ] **Step 3: Push to GitHub**

```bash
cd benchabird_app
git push origin main
```
