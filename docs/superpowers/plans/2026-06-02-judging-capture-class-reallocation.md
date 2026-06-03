# Judging Capture Class Reallocation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow the show manager to correct an exhibit's class while capturing Judges Catalogue results, preserving the exhibit AutoNum.

**Architecture:** Extend `services/judging_catalogue_service.py` so class options, class-change validation, and class/result transaction semantics are pure and testable. Then update `views/_judging_capture_dialog.py` to show a per-row class selector, warn when a row moves out of the active category, and submit changed class/result data together.

**Tech Stack:** Python, Peewee, CustomTkinter, pytest.

---

## File Structure

- Modify `services/judging_catalogue_service.py`: add class-option query, service exception, class-change payload handling, and transactional save.
- Modify `tests/test_judging_catalogue_service.py`: add tests for valid class reallocation, invalid class rejection, class+result transaction behavior, and category reload behavior.
- Modify `views/_judging_capture_dialog.py`: add class combo state per row, changed-class helper, cross-category warning helper, and save payload changes.
- Modify `tests/test_judging_capture_imports.py`: add helper tests for changed class payloads and cross-category warning detection.
- Modify `README.md` and `views/help_view.py`: mention class correction during Judging Capture.

---

## Task 1: Service Class Reallocation

**Files:**
- Modify: `services/judging_catalogue_service.py`
- Modify: `tests/test_judging_catalogue_service.py`

- [ ] **Step 1: Add failing service tests**

Append these tests to `tests/test_judging_catalogue_service.py`:

```python
def test_list_class_options_orders_with_context(test_db):
    from services.judging_catalogue_service import list_class_options

    seed_class_data()

    options = list_class_options()

    assert [(o.class_code, o.category, o.main_class, o.colour) for o in options] == [
        ("GL01", "Gloster", "Novice", "Corona hen"),
        ("RF01", "Red Factor", "Champion", "Red cock"),
    ]


def test_save_category_results_reallocates_class_and_preserves_auto_num(test_db):
    from services.judging_catalogue_service import save_category_results

    seed_class_data()
    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="GL01")

    saved = save_category_results({20: {"class_code": "RF01"}})

    row = CalculatedEntry.get_by_id(20)
    assert saved == 1
    assert row.auto_num == 20
    assert row.class_code == "RF01"


def test_save_category_results_reallocates_class_and_records_result(test_db):
    from services.judging_catalogue_service import save_category_results

    seed_class_data()
    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="GL01")

    saved = save_category_results({20: {"class_code": "RF01", "result": "BOB"}})

    row = CalculatedEntry.get_by_id(20)
    assert saved == 1
    assert row.class_code == "RF01"
    assert Result.get(Result.exhibit_no == 20).result == "BOB"


def test_save_category_results_rejects_invalid_class_without_result_side_effect(test_db):
    from services.judging_catalogue_service import JudgingCatalogueError, save_category_results

    seed_class_data()
    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="GL01")

    try:
        save_category_results({20: {"class_code": "BAD", "result": "BOB"}})
    except JudgingCatalogueError as exc:
        assert "Select a valid class" in str(exc)
    else:
        raise AssertionError("Expected invalid class to raise JudgingCatalogueError")

    row = CalculatedEntry.get_by_id(20)
    assert row.class_code == "GL01"
    assert Result.get_or_none(Result.exhibit_no == 20) is None


def test_reallocated_class_moves_row_to_new_category(test_db):
    from services.judging_catalogue_service import get_judging_entries, save_category_results

    seed_class_data()
    CalculatedEntry.create(auto_num=20, exh_no=1, name="A", class_code="GL01")

    save_category_results({20: {"class_code": "RF01"}})

    assert [r.auto_num for r in get_judging_entries("Gloster")] == []
    assert [r.auto_num for r in get_judging_entries("Red Factor")] == [20]
```

- [ ] **Step 2: Run service tests and verify failure**

Run:

```powershell
python -m pytest tests\test_judging_catalogue_service.py -q
```

Expected: the new tests fail because `list_class_options` and `JudgingCatalogueError` do not exist, and `save_category_results` only accepts string result values.

- [ ] **Step 3: Implement service support**

In `services/judging_catalogue_service.py`, add the missing imports near the top:

```python
from typing import Any

from models.class_def import ClassDef
```

Add these definitions below the existing constants:

```python
class JudgingCatalogueError(Exception):
    pass


@dataclass(frozen=True)
class JudgingClassOption:
    class_code: str
    category: str
    category_seq: int
    main_class: str
    main_class_seq: int
    class_seq: int
    type_b: str
    colour: str

    @property
    def label(self) -> str:
        bits = [self.class_code]
        if self.colour:
            bits.append(self.colour)
        if self.category:
            bits.append(self.category)
        return " - ".join(bits)
```

Add this function after `_rows()`:

```python
def list_class_options() -> list[JudgingClassOption]:
    db = ClassDef._meta.database
    sql = """
        SELECT cd.class_code,
               COALESCE(cd.bird_type, '(Unclassified)') AS category,
               COALESCE(sp.seq, 999999) AS category_seq,
               COALESCE(cd.main_class, '(Unknown)') AS main_class,
               COALESCE(mc.mc_seq, 999999) AS main_class_seq,
               COALESCE(cd.class_seq, 999999) AS class_seq,
               COALESCE(cd.type_b, '') AS type_b,
               COALESCE(cd.colour, '') AS colour
        FROM class_def cd
        LEFT JOIN species sp ON cd.bird_type = sp.bird_type
        LEFT JOIN main_class mc ON cd.main_class = mc.main_class
        WHERE cd.class_code IS NOT NULL AND TRIM(cd.class_code) <> ''
        ORDER BY category_seq, category, main_class_seq, main_class, class_seq, cd.class_code
    """
    return [
        JudgingClassOption(
            class_code=row[0],
            category=row[1],
            category_seq=int(row[2] or 999999),
            main_class=row[3],
            main_class_seq=int(row[4] or 999999),
            class_seq=int(row[5] or 999999),
            type_b=row[6],
            colour=row[7],
        )
        for row in db.execute_sql(sql).fetchall()
    ]
```

Replace `save_category_results` with:

```python
def _normalise_selection(value: Any) -> tuple[str, str | None]:
    if isinstance(value, dict):
        result_value = (value.get("result") or "").strip()
        class_code = (value.get("class_code") or "").strip() or None
    else:
        result_value = (value or "").strip()
        class_code = None
    return result_value, class_code


def save_category_results(selections: dict[int, Any]) -> int:
    saved = 0
    valid = set(RESULT_OPTIONS + [NB_OPTION, CLEAR_OPTION])
    db = CalculatedEntry._meta.database

    with db.atomic():
        for auto_num, raw_value in selections.items():
            result_value, class_code = _normalise_selection(raw_value)
            if result_value and result_value not in valid:
                continue

            entry = CalculatedEntry.get_or_none(CalculatedEntry.auto_num == auto_num)
            if entry is None:
                continue

            changed = False
            if class_code and class_code != entry.class_code:
                exists = ClassDef.get_or_none(ClassDef.class_code == class_code)
                if exists is None:
                    raise JudgingCatalogueError(f"Select a valid class for exhibit #{auto_num}.")
                entry.class_code = class_code
                entry.save(only=[CalculatedEntry.class_code])
                changed = True

            if result_value:
                if result_value == NB_OPTION:
                    mark_not_benched(auto_num)
                    record_result(auto_num, None)
                elif result_value == CLEAR_OPTION:
                    unmark_not_benched(auto_num)
                    record_result(auto_num, None)
                else:
                    unmark_not_benched(auto_num)
                    record_result(auto_num, result_value)
                changed = True

            if changed:
                saved += 1
    return saved
```

- [ ] **Step 4: Run service tests and verify pass**

Run:

```powershell
python -m pytest tests\test_judging_catalogue_service.py -q
```

Expected: all tests in `test_judging_catalogue_service.py` pass.

---

## Task 2: Dialog Payload Helpers

**Files:**
- Modify: `views/_judging_capture_dialog.py`
- Modify: `tests/test_judging_capture_imports.py`

- [ ] **Step 1: Add failing helper tests**

Append these tests to `tests/test_judging_capture_imports.py`:

```python
def test_judging_capture_builds_combined_save_payload(test_db):
    from views._judging_capture_dialog import JudgingCaptureDialog

    payload = JudgingCaptureDialog.changed_payload(
        current_results={10: "1st", 11: "", 12: "NB"},
        initial_results={10: "", 11: "", 12: "NB"},
        current_classes={10: "GL01", 11: "RF01", 12: "GL01"},
        initial_classes={10: "GL01", 11: "GL01", 12: "GL01"},
    )

    assert payload == {
        10: {"result": "1st"},
        11: {"class_code": "RF01"},
    }


def test_judging_capture_detects_cross_category_moves(test_db):
    from views._judging_capture_dialog import JudgingCaptureDialog

    moves = JudgingCaptureDialog.cross_category_moves(
        payload={10: {"class_code": "RF01"}, 11: {"class_code": "GL01"}},
        active_category="Gloster",
        class_categories={"RF01": "Red Factor", "GL01": "Gloster"},
    )

    assert moves == [(10, "Red Factor")]
```

- [ ] **Step 2: Run helper tests and verify failure**

Run:

```powershell
python -m pytest tests\test_judging_capture_imports.py -q
```

Expected: fail because `changed_payload` and `cross_category_moves` do not exist.

- [ ] **Step 3: Add helper methods**

In `views/_judging_capture_dialog.py`, replace the current `changed_selections` static method with:

```python
    @staticmethod
    def changed_selections(current, initial):
        return {
            auto_num: value
            for auto_num, value in current.items()
            if value and value != initial.get(auto_num, "")
        }

    @staticmethod
    def changed_payload(current_results, initial_results, current_classes, initial_classes):
        payload = {}
        for auto_num, value in current_results.items():
            if value and value != initial_results.get(auto_num, ""):
                payload.setdefault(auto_num, {})["result"] = value
        for auto_num, class_code in current_classes.items():
            if class_code and class_code != initial_classes.get(auto_num, ""):
                payload.setdefault(auto_num, {})["class_code"] = class_code
        return payload

    @staticmethod
    def cross_category_moves(payload, active_category, class_categories):
        moves = []
        for auto_num, values in payload.items():
            class_code = values.get("class_code")
            new_category = class_categories.get(class_code)
            if new_category and new_category != active_category:
                moves.append((auto_num, new_category))
        return moves
```

- [ ] **Step 4: Run helper tests and verify pass**

Run:

```powershell
python -m pytest tests\test_judging_capture_imports.py -q
```

Expected: all tests in `test_judging_capture_imports.py` pass.

---

## Task 3: Dialog Class Selector UI

**Files:**
- Modify: `views/_judging_capture_dialog.py`

- [ ] **Step 1: Import class options**

Update the service import at the top of `views/_judging_capture_dialog.py`:

```python
from services.judging_catalogue_service import (
    CLEAR_OPTION,
    NB_OPTION,
    RESULT_OPTIONS,
    JudgingCatalogueError,
    get_judging_entries,
    list_class_options,
    list_judging_categories,
    save_category_results,
)
```

- [ ] **Step 2: Add class state fields**

In `JudgingCaptureDialog.__init__`, after `self._initial = {}`, add:

```python
        self._class_vars = {}
        self._initial_classes = {}
        self._class_options = []
        self._class_labels_by_code = {}
        self._class_code_by_label = {}
        self._class_categories = {}
        self._active_category = ""
```

- [ ] **Step 3: Load class options when categories load**

At the start of `_load_categories`, before `self._categories = list_judging_categories()`, add:

```python
        self._class_options = list_class_options()
        self._class_labels_by_code = {
            option.class_code: option.label
            for option in self._class_options
        }
        self._class_code_by_label = {
            option.label: option.class_code
            for option in self._class_options
        }
        self._class_categories = {
            option.class_code: option.category
            for option in self._class_options
        }
```

- [ ] **Step 4: Track the active category**

In `_load_selected`, immediately after `if category is None: return`, add:

```python
        self._active_category = category.key
```

- [ ] **Step 5: Render a class combobox per row**

In `_render_rows`, after `self._initial = {}`, add:

```python
        self._class_vars = {}
        self._initial_classes = {}
```

Change the `headers` assignment to:

```python
        headers = ["Exhibit", "Class", "Description", *RESULT_OPTIONS, NB_OPTION, CLEAR_OPTION]
```

Replace the existing class label block:

```python
            ctk.CTkLabel(self._scroll, text=entry.class_code or "", width=64).grid(
                row=row_i,
                column=1,
                padx=3,
                pady=2,
            )
```

with:

```python
            class_label = self._class_labels_by_code.get(entry.class_code or "", entry.class_code or "")
            class_var = ctk.StringVar(value=class_label)
            self._class_vars[entry.auto_num] = class_var
            self._initial_classes[entry.auto_num] = entry.class_code or ""
            ctk.CTkComboBox(
                self._scroll,
                values=list(self._class_code_by_label.keys()),
                variable=class_var,
                width=150,
            ).grid(row=row_i, column=1, padx=3, pady=2)
```

- [ ] **Step 6: Save combined result/class payloads**

Replace `_save` with:

```python
    def _save(self):
        current_results = {
            auto_num: var.get()
            for auto_num, var in self._vars.items()
        }
        current_classes = {
            auto_num: self._class_code_by_label.get(var.get(), var.get())
            for auto_num, var in self._class_vars.items()
        }
        payload = self.changed_payload(
            current_results,
            self._initial,
            current_classes,
            self._initial_classes,
        )
        moves = self.cross_category_moves(
            payload,
            self._active_category,
            self._class_categories,
        )
        if moves:
            msg = "\n".join(
                f"Exhibit #{auto_num} will move to {category}."
                for auto_num, category in moves
            )
            from tkinter import messagebox

            ok = messagebox.askyesno(
                "Class moves to another category",
                f"{msg}\n\nThese rows will disappear from this page after saving. Continue?",
                parent=self,
            )
            if not ok:
                return
        try:
            saved = save_category_results(payload)
        except JudgingCatalogueError as exc:
            self._status.configure(text=str(exc))
            return
        self._status.configure(text=f"Saved {saved} updates.")
        self._load_categories()
        if self._on_saved:
            self._on_saved()
```

- [ ] **Step 7: Run targeted import/helper tests**

Run:

```powershell
python -m pytest tests\test_judging_capture_imports.py -q
```

Expected: all tests pass.

---

## Task 4: Documentation and Verification

**Files:**
- Modify: `README.md`
- Modify: `views/help_view.py`

- [ ] **Step 1: Update README Judging Capture text**

In `README.md`, in the `Judging Capture` bullets under `### Results`, replace:

```markdown
- Select a category, choose radio-button results or NB/Clear per exhibit, then click `Save Category Results`
```

with:

```markdown
- Select a category, correct the class if the judge sheet shows a reallocation, choose radio-button results or NB/Clear per exhibit, then click `Save Category Results`
```

- [ ] **Step 2: Update in-app Help Judging Capture text**

In `views/help_view.py`, in the `Judging Capture` section, replace:

```python
            "5. For each exhibit, choose a placing, NB, or Clear using the radio buttons\n"
            "6. Click Save Category Results at the end of the category/page\n\n"
```

with:

```python
            "5. If needed, change the exhibit's class before saving\n"
            "6. For each exhibit, choose a placing, NB, or Clear using the radio buttons\n"
            "7. Click Save Category Results at the end of the category/page\n\n"
```

- [ ] **Step 3: Run targeted feature tests**

Run:

```powershell
python -m pytest tests\test_judging_catalogue_service.py tests\test_judges_catalogue_pdf.py tests\test_judging_capture_imports.py
```

Expected: all targeted tests pass.

- [ ] **Step 4: Run full test suite**

Run:

```powershell
python -m pytest tests
```

Expected: all tests pass.

- [ ] **Step 5: Do not commit until user testing is complete**

The user explicitly said they will test before commit. Leave the implementation uncommitted unless the user asks for a commit after testing.

---

## Self-Review

- Spec coverage: service-level class reallocation, invalid class rejection, cross-category warning, AutoNum preservation, UI class selector, docs, and verification are covered.
- Placeholder scan: no `TBD`, `TODO`, or vague "add tests later" steps remain.
- Type consistency: service payloads use `{auto_num: {"result": str, "class_code": str}}`; UI helper methods and service save function use the same shape.
