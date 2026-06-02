# Exhibitor Bundle QOL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Reports workflow that generates a one-exhibitor PDF bundle containing exhibition paperwork and related show information.

**Architecture:** Add a focused report service that loads one exhibitor, their entries, tickets, late entries, results, NB state, and address-label flag, then renders one PDF with clear sections. Add a searchable selector dialog launched from Reports and preview the generated PDF with the existing PDF preview window.

**Tech Stack:** Python, Peewee, ReportLab, CustomTkinter, pytest

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `tests/test_exhibitor_bundle_pdf.py` | Create | PDF service tests for empty, entries, late entries, results, address label, missing exhibitor |
| `services/reports/exhibitor_bundle.py` | Create | Generate one-exhibitor bundle PDFs |
| `views/_exhibitor_bundle_dialog.py` | Create | Search/select exhibitor and trigger bundle generation |
| `views/reports_view.py` | Modify | Add `Exhibitor Bundle` report button |
| `views/help_view.py` | Modify | Document bundle workflow |
| `README.md` | Modify | Document bundle workflow |

---

## Task 1: RED Bundle Service Tests

**Files:**
- Create: `tests/test_exhibitor_bundle_pdf.py`

- [ ] **Step 1: Add failing tests**

Create `tests/test_exhibitor_bundle_pdf.py`:

```python
import pytest

from models.exhibitor import Exhibitor
from models.results import Result
from models.show_entry import CalculatedEntry, LateEntry, ShowEntry
from services.reports.exhibitor_bundle import (
    ExhibitorBundleError,
    generate_exhibitor_bundle,
)


def test_missing_exhibitor_raises_clear_error(test_db):
    with pytest.raises(ExhibitorBundleError, match="No exhibitor"):
        generate_exhibitor_bundle(99)


def test_no_entry_exhibitor_returns_valid_pdf(test_db):
    Exhibitor.create(exh_no=7, name="Alice Bird", email="alice@example.test")

    pdf = generate_exhibitor_bundle(7)

    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000


def test_bundle_includes_calculated_entries(test_db):
    Exhibitor.create(exh_no=7, name="Alice Bird")
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")

    pdf = generate_exhibitor_bundle(7)

    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1500


def test_bundle_falls_back_to_raw_entries_before_calculate(test_db):
    Exhibitor.create(exh_no=7, name="Alice Bird")
    ShowEntry.create(auto_num=5, exh_no=7, class_code="A1")

    pdf = generate_exhibitor_bundle(7)

    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1200


def test_bundle_grows_with_late_entries(test_db):
    Exhibitor.create(exh_no=7, name="Alice Bird")
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")
    LateEntry.create(auto_num=77, exh_no=7, name="Alice Bird", class_code="L1")

    without_late = generate_exhibitor_bundle(7, include_late=False)
    with_late = generate_exhibitor_bundle(7, include_late=True)

    assert len(with_late) > len(without_late)


def test_bundle_grows_with_results(test_db):
    Exhibitor.create(exh_no=7, name="Alice Bird")
    CalculatedEntry.create(auto_num=42, exh_no=7, name="Alice Bird", class_code="A1")
    Result.create(exhibit_no=42, result="1st")

    without_results = generate_exhibitor_bundle(7, include_results=False)
    with_results = generate_exhibitor_bundle(7, include_results=True)

    assert len(with_results) > len(without_results)


def test_bundle_grows_with_address_label_when_flagged(test_db):
    Exhibitor.create(
        exh_no=7,
        name="Alice Bird",
        address="1 Main Road",
        town="Cape Town",
        zip_code="8000",
        print_address=True,
    )

    without_label = generate_exhibitor_bundle(7, include_address_label=False)
    with_label = generate_exhibitor_bundle(7, include_address_label=True)

    assert len(with_label) > len(without_label)
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_exhibitor_bundle_pdf.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'services.reports.exhibitor_bundle'`.

- [ ] **Step 3: Commit RED tests**

Run:

```bash
git add tests/test_exhibitor_bundle_pdf.py
git commit -m "test: add exhibitor bundle pdf coverage"
```

---

## Task 2: Bundle PDF Service

**Files:**
- Create: `services/reports/exhibitor_bundle.py`
- Test: `tests/test_exhibitor_bundle_pdf.py`

- [ ] **Step 1: Implement service skeleton and data loading**

Create `services/reports/exhibitor_bundle.py`:

```python
"""Generate one-exhibitor document bundles."""

from __future__ import annotations

from dataclasses import dataclass

from models.exhibitor import Exhibitor
from models.results import NotBenched, Result
from models.show_entry import CalculatedEntry, LateEntry, ShowEntry
from services.reports.base import (
    MARGIN,
    PAGE_H,
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


def _exhibitor_or_error(exh_no: int) -> Exhibitor:
    exhibitor = Exhibitor.get_or_none(Exhibitor.exh_no == exh_no)
    if exhibitor is None:
        raise ExhibitorBundleError(f"No exhibitor found for #{exh_no}.")
    return exhibitor


def _regular_entries(exh_no: int) -> list[BundleEntry]:
    ticket_by_auto = {
        row["auto_num"]: row["ticket_no"]
        for row in get_ticket_assignments()
        if row["exh_no"] == exh_no
    }
    calculated = list(
        CalculatedEntry.select()
        .where(CalculatedEntry.exh_no == exh_no)
        .order_by(CalculatedEntry.auto_num)
    )
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
    raw = list(
        ShowEntry.select()
        .where(ShowEntry.exh_no == exh_no)
        .order_by(ShowEntry.auto_num)
    )
    return [
        BundleEntry(
            ticket_no=None,
            auto_num=entry.auto_num,
            class_code=entry.class_code,
            source="Raw",
        )
        for entry in raw
    ]


def _late_entries(exh_no: int) -> list[BundleEntry]:
    return [
        BundleEntry(
            ticket_no=None,
            auto_num=entry.auto_num,
            class_code=entry.class_code,
            source="Late",
        )
        for entry in LateEntry.select()
        .where(LateEntry.exh_no == exh_no)
        .order_by(LateEntry.auto_num)
    ]
```

- [ ] **Step 2: Add drawing helpers**

Append:

```python
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
```

- [ ] **Step 3: Add generator**

Append:

```python
def generate_exhibitor_bundle(
    exh_no: int,
    sd=None,
    include_tickets: bool = True,
    include_late: bool = True,
    include_results: bool = True,
    include_address_label: bool = True,
) -> bytes:
    exhibitor = _exhibitor_or_error(exh_no)
    regular = _regular_entries(exh_no)
    late = _late_entries(exh_no) if include_late else []

    result_by_auto = {
        row.exhibit_no: row.result
        for row in Result.select().where(Result.result.is_null(False))
    }
    nb_set = {row.exhibit_no for row in NotBenched.select()}

    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, f"Exhibitor Bundle #{exh_no}", sd)

    y = _section(c, y, "Exhibitor Summary")
    y = _line(c, y, f"Name: {exhibitor.name or ''}", "Helvetica-Bold", 10)
    y = _line(c, y, f"Exhibitor #: {exhibitor.exh_no or ''}")
    y = _line(c, y, f"Club: {exhibitor.club or ''}")
    y = _line(c, y, f"Phone: {exhibitor.cell_no or exhibitor.tel_home or ''}")
    y = _line(c, y, f"Email: {exhibitor.email or ''}")

    y = _draw_entries(
        c,
        y,
        "Entry Confirmation",
        regular if include_tickets else [
            BundleEntry(None, e.auto_num, e.class_code, e.source) for e in regular
        ],
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

    if y < MARGIN + ROW_H:
        draw_footer(c, page_num)
        c.showPage()
        page_num += 1
        y = draw_page_header(c, f"Exhibitor Bundle #{exh_no}", sd)
    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
python -m pytest tests/test_exhibitor_bundle_pdf.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit service**

Run:

```bash
git add services/reports/exhibitor_bundle.py tests/test_exhibitor_bundle_pdf.py
git commit -m "feat: add exhibitor bundle pdf"
```

---

## Task 3: Exhibitor Bundle Selector Dialog

**Files:**
- Create: `views/_exhibitor_bundle_dialog.py`
- Modify: `tests/test_exhibitor_bundle_pdf.py`

- [ ] **Step 1: Add dialog import smoke test**

Append to `tests/test_exhibitor_bundle_pdf.py`:

```python
def test_exhibitor_bundle_dialog_imports():
    from views._exhibitor_bundle_dialog import ExhibitorBundleDialog

    assert ExhibitorBundleDialog.__name__ == "ExhibitorBundleDialog"
```

- [ ] **Step 2: Verify RED**

Run:

```bash
python -m pytest tests/test_exhibitor_bundle_pdf.py::test_exhibitor_bundle_dialog_imports -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'views._exhibitor_bundle_dialog'`.

- [ ] **Step 3: Create dialog**

Create `views/_exhibitor_bundle_dialog.py`:

```python
import threading

import customtkinter as ctk

from models.exhibitor import Exhibitor
from services.reports.exhibitor_bundle import (
    ExhibitorBundleError,
    generate_exhibitor_bundle,
)


class ExhibitorBundleDialog(ctk.CTkToplevel):
    def __init__(self, parent, sd, on_pdf):
        super().__init__(parent)
        self._sd = sd
        self._on_pdf = on_pdf
        self._selected_exh_no = None
        self.title("Exhibitor Bundle")
        self.geometry("640x520")
        self.minsize(520, 420)
        self._build()
        self._load()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(
            self,
            text="Print Exhibitor Bundle",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._load())
        ctk.CTkEntry(
            self,
            textvariable=self._search_var,
            placeholder_text="Search by exhibitor number, name, email, or club",
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=8)

        self._list = ctk.CTkScrollableFrame(self)
        self._list.grid(row=2, column=0, sticky="nsew", padx=16, pady=8)
        self._list.grid_columnconfigure(0, weight=1)

        options = ctk.CTkFrame(self, fg_color="transparent")
        options.grid(row=3, column=0, sticky="ew", padx=16, pady=4)
        self._include_tickets = ctk.BooleanVar(value=True)
        self._include_late = ctk.BooleanVar(value=True)
        self._include_results = ctk.BooleanVar(value=True)
        self._include_address = ctk.BooleanVar(value=True)
        for text, var in [
            ("Tickets", self._include_tickets),
            ("Late entries", self._include_late),
            ("Results", self._include_results),
            ("Address label", self._include_address),
        ]:
            ctk.CTkCheckBox(options, text=text, variable=var).pack(side="left", padx=6)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=4, column=0, sticky="ew", padx=16, pady=(4, 16))
        self._status = ctk.CTkLabel(bottom, text="", font=ctk.CTkFont(size=11))
        self._status.pack(side="left")
        self._generate_btn = ctk.CTkButton(
            bottom,
            text="Generate Bundle",
            state="disabled",
            command=self._generate,
        )
        self._generate_btn.pack(side="right")

    def _load(self):
        for child in self._list.winfo_children():
            child.destroy()
        q = self._search_var.get().strip().lower()
        rows = list(Exhibitor.select().order_by(Exhibitor.exh_no))
        if q:
            rows = [
                e for e in rows
                if q in str(e.exh_no or "").lower()
                or q in (e.name or "").lower()
                or q in (e.email or "").lower()
                or q in (e.club or "").lower()
            ]
        if not rows:
            ctk.CTkLabel(self._list, text="No matching exhibitors.").grid(
                row=0, column=0, sticky="w", padx=8, pady=8
            )
            return
        for index, exhibitor in enumerate(rows[:100]):
            label = f"#{exhibitor.exh_no or ''}  {exhibitor.name or ''}  {exhibitor.club or ''}"
            ctk.CTkButton(
                self._list,
                text=label,
                anchor="w",
                fg_color=("gray85", "gray25"),
                text_color=("gray10", "gray90"),
                command=lambda exh_no=exhibitor.exh_no: self._select(exh_no),
            ).grid(row=index, column=0, sticky="ew", padx=4, pady=3)

    def _select(self, exh_no):
        self._selected_exh_no = exh_no
        self._status.configure(text=f"Selected exhibitor #{exh_no}")
        self._generate_btn.configure(state="normal")

    def _generate(self):
        if self._selected_exh_no is None:
            return
        self._generate_btn.configure(state="disabled", text="Generating...")

        def run():
            try:
                pdf = generate_exhibitor_bundle(
                    self._selected_exh_no,
                    sd=self._sd,
                    include_tickets=self._include_tickets.get(),
                    include_late=self._include_late.get(),
                    include_results=self._include_results.get(),
                    include_address_label=self._include_address.get(),
                )
                self.after(0, lambda: self._done(pdf))
            except ExhibitorBundleError as exc:
                self.after(0, lambda: self._error(str(exc)))

        threading.Thread(target=run, daemon=True).start()

    def _done(self, pdf):
        self._generate_btn.configure(state="normal", text="Generate Bundle")
        self._on_pdf(pdf, f"benchabird_exhibitor_{self._selected_exh_no}_bundle.pdf")
        self.destroy()

    def _error(self, message):
        self._generate_btn.configure(state="normal", text="Generate Bundle")
        self._status.configure(text=message[:90])
```

- [ ] **Step 4: Run import test and compile**

Run:

```bash
python -m py_compile views/_exhibitor_bundle_dialog.py services/reports/exhibitor_bundle.py
python -m pytest tests/test_exhibitor_bundle_pdf.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit dialog**

Run:

```bash
git add views/_exhibitor_bundle_dialog.py tests/test_exhibitor_bundle_pdf.py
git commit -m "feat: add exhibitor bundle selector"
```

---

## Task 4: Reports Wiring

**Files:**
- Modify: `views/reports_view.py`
- Modify: `tests/test_exhibitor_bundle_pdf.py`

- [ ] **Step 1: Add Reports import smoke test**

Append to `tests/test_exhibitor_bundle_pdf.py`:

```python
def test_reports_view_imports_with_exhibitor_bundle():
    from views.reports_view import ReportsView

    assert ReportsView.__name__ == "ReportsView"
```

- [ ] **Step 2: Wire Reports button**

In `views/reports_view.py`, add:

```python
from views._exhibitor_bundle_dialog import ExhibitorBundleDialog
```

near the other imports.

Add to the `reports` list:

```python
            ("Exhibitor Bundle", "benchabird_exhibitor_bundle.pdf", self._gen_exhibitor_bundle),
```

Add this method:

```python
    def _gen_exhibitor_bundle(self):
        ExhibitorBundleDialog(self, self._get_sd(), self._show_preview)
```

- [ ] **Step 3: Verify focused tests**

Run:

```bash
python -m py_compile views/reports_view.py views/_exhibitor_bundle_dialog.py services/reports/exhibitor_bundle.py
python -m pytest tests/test_exhibitor_bundle_pdf.py -v
```

Expected: PASS.

- [ ] **Step 4: Commit wiring**

Run:

```bash
git add views/reports_view.py tests/test_exhibitor_bundle_pdf.py
git commit -m "feat: add exhibitor bundle report action"
```

---

## Task 5: Docs

**Files:**
- Modify: `README.md`
- Modify: `views/help_view.py`

- [ ] **Step 1: Update README**

Add to the Reports or Exhibitors guide:

```markdown
**Exhibitor Bundle:** click `Exhibitor Bundle` in Reports, search for an exhibitor, choose bundle sections, then preview/print one PDF containing that exhibitor's summary, entries, tickets when calculated, late entries, results when recorded, and address label when flagged.
```

- [ ] **Step 2: Update in-app Help**

In `views/help_view.py`, add a Tickets & Reports topic:

```python
        ("Exhibitor Bundle", (
            "Use Exhibitor Bundle when you need one exhibitor's paperwork in a single PDF.\n\n"
            "1. Go to Reports\n"
            "2. Click Exhibitor Bundle\n"
            "3. Search by exhibitor number, name, email, or club\n"
            "4. Select the exhibitor and choose the bundle sections\n"
            "5. Preview, print, or save the generated PDF\n\n"
            "Bundles can include exhibitor details, entries, cage tickets after Calculate, late entries, "
            "results when recorded, and an address label when the exhibitor is flagged for labels."
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
git commit -m "docs: document exhibitor bundles"
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

