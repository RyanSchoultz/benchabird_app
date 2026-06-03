# Entrant Flag & Entries Submitted Report — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an `is_entrant` boolean flag to Exhibitor with a toggle in the Exhibitors page, filter the Enrol dialog to show only flagged exhibitors, and create a pre-show "Entries Submitted" PDF report with summary, by-class, and by-exhibitor sections.

**Architecture:** `is_entrant` is a per-show boolean on the `Exhibitor` model, reset alongside `exh_no` at season end. The flag gates the Enrol dialog and feeds the new `entries_submitted.py` report service which reads from `ShowEntry` (not `CalculatedEntry`). All new UI follows existing patterns: Toggle Labels → Toggle Entrant; entries_received.py → entries_submitted.py.

**Tech Stack:** Python 3.14, peewee ORM, customtkinter, ReportLab, pytest (in-memory SQLite)

---

## File Map

| Action | File |
|---|---|
| Modify | `models/exhibitor.py` |
| Modify | `main.py` |
| Modify | `services/reset_service.py` |
| Modify | `services/show_participants_service.py` |
| Modify | `views/_enrol_dialog.py` |
| Modify | `views/exhibitors_view.py` |
| Create | `services/reports/entries_submitted.py` |
| Modify | `views/reports_view.py` |
| Modify | `tests/test_models.py` |
| Modify | `tests/test_reset_service.py` |
| Modify | `tests/test_show_participants_service.py` |

---

## Task 1: Add `is_entrant` field to Exhibitor + migration

**Files:**
- Modify: `models/exhibitor.py`
- Modify: `main.py`
- Modify: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_models.py`:

```python
def test_exhibitor_has_is_entrant_field(test_db):
    from models.exhibitor import Exhibitor
    e = Exhibitor.create(name="Test Person")
    assert e.is_entrant is False
    e.is_entrant = True
    e.save()
    assert Exhibitor.get_by_id(e.id).is_entrant is True
```

- [ ] **Step 2: Run to verify it fails**

```
cd benchabird_app
pytest tests/test_models.py::test_exhibitor_has_is_entrant_field -v
```

Expected: `FAILED` — `Exhibitor has no field is_entrant`

- [ ] **Step 3: Add the field to `models/exhibitor.py`**

Add after `print_address`:

```python
class Exhibitor(BaseModel):
    exh_no = IntegerField(null=True, index=True)
    name = CharField(max_length=75, unique=True)
    address = CharField(max_length=100, null=True)
    suburb = CharField(max_length=50, null=True)
    town = CharField(max_length=50, null=True)
    zip_code = CharField(max_length=10, null=True)
    tel_home = CharField(max_length=50, null=True)
    tel_work = CharField(max_length=50, null=True)
    cell_no = CharField(max_length=50, null=True)
    fax_no = CharField(max_length=50, null=True)
    email = CharField(max_length=100, null=True)
    club = CharField(max_length=50, null=True)
    club1 = CharField(max_length=255, null=True)
    print_address = BooleanField(default=False)
    is_entrant = BooleanField(default=False)

    class Meta:
        table_name = 'exhibitor'
```

- [ ] **Step 4: Add migration to `main.py`**

In `_migrate_db()`, append to the sql list:

```python
"ALTER TABLE exhibitor ADD COLUMN is_entrant BOOLEAN DEFAULT 0",
```

- [ ] **Step 5: Run to verify it passes**

```
pytest tests/test_models.py::test_exhibitor_has_is_entrant_field -v
```

Expected: `PASSED`

- [ ] **Step 6: Run full suite**

```
pytest tests/ -q --tb=short
```

Expected: all pass

- [ ] **Step 7: Commit**

```bash
git add models/exhibitor.py main.py tests/test_models.py
git commit -m "feat: add is_entrant field to Exhibitor model"
```

---

## Task 2: Reset show data clears `is_entrant`

**Files:**
- Modify: `services/reset_service.py`
- Modify: `tests/test_reset_service.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_reset_service.py`:

```python
def test_reset_clears_is_entrant(test_db):
    from services.reset_service import reset_show_data
    Exhibitor.create(name="Flagged Person", is_entrant=True)
    Exhibitor.create(name="Unflagged Person", is_entrant=False)
    reset_show_data()
    assert all(not e.is_entrant for e in Exhibitor.select())


def test_reset_returns_entrants_cleared_count(test_db):
    from services.reset_service import reset_show_data
    Exhibitor.create(name="A", is_entrant=True)
    Exhibitor.create(name="B", is_entrant=True)
    Exhibitor.create(name="C", is_entrant=False)
    counts = reset_show_data()
    assert counts['entrants_cleared'] == 2
    assert 'entrants_cleared' in counts
```

- [ ] **Step 2: Run to verify they fail**

```
pytest tests/test_reset_service.py::test_reset_clears_is_entrant -v
```

Expected: `FAILED` — KeyError or assertion error

- [ ] **Step 3: Update `services/reset_service.py`**

Replace the full file:

```python
# services/reset_service.py
"""Clear all show-year data without touching reference tables."""
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry, CalculatedEntry, LateEntry
from models.results import Result, NotBenched
from models.special import SpecialWinner


def reset_show_data() -> dict:
    """
    Delete all entries, results, and special winners.
    Clears ExhNo and is_entrant from all exhibitors — both are per-show.
    Returns dict of table -> row count affected.
    Class defs, hall of fame, and brochure notes are NOT affected.
    """
    with ShowEntry._meta.database.atomic():
        return {
            'entries':          ShowEntry.delete().execute(),
            'calculated':       CalculatedEntry.delete().execute(),
            'late_entries':     LateEntry.delete().execute(),
            'results':          Result.delete().execute(),
            'not_benched':      NotBenched.delete().execute(),
            'special_winners':  SpecialWinner.delete().execute(),
            'exh_nos_cleared':  Exhibitor.update(exh_no=None).where(
                Exhibitor.exh_no.is_null(False)
            ).execute(),
            'entrants_cleared': Exhibitor.update(is_entrant=False).where(
                Exhibitor.is_entrant == True
            ).execute(),
        }
```

- [ ] **Step 4: Run to verify they pass**

```
pytest tests/test_reset_service.py -v
```

Expected: all pass

- [ ] **Step 5: Run full suite**

```
pytest tests/ -q --tb=short
```

- [ ] **Step 6: Commit**

```bash
git add services/reset_service.py tests/test_reset_service.py
git commit -m "feat: reset show data now also clears is_entrant flag"
```

---

## Task 3: `get_unenrolled_exhibitors` — add `flagged_only` param

**Files:**
- Modify: `services/show_participants_service.py`
- Modify: `tests/test_show_participants_service.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_show_participants_service.py`:

```python
def test_get_unenrolled_exhibitors_flagged_only_excludes_unflagged(test_db):
    from services.show_participants_service import get_unenrolled_exhibitors
    Exhibitor.create(exh_no=None, name="Flagged", is_entrant=True)
    Exhibitor.create(exh_no=None, name="Unflagged", is_entrant=False)
    results = get_unenrolled_exhibitors(flagged_only=True)
    assert len(results) == 1
    assert results[0].name == "Flagged"


def test_get_unenrolled_exhibitors_flagged_only_false_returns_all(test_db):
    from services.show_participants_service import get_unenrolled_exhibitors
    Exhibitor.create(exh_no=None, name="Flagged", is_entrant=True)
    Exhibitor.create(exh_no=None, name="Unflagged", is_entrant=False)
    results = get_unenrolled_exhibitors(flagged_only=False)
    assert len(results) == 2
```

- [ ] **Step 2: Run to verify they fail**

```
pytest tests/test_show_participants_service.py::test_get_unenrolled_exhibitors_flagged_only_excludes_unflagged -v
```

Expected: `FAILED` — unexpected keyword argument `flagged_only`

- [ ] **Step 3: Update `get_unenrolled_exhibitors` in `services/show_participants_service.py`**

Replace the existing function:

```python
def get_unenrolled_exhibitors(query: str = "", flagged_only: bool = False) -> list[Exhibitor]:
    """All exhibitors with no ExhNo assigned, optionally filtered by name or entrant flag."""
    q = (query or "").strip()
    base = Exhibitor.select().where(Exhibitor.exh_no.is_null(True))
    if flagged_only:
        base = base.where(Exhibitor.is_entrant == True)
    if q:
        base = base.where(Exhibitor.name.contains(q))
    return list(base.order_by(Exhibitor.name))
```

- [ ] **Step 4: Run to verify they pass**

```
pytest tests/test_show_participants_service.py -v
```

Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add services/show_participants_service.py tests/test_show_participants_service.py
git commit -m "feat: get_unenrolled_exhibitors supports flagged_only param"
```

---

## Task 4: Update `_enrol_dialog.py` — show only flagged entrants

**Files:**
- Modify: `views/_enrol_dialog.py`

- [ ] **Step 1: Update `_load()` in `views/_enrol_dialog.py`**

Replace the `_load` method:

```python
    def _load(self):
        self._all_exhibitors = get_unenrolled_exhibitors(flagged_only=True)
        self._vars = {e.id: ctk.BooleanVar(value=False) for e in self._all_exhibitors}
        self._apply_filter()
```

Also update the dialog title in `__init__`:

```python
        self.title("Enrol Exhibitors for This Show")
```

And update `_count_lbl` text in `_apply_filter()` to make it clear this is filtered:

```python
        total_left = len(self._all_exhibitors)
        self._count_lbl.configure(
            text=f"{total_left} flagged entrant{'s' if total_left != 1 else ''}"
        )
```

- [ ] **Step 2: Run full suite to verify no regressions**

```
pytest tests/ -q --tb=short
```

Expected: all pass

- [ ] **Step 3: Commit**

```bash
git add views/_enrol_dialog.py
git commit -m "feat: enrol dialog now shows only flagged entrants"
```

---

## Task 5: Exhibitors page — Toggle Entrant button + Entrant column

**Files:**
- Modify: `views/exhibitors_view.py`

- [ ] **Step 1: Add Entrant column to table headers in `_build()`**

Replace the PaginatedTable instantiation:

```python
        self._table = PaginatedTable(
            self,
            headers=["Exh #", "Name", "Town", "Phone", "Email", "Labels", "Entrant"],
            col_weights=[1, 2, 1, 1, 2, 1, 1],
            on_select=self._select,
        )
```

- [ ] **Step 2: Add Toggle Entrant button to toolbar in `_build()`**

Add after the Toggle Labels button (keeping the same side="right" packing order):

```python
        ctk.CTkButton(toolbar, text="Toggle Entrant", width=120,
                      fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
                      command=self._toggle_entrant).pack(side="right", padx=4)
```

- [ ] **Step 3: Update `_load()` to include Entrant cell**

Replace the data list comprehension in `_load()`:

```python
        data = [
            (e.id, [
                str(e.exh_no or ""), e.name or "", e.town or "",
                e.tel_home or e.cell_no or "", e.email or "",
                "✓" if e.print_address else "",
                "✓" if e.is_entrant else "",
            ])
            for e in exhibitors
        ]
```

- [ ] **Step 4: Add `_toggle_entrant()` method**

Add after `_toggle_labels()`:

```python
    def _toggle_entrant(self):
        if not self._selected_pk:
            return
        exhibitor = _repo.get_by_id(self._selected_pk)
        if exhibitor:
            _repo.update(exhibitor, is_entrant=not exhibitor.is_entrant)
        self._load()
```

- [ ] **Step 5: Update `_export()` to include is_entrant**

Replace the export rows and headers:

```python
    def _export(self):
        from services.export_service import export_data
        exhibitors = search(self._search_var.get())
        rows = [
            [str(e.exh_no or ""), e.name or "", e.address or "", e.suburb or "",
             e.town or "", e.zip_code or "", e.tel_home or "", e.cell_no or "",
             e.email or "", e.club or "",
             "Yes" if e.print_address else "No",
             "Yes" if e.is_entrant else "No"]
            for e in exhibitors
        ]
        headers = ["ExhNo", "Name", "Address", "Suburb", "Town", "ZipCode",
                   "TelHome", "Cell", "Email", "Club", "PrintAddress", "IsEntrant"]
        export_data(rows, headers, "exhibitors.csv")
```

- [ ] **Step 6: Run full suite**

```
pytest tests/ -q --tb=short
```

Expected: all pass

- [ ] **Step 7: Commit**

```bash
git add views/exhibitors_view.py
git commit -m "feat: exhibitors page adds Toggle Entrant button and Entrant column"
```

---

## Task 6: Create `entries_submitted.py` report

**Files:**
- Create: `services/reports/entries_submitted.py`

- [ ] **Step 1: Write the smoke test**

Append to an existing import test file. Add to `tests/test_entries_received_pdf.py` (or create a new file `tests/test_entries_submitted_pdf.py`):

Create `tests/test_entries_submitted_pdf.py`:

```python
from models.exhibitor import Exhibitor
from models.show_entry import ShowEntry
from models.class_def import ClassDef


def test_entries_submitted_generates_pdf_with_no_data(test_db):
    from services.reports.entries_submitted import generate_entries_submitted
    pdf = generate_entries_submitted()
    assert isinstance(pdf, bytes)
    assert len(pdf) > 0


def test_entries_submitted_generates_pdf_with_data(test_db):
    from services.reports.entries_submitted import generate_entries_submitted
    Exhibitor.create(exh_no=1, name="Adams, A.", club="KVK")
    ClassDef.create(class_code="N1", bird_type="NORWICH CANARY", main_class="OPEN COCKS",
                    colour="Yellow Clear", class_seq=1)
    ShowEntry.create(auto_num=1, exh_no=1, class_code="N1")
    pdf = generate_entries_submitted()
    assert isinstance(pdf, bytes)
    assert len(pdf) > 1000
```

- [ ] **Step 2: Run to verify they fail**

```
pytest tests/test_entries_submitted_pdf.py -v
```

Expected: `FAILED` — module not found

- [ ] **Step 3: Create `services/reports/entries_submitted.py`**

```python
# services/reports/entries_submitted.py
"""
Pre-show Entries Submitted report — three sections:
  A) Summary table (exhibitor + count)
  B) Entries by class (like Access 0030Q)
  C) Entries by exhibitor
Source: ShowEntry (pre-benching), NOT CalculatedEntry.
"""
from collections import defaultdict
from reportlab.lib.units import mm
from models.show_entry import ShowEntry
from models.exhibitor import Exhibitor
from models.class_def import ClassDef
from services.reports.base import (
    new_canvas, draw_page_header, draw_footer,
    MARGIN, PAGE_W, PAGE_H, ROW_H,
)

_SECTION_GAP = 4 * mm


def _load_data():
    exh_map = {e.exh_no: e for e in Exhibitor.select() if e.exh_no is not None}
    class_map = {c.class_code: c for c in ClassDef.select() if c.class_code}
    entries = list(ShowEntry.select().order_by(ShowEntry.exh_no, ShowEntry.auto_num))
    entries_by_exh: dict[int, list] = defaultdict(list)
    entries_by_class: dict[str, list] = defaultdict(list)
    for e in entries:
        if e.exh_no is not None:
            entries_by_exh[e.exh_no].append(e)
        entries_by_class[e.class_code or ""].append(e)
    return entries_by_exh, entries_by_class, exh_map, class_map


def _class_seq(code, class_map):
    cd = class_map.get(code)
    try:
        return float(cd.class_seq) if cd and cd.class_seq is not None else 999999.0
    except (TypeError, ValueError):
        return 999999.0


def _new_page(c, page_num, title, sd):
    draw_footer(c, page_num)
    c.showPage()
    page_num += 1
    y = draw_page_header(c, title, sd)
    return page_num, y


def generate_entries_submitted(sd=None) -> bytes:
    entries_by_exh, entries_by_class, exh_map, class_map = _load_data()
    buf, c = new_canvas()
    page_num = 1

    # Section A: Summary
    y = draw_page_header(c, "Entries Submitted — Summary", sd)
    page_num, y = _draw_summary(c, page_num, y, entries_by_exh, exh_map, sd)

    # Section B: By Class
    draw_footer(c, page_num)
    c.showPage()
    page_num += 1
    y = draw_page_header(c, "Entries Submitted — By Class", sd)
    page_num, y = _draw_by_class(c, page_num, y, entries_by_class, exh_map, class_map, sd)

    # Section C: By Exhibitor
    draw_footer(c, page_num)
    c.showPage()
    page_num += 1
    y = draw_page_header(c, "Entries Submitted — By Exhibitor", sd)
    page_num, y = _draw_by_exhibitor(c, page_num, y, entries_by_exh, exh_map, class_map, sd)

    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()


def _draw_summary(c, page_num, y, entries_by_exh, exh_map, sd):
    title = "Entries Submitted — Summary"
    col_exh = MARGIN
    col_name = MARGIN + 16 * mm
    col_club = MARGIN + 92 * mm
    col_count = PAGE_W - MARGIN

    def _header_row(y):
        c.setFont("Helvetica-Bold", 9)
        c.drawString(col_exh, y, "Exh #")
        c.drawString(col_name, y, "Name")
        c.drawString(col_club, y, "Club")
        c.drawRightString(col_count, y, "Entries")
        c.setLineWidth(0.3)
        c.line(MARGIN, y - 2, PAGE_W - MARGIN, y - 2)
        return y - ROW_H

    y = _header_row(y)
    total_entries = 0

    for exh_no in sorted(entries_by_exh):
        if y < MARGIN + ROW_H:
            page_num, y = _new_page(c, page_num, title, sd)
            y = _header_row(y)
        exh = exh_map.get(exh_no)
        count = len(entries_by_exh[exh_no])
        total_entries += count
        c.setFont("Helvetica", 9)
        c.drawString(col_exh, y, str(exh_no))
        c.drawString(col_name, y, (exh.name if exh else "")[:42])
        c.drawString(col_club, y, (exh.club if exh else "")[:20])
        c.drawRightString(col_count, y, str(count))
        y -= ROW_H

    # Totals
    c.setLineWidth(0.3)
    c.line(MARGIN, y + ROW_H - 1, PAGE_W - MARGIN, y + ROW_H - 1)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(col_name, y, f"Total: {len(entries_by_exh)} exhibitors")
    c.drawRightString(col_count, y, str(total_entries))
    return page_num, y - ROW_H


def _draw_by_class(c, page_num, y, entries_by_class, exh_map, class_map, sd):
    title = "Entries Submitted — By Class"
    sorted_codes = sorted(
        entries_by_class, key=lambda code: _class_seq(code, class_map)
    )
    cur_bird_type = None
    cur_main_class = None

    for code in sorted_codes:
        cd = class_map.get(code)
        bird_type = (cd.bird_type or "").upper() if cd else ""
        main_class = (cd.main_class or "").upper() if cd else ""
        colour = (cd.colour or "") if cd else ""

        if bird_type != cur_bird_type:
            if y < MARGIN + ROW_H * 4:
                page_num, y = _new_page(c, page_num, title, sd)
            cur_bird_type = bird_type
            cur_main_class = None
            y -= 2
            c.setFont("Helvetica-Bold", 10)
            c.drawString(MARGIN, y, bird_type)
            c.setLineWidth(0.5)
            c.line(MARGIN, y - 2, PAGE_W - MARGIN, y - 2)
            y -= ROW_H + 1

        if main_class != cur_main_class:
            cur_main_class = main_class
            if y < MARGIN + ROW_H * 3:
                page_num, y = _new_page(c, page_num, title, sd)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(MARGIN + 4 * mm, y, main_class)
            y -= ROW_H

        if y < MARGIN + ROW_H * 2:
            page_num, y = _new_page(c, page_num, title, sd)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(MARGIN + 8 * mm, y, f"{code}  {colour}"[:58])
        y -= ROW_H * 0.85

        for entry in entries_by_class[code]:
            if y < MARGIN + ROW_H:
                page_num, y = _new_page(c, page_num, title, sd)
            exh = exh_map.get(entry.exh_no)
            name = exh.name if exh else f"ExhNo {entry.exh_no}"
            c.setFont("Helvetica", 9)
            c.drawString(MARGIN + 14 * mm, y, f"{name}  (#{entry.exh_no})")
            y -= ROW_H * 0.9
        y -= 2

    return page_num, y


def _draw_by_exhibitor(c, page_num, y, entries_by_exh, exh_map, class_map, sd):
    title = "Entries Submitted — By Exhibitor"

    for exh_no in sorted(entries_by_exh):
        exh = exh_map.get(exh_no)
        exh_entries = entries_by_exh[exh_no]
        count = len(exh_entries)
        name = exh.name if exh else f"ExhNo {exh_no}"

        if y < MARGIN + ROW_H * 3:
            page_num, y = _new_page(c, page_num, title, sd)

        c.setFont("Helvetica-Bold", 10)
        label = f"#{exh_no}  {name}  —  {count} entr{'y' if count == 1 else 'ies'}"
        c.drawString(MARGIN, y, label[:70])
        c.setLineWidth(0.3)
        c.line(MARGIN, y - 2, PAGE_W - MARGIN, y - 2)
        y -= ROW_H

        for entry in sorted(exh_entries, key=lambda e: _class_seq(e.class_code, class_map)):
            if y < MARGIN + ROW_H:
                page_num, y = _new_page(c, page_num, title, sd)
            cd = class_map.get(entry.class_code)
            colour = cd.colour if cd else ""
            c.setFont("Helvetica", 9)
            c.drawString(MARGIN + 8 * mm, y, f"{(entry.class_code or ''):<8} {colour}"[:58])
            y -= ROW_H * 0.9

        y -= _SECTION_GAP

    return page_num, y
```

- [ ] **Step 4: Run to verify tests pass**

```
pytest tests/test_entries_submitted_pdf.py -v
```

Expected: both pass

- [ ] **Step 5: Run full suite**

```
pytest tests/ -q --tb=short
```

- [ ] **Step 6: Commit**

```bash
git add services/reports/entries_submitted.py tests/test_entries_submitted_pdf.py
git commit -m "feat: add Entries Submitted 3-section pre-show report"
```

---

## Task 7: Wire Entries Submitted button into reports view

**Files:**
- Modify: `views/reports_view.py`

- [ ] **Step 1: Add `_gen_entries_submitted()` method to `ReportsView`**

Append after `_gen_entries_received()`:

```python
    def _gen_entries_submitted(self):
        from services.reports.entries_submitted import generate_entries_submitted
        self._save_and_open(generate_entries_submitted, "benchabird_entries_submitted.pdf")
```

- [ ] **Step 2: Add entry to the reports list in `_build()`**

In the `reports` list, add as the first entry (pre-show reports should come first):

```python
        reports = [
            ("Entries Submitted", "benchabird_entries_submitted.pdf", self._gen_entries_submitted),
            ("Entries Received", "benchabird_entries_received.pdf", self._gen_entries_received),
            ("Show Catalogue", "benchabird_show_catalogue.pdf", self._gen_show_catalogue),
            # ... rest unchanged
        ]
```

The full updated list:

```python
        reports = [
            ("Entries Submitted",  "benchabird_entries_submitted.pdf",  self._gen_entries_submitted),
            ("Entries Received",   "benchabird_entries_received.pdf",   self._gen_entries_received),
            ("Show Catalogue",     "benchabird_show_catalogue.pdf",     self._gen_show_catalogue),
            ("4.1 Judges Catalogue","benchabird_4_1_judges_catalogue.pdf", self._gen_judges_catalogue),
            ("4.2 Special Lists",  "benchabird_4_2_special_lists.pdf",  self._gen_special_lists_catalogue),
            ("4.3 Catalogue",      "benchabird_4_3_catalogue.pdf",      self._gen_catalogue_4_3),
            ("4.4 Marked Catalogue","benchabird_4_4_marked_catalogue.pdf", self._gen_marked_catalogue),
            ("Results Sheet",      "benchabird_results_sheet.pdf",      self._gen_results_sheet),
            ("Special Winners",    "benchabird_special_winners.pdf",    self._gen_special_winners),
            ("Prize Money",        "benchabird_prize_money.pdf",        self._gen_prize_money),
            ("Address Tags",       "benchabird_address_tags.pdf",       self._gen_address_tags),
            ("Exhibitor List",     "benchabird_exhibitor_list.pdf",     self._gen_exhibitor_list),
            ("Entry Confirmation", "benchabird_entry_confirmation.pdf", self._gen_entry_confirmation),
            ("Exhibitor Bundle",   "benchabird_exhibitor_bundle.pdf",   self._gen_exhibitor_bundle),
            ("Results by Exhibitor","benchabird_results_by_exhibitor.pdf", self._gen_results_by_exhibitor),
        ]
```

- [ ] **Step 3: Run full suite**

```
pytest tests/ -q --tb=short
```

Expected: all pass

- [ ] **Step 4: Commit**

```bash
git add views/reports_view.py
git commit -m "feat: add Entries Submitted button to Reports view"
```

---

## Self-Review

**Spec coverage:**
- [x] `is_entrant` field on Exhibitor → Task 1
- [x] Migration → Task 1
- [x] Reset clears `is_entrant` → Task 2
- [x] `get_unenrolled_exhibitors(flagged_only)` → Task 3
- [x] Enrol dialog uses `flagged_only=True` → Task 4
- [x] Toggle Entrant button on Exhibitors page → Task 5
- [x] Entrant column in table → Task 5
- [x] Export includes is_entrant → Task 5
- [x] `entries_submitted.py` — Section A summary → Task 6
- [x] `entries_submitted.py` — Section B by class → Task 6
- [x] `entries_submitted.py` — Section C by exhibitor → Task 6
- [x] Reports view button → Task 7

**No placeholders:** All steps contain complete code.

**Type consistency:**
- `get_unenrolled_exhibitors(query="", flagged_only=False)` defined in Task 3, called with `flagged_only=True` in Task 4. ✓
- `_repo.update(exhibitor, is_entrant=...)` uses `ExhibitorRepo.update(**data)` which accepts kwargs. ✓
- `generate_entries_submitted(sd=None)` matches the pattern of all other report generators. ✓
- `_new_page(c, page_num, title, sd)` returns `(page_num, y)` consistently across all three section helpers. ✓
