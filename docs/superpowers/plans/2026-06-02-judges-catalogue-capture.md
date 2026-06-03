# Judges Catalogue Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an Access-inspired Judges Catalogue PDF and a category-based Judging Capture dialog for entering handwritten judging results.

**Architecture:** Add a pure service layer for category/query/save behavior, then use it from both the PDF generator and the capture dialog. Keep UI wiring small: Reports gets a `Judges Catalogue` button, Results replaces the visible `Judge Mode` button with `Judging Capture`, and README documents the paper workflow.

**Tech Stack:** Python, Peewee, CustomTkinter, ReportLab, pytest.

---

## File Structure

- Create `services/judging_catalogue_service.py`: query category groups, query ordered entries for a category, and bulk-save row selections.
- Create `services/reports/judges_catalogue.py`: generate the printable Judges Catalogue PDF from the service rows.
- Create `tests/test_judging_catalogue_service.py`: service tests for ordering, category filtering, and save semantics.
- Create `tests/test_judges_catalogue_pdf.py`: PDF smoke tests and no-data behavior.
- Create `views/_judging_capture_dialog.py`: modal category capture UI using radio buttons and the service save API.
- Modify `views/results_view.py`: replace visible `Judge Mode` button with `Judging Capture`.
- Modify `views/reports_view.py`: add `Judges Catalogue` to the report grid.
- Modify `README.md`: document the print/capture/results workflow.

---

## Task 1: Judging Catalogue Service

**Files:**
- Create: `services/judging_catalogue_service.py`
- Test: `tests/test_judging_catalogue_service.py`

- [ ] **Step 1: Write failing service tests**

Create `tests/test_judging_catalogue_service.py`:

```python
from models.class_def import ClassDef, MainClass, Species
from models.results import NotBenched, Result
from models.show_entry import CalculatedEntry


def seed_class_data():
    Species.create(seq=2, bird_type="Red Factor", type2="Red Factor", type3="Red")
    Species.create(seq=1, bird_type="Gloster", type2="Gloster", type3="Gloster")
    MainClass.create(main_class="Champion", mc_seq=1)
    MainClass.create(main_class="Novice", mc_seq=2)
    ClassDef.create(
        class_code="RF01",
        bird_type="Red Factor",
        type_b="Red Factor Type",
        main_class="Champion",
        colour="Red cock",
        class_seq=10,
    )
    ClassDef.create(
        class_code="GL01",
        bird_type="Gloster",
        type_b="Gloster Type",
        main_class="Novice",
        colour="Corona hen",
        class_seq=5,
    )


def test_list_judging_categories_orders_by_species_sequence(test_db):
    from services.judging_catalogue_service import list_judging_categories

    seed_class_data()
    CalculatedEntry.create(auto_num=20, exh_no=2, name="B", class_code="RF01")
    CalculatedEntry.create(auto_num=10, exh_no=1, name="A", class_code="GL01")

    categories = list_judging_categories()

    assert [(c.key, c.label, c.entry_count) for c in categories] == [
        ("Gloster", "Gloster", 1),
        ("Red Factor", "Red Factor", 1),
    ]


def test_get_judging_entries_for_category_preserves_access_inspired_order(test_db):
    from services.judging_catalogue_service import get_judging_entries

    seed_class_data()
    CalculatedEntry.create(auto_num=21, exh_no=2, name="B", class_code="RF01")
    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="RF01")
    CalculatedEntry.create(auto_num=10, exh_no=3, name="C", class_code="GL01")

    rows = get_judging_entries("Red Factor")

    assert [r.auto_num for r in rows] == [20, 21]
    assert rows[0].category == "Red Factor"
    assert rows[0].main_class == "Champion"
    assert rows[0].class_code == "RF01"
    assert rows[0].colour == "Red cock"


def test_get_judging_entries_includes_existing_result_and_nb(test_db):
    from services.judging_catalogue_service import get_judging_entries

    seed_class_data()
    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="RF01")
    Result.create(exhibit_no=20, result="1st")
    NotBenched.create(exhibit_no=20, not_benched="Not Benched", nb="NB")

    rows = get_judging_entries("Red Factor")

    assert rows[0].current_result == "1st"
    assert rows[0].not_benched is True


def test_save_category_results_records_placing_and_clears_nb(test_db):
    from services.judging_catalogue_service import save_category_results

    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="RF01")
    NotBenched.create(exhibit_no=20, not_benched="Not Benched", nb="NB")

    saved = save_category_results({20: "BOB"})

    assert saved == 1
    assert Result.get(Result.exhibit_no == 20).result == "BOB"
    assert NotBenched.get_or_none(NotBenched.exhibit_no == 20) is None


def test_save_category_results_records_nb_and_clears_result(test_db):
    from services.judging_catalogue_service import save_category_results

    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="RF01")
    Result.create(exhibit_no=20, result="1st")

    saved = save_category_results({20: "NB"})

    assert saved == 1
    assert Result.get(Result.exhibit_no == 20).result is None
    assert NotBenched.get_or_none(NotBenched.exhibit_no == 20) is not None


def test_save_category_results_clear_removes_result_and_nb(test_db):
    from services.judging_catalogue_service import save_category_results

    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="RF01")
    Result.create(exhibit_no=20, result="1st")
    NotBenched.create(exhibit_no=20, not_benched="Not Benched", nb="NB")

    saved = save_category_results({20: "Clear"})

    assert saved == 1
    assert Result.get(Result.exhibit_no == 20).result is None
    assert NotBenched.get_or_none(NotBenched.exhibit_no == 20) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests\test_judging_catalogue_service.py`

Expected: fail with `ModuleNotFoundError: No module named 'services.judging_catalogue_service'`.

- [ ] **Step 3: Implement service**

Create `services/judging_catalogue_service.py`:

```python
from __future__ import annotations

from dataclasses import dataclass

from models.class_def import ClassDef, MainClass, Species
from models.results import Result
from models.show_entry import CalculatedEntry
from services.not_benched_service import (
    get_not_benched_set,
    mark_not_benched,
    unmark_not_benched,
)
from services.results_service import record_result


RESULT_OPTIONS = ["1st", "2nd", "3rd", "4th", "5th", "BOB", "R/U BOB", "Champion", "Reserve"]
CLEAR_OPTION = "Clear"
NB_OPTION = "NB"


@dataclass(frozen=True)
class JudgingCategory:
    key: str
    label: str
    seq: int
    entry_count: int


@dataclass(frozen=True)
class JudgingEntry:
    auto_num: int
    exh_no: int | None
    name: str | None
    class_code: str | None
    category: str
    category_seq: int
    main_class: str
    main_class_seq: int
    class_seq: int
    type_b: str
    colour: str
    current_result: str | None
    not_benched: bool


def _rows() -> list[JudgingEntry]:
    db = CalculatedEntry._meta.database
    sql = """
        SELECT ce.auto_num, ce.exh_no, ce.name, ce.class_code,
               COALESCE(cd.bird_type, '(Unclassified)') AS category,
               COALESCE(sp.seq, 999999) AS category_seq,
               COALESCE(cd.main_class, '(Unknown)') AS main_class,
               COALESCE(mc.mc_seq, 999999) AS main_class_seq,
               COALESCE(cd.class_seq, 999999) AS class_seq,
               COALESCE(cd.type_b, '') AS type_b,
               COALESCE(cd.colour, '') AS colour,
               r.result
        FROM calculated_entry ce
        LEFT JOIN class_def cd ON ce.class_code = cd.class_code
        LEFT JOIN species sp ON cd.bird_type = sp.bird_type
        LEFT JOIN main_class mc ON cd.main_class = mc.main_class
        LEFT JOIN result r ON ce.auto_num = r.exhibit_no
        ORDER BY category_seq, category, main_class_seq, main_class, class_seq, ce.class_code, ce.auto_num
    """
    nb_set = get_not_benched_set()
    return [
        JudgingEntry(
            auto_num=row[0],
            exh_no=row[1],
            name=row[2],
            class_code=row[3],
            category=row[4],
            category_seq=int(row[5] or 999999),
            main_class=row[6],
            main_class_seq=int(row[7] or 999999),
            class_seq=int(row[8] or 999999),
            type_b=row[9],
            colour=row[10],
            current_result=row[11],
            not_benched=row[0] in nb_set,
        )
        for row in db.execute_sql(sql).fetchall()
    ]


def list_judging_categories() -> list[JudgingCategory]:
    grouped: dict[str, JudgingCategory] = {}
    for row in _rows():
        existing = grouped.get(row.category)
        if existing is None:
            grouped[row.category] = JudgingCategory(
                key=row.category,
                label=row.category,
                seq=row.category_seq,
                entry_count=1,
            )
        else:
            grouped[row.category] = JudgingCategory(
                key=existing.key,
                label=existing.label,
                seq=existing.seq,
                entry_count=existing.entry_count + 1,
            )
    return sorted(grouped.values(), key=lambda c: (c.seq, c.label))


def get_judging_entries(category_key: str | None = None) -> list[JudgingEntry]:
    rows = _rows()
    if category_key:
        rows = [row for row in rows if row.category == category_key]
    return rows


def save_category_results(selections: dict[int, str]) -> int:
    saved = 0
    valid = set(RESULT_OPTIONS + [NB_OPTION, CLEAR_OPTION])
    for auto_num, value in selections.items():
        value = (value or "").strip()
        if not value or value not in valid:
            continue
        if value == NB_OPTION:
            mark_not_benched(auto_num)
            record_result(auto_num, None)
        elif value == CLEAR_OPTION:
            unmark_not_benched(auto_num)
            record_result(auto_num, None)
        else:
            unmark_not_benched(auto_num)
            record_result(auto_num, value)
        saved += 1
    return saved
```

- [ ] **Step 4: Run service tests**

Run: `python -m pytest tests\test_judging_catalogue_service.py`

Expected: all tests pass.

---

## Task 2: Judges Catalogue PDF

**Files:**
- Create: `services/reports/judges_catalogue.py`
- Test: `tests/test_judges_catalogue_pdf.py`

- [ ] **Step 1: Write failing PDF tests**

Create `tests/test_judges_catalogue_pdf.py`:

```python
from models.class_def import ClassDef, MainClass, Species
from models.show_entry import CalculatedEntry


def test_generate_judges_catalogue_empty_returns_pdf(test_db):
    from services.reports.judges_catalogue import generate_judges_catalogue

    pdf = generate_judges_catalogue()

    assert pdf[:4] == b"%PDF"
    assert b"Judges Catalogue" in pdf
    assert b"Run Calculate" in pdf


def test_generate_judges_catalogue_with_entries_returns_pdf(test_db):
    from services.reports.judges_catalogue import generate_judges_catalogue

    Species.create(seq=1, bird_type="Gloster", type2="Gloster", type3="Gloster")
    MainClass.create(main_class="Novice", mc_seq=1)
    ClassDef.create(
        class_code="GL01",
        bird_type="Gloster",
        type_b="Gloster Type",
        main_class="Novice",
        colour="Corona hen",
        class_seq=5,
    )
    CalculatedEntry.create(auto_num=10, exh_no=1, name="A", class_code="GL01")

    pdf = generate_judges_catalogue()

    assert pdf[:4] == b"%PDF"
    assert b"Judges Catalogue" in pdf
    assert b"GL01" in pdf
    assert b"BOB" in pdf
    assert b"NB" in pdf
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests\test_judges_catalogue_pdf.py`

Expected: fail with `ModuleNotFoundError: No module named 'services.reports.judges_catalogue'`.

- [ ] **Step 3: Implement PDF generator**

Create `services/reports/judges_catalogue.py` using `get_judging_entries`, `new_canvas`, `draw_page_header`, `draw_footer`, `MARGIN`, `PAGE_H`, `PAGE_W`, and `ROW_H`.

Key behavior:

```python
from reportlab.lib.units import mm

from services.judging_catalogue_service import get_judging_entries
from services.reports.base import MARGIN, PAGE_H, PAGE_W, ROW_H, draw_footer, draw_page_header, new_canvas

BOX_LABELS = ["1", "2", "3", "4", "5", "BOB", "R/U BOB", "Champ", "Res", "NB"]


def _draw_boxes(c, y):
    x = MARGIN + 28 * mm
    for label in BOX_LABELS:
        width = 10 * mm if len(label) <= 2 else 16 * mm
        c.rect(x, y - 3, width, 10, stroke=1, fill=0)
        c.setFont("Helvetica", 6)
        c.drawCentredString(x + width / 2, y, label)
        x += width + 2 * mm


def generate_judges_catalogue(sd=None) -> bytes:
    rows = get_judging_entries()
    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "Judges Catalogue", sd)

    if not rows:
        c.setFont("Helvetica", 10)
        c.drawString(MARGIN, y, "Run Calculate before printing judging sheets.")
        draw_footer(c, page_num)
        c.save()
        return buf.getvalue()

    last_category = None
    last_main = None
    last_class = None

    for row in rows:
        if row.category != last_category:
            if last_category is not None:
                draw_footer(c, page_num)
                c.showPage()
                page_num += 1
                y = draw_page_header(c, "Judges Catalogue", sd)
            c.setFont("Helvetica-Bold", 13)
            c.drawString(MARGIN, y, row.category)
            y -= ROW_H + 3
            last_category = row.category
            last_main = None
            last_class = None

        if y < MARGIN + ROW_H * 5:
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            y = draw_page_header(c, "Judges Catalogue", sd)
            last_main = None
            last_class = None

        if row.main_class != last_main:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(MARGIN, y, row.main_class)
            y -= ROW_H
            last_main = row.main_class
            last_class = None

        if row.class_code != last_class:
            c.setFont("Helvetica-Bold", 9)
            class_label = f"{row.class_code or ''}  {row.colour}".strip()
            c.drawString(MARGIN, y, class_label)
            if row.type_b:
                c.setFont("Helvetica", 8)
                c.drawRightString(PAGE_W - MARGIN, y, row.type_b)
            y -= ROW_H
            last_class = row.class_code

        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN + 4 * mm, y, str(row.auto_num))
        _draw_boxes(c, y)
        y -= ROW_H + 1

    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()
```

- [ ] **Step 4: Run PDF tests**

Run: `python -m pytest tests\test_judges_catalogue_pdf.py`

Expected: all tests pass.

---

## Task 3: Judging Capture Dialog and Wiring

**Files:**
- Create: `views/_judging_capture_dialog.py`
- Modify: `views/results_view.py`
- Modify: `views/reports_view.py`
- Test: existing import tests or focused new smoke tests in `tests/test_judging_capture_imports.py`

- [ ] **Step 1: Write failing import/wiring tests**

Create `tests/test_judging_capture_imports.py`:

```python
def test_judging_capture_dialog_imports(test_db):
    from views._judging_capture_dialog import JudgingCaptureDialog

    assert JudgingCaptureDialog.__name__ == "JudgingCaptureDialog"


def test_reports_view_imports_with_judges_catalogue(test_db):
    from views.reports_view import ReportsView

    assert ReportsView.__name__ == "ReportsView"


def test_results_view_imports_with_judging_capture(test_db):
    from views.results_view import ResultsView

    assert ResultsView.__name__ == "ResultsView"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests\test_judging_capture_imports.py`

Expected: fail because `views._judging_capture_dialog` does not exist.

- [ ] **Step 3: Implement dialog**

Create `views/_judging_capture_dialog.py`:

```python
import customtkinter as ctk

from services.judging_catalogue_service import (
    CLEAR_OPTION,
    NB_OPTION,
    RESULT_OPTIONS,
    get_judging_entries,
    list_judging_categories,
    save_category_results,
)


class JudgingCaptureDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_saved=None):
        super().__init__(parent)
        self._on_saved = on_saved
        self._categories = []
        self._rows = []
        self._vars = {}
        self.title("Judging Capture")
        self.geometry("980x650")
        self.minsize(820, 500)
        self._build()
        self.after(50, self.lift)

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        ctk.CTkLabel(top, text="Judging Capture", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        picker = ctk.CTkFrame(self, fg_color=("gray88", "gray20"), corner_radius=8)
        picker.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        ctk.CTkLabel(picker, text="Category").pack(side="left", padx=(12, 4), pady=8)
        self._category_combo = ctk.CTkComboBox(picker, values=[], width=240, command=lambda _v: self._load_selected())
        self._category_combo.pack(side="left", padx=4, pady=8)
        self._status = ctk.CTkLabel(picker, text="", font=ctk.CTkFont(size=11), text_color=("gray40", "gray60"))
        self._status.pack(side="left", padx=12)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 8))

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 16))
        ctk.CTkButton(bottom, text="Save Category Results", command=self._save).pack(side="right", padx=4)
        ctk.CTkButton(
            bottom,
            text="Close",
            fg_color=("gray75", "gray35"),
            text_color=("gray10", "gray90"),
            command=self.destroy,
        ).pack(side="right", padx=4)

        self._load_categories()

    def _load_categories(self):
        self._categories = list_judging_categories()
        labels = [c.label for c in self._categories]
        self._category_combo.configure(values=labels)
        if not labels:
            self._status.configure(text="Run Calculate before capturing judging sheets.")
            return
        self._category_combo.set(labels[0])
        self._load_selected()

    def _load_selected(self):
        label = self._category_combo.get()
        category = next((c for c in self._categories if c.label == label), None)
        if category is None:
            return
        self._rows = get_judging_entries(category.key)
        self._render_rows()

    def _render_rows(self):
        for child in self._scroll.winfo_children():
            child.destroy()
        self._vars = {}
        if not self._rows:
            ctk.CTkLabel(self._scroll, text="No entries in this category.").grid(row=0, column=0, pady=20)
            return

        headers = ["Exhibit", "Class", "Description", *RESULT_OPTIONS, NB_OPTION, CLEAR_OPTION]
        for col, header in enumerate(headers):
            ctk.CTkLabel(self._scroll, text=header, font=ctk.CTkFont(size=11, weight="bold")).grid(
                row=0, column=col, padx=3, pady=3, sticky="w"
            )

        for row_i, entry in enumerate(self._rows, start=1):
            ctk.CTkLabel(self._scroll, text=str(entry.auto_num), width=54).grid(row=row_i, column=0, padx=3, pady=2)
            ctk.CTkLabel(self._scroll, text=entry.class_code or "", width=64).grid(row=row_i, column=1, padx=3, pady=2)
            desc = entry.colour or entry.type_b or ""
            ctk.CTkLabel(self._scroll, text=desc[:30], width=160, anchor="w").grid(row=row_i, column=2, padx=3, pady=2)
            current = NB_OPTION if entry.not_benched else (entry.current_result or "")
            var = ctk.StringVar(value=current)
            self._vars[entry.auto_num] = var
            for offset, option in enumerate([*RESULT_OPTIONS, NB_OPTION, CLEAR_OPTION], start=3):
                ctk.CTkRadioButton(
                    self._scroll,
                    text="",
                    value=option,
                    variable=var,
                    width=26,
                ).grid(row=row_i, column=offset, padx=2, pady=2)

    def _save(self):
        selections = {auto_num: var.get() for auto_num, var in self._vars.items() if var.get()}
        saved = save_category_results(selections)
        self._status.configure(text=f"Saved {saved} updates.")
        self._load_selected()
        if self._on_saved:
            self._on_saved()
```

- [ ] **Step 4: Wire Results button**

In `views/results_view.py`:

- Import `JudgingCaptureDialog`.
- Replace the toolbar button text/command from `Judge Mode` / `_open_judge_mode` to `Judging Capture` / `_open_judging_capture`.
- Add `_open_judging_capture` that calls `JudgingCaptureDialog(self, on_saved=self._reload_table)`.

- [ ] **Step 5: Wire Reports button**

In `views/reports_view.py`:

- Add `("Judges Catalogue", "benchabird_judges_catalogue.pdf", self._gen_judges_catalogue)` to the `reports` list.
- Add `_gen_judges_catalogue` importing `generate_judges_catalogue` and calling `_save_and_open`.

- [ ] **Step 6: Run import tests**

Run: `python -m pytest tests\test_judging_capture_imports.py`

Expected: all tests pass.

---

## Task 4: Documentation and Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Document:

- Reports includes `Judges Catalogue`.
- Results includes `Judging Capture`.
- Workflow: print sheet, judges mark by hand, show manager captures by category, then prints result reports.

- [ ] **Step 2: Run targeted tests**

Run:

```powershell
python -m pytest tests\test_judging_catalogue_service.py tests\test_judges_catalogue_pdf.py tests\test_judging_capture_imports.py
```

Expected: all tests pass.

- [ ] **Step 3: Run full app tests**

Run: `python -m pytest tests`

Expected: all tests pass.

- [ ] **Step 4: Commit implementation**

Run:

```powershell
git add README.md services\judging_catalogue_service.py services\reports\judges_catalogue.py tests\test_judging_catalogue_service.py tests\test_judges_catalogue_pdf.py tests\test_judging_capture_imports.py views\_judging_capture_dialog.py views\reports_view.py views\results_view.py
git commit -m "Add judges catalogue capture workflow"
```

---

## Self-Review

- Spec coverage: the plan covers the PDF, category capture dialog, saving semantics, Results/Reports wiring, tests, and README updates.
- Placeholder scan: no `TBD`, `TODO`, or vague "add tests later" steps remain.
- Type consistency: service dataclasses are `JudgingCategory` and `JudgingEntry`; UI and PDF use the same service functions and constants.
