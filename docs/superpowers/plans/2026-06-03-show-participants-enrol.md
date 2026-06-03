# Show Participants Enrol & Query Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the bug where Show Participants shows "No participants found" for exhibitors with ExhNos but no entries, and add a bulk Enrol dialog to assign ExhNos to multiple exhibitors at once.

**Architecture:** Three changes: (1) remove the entry-existence requirement from `get_participants()`, (2) add `get_unenrolled_exhibitors()` and `enrol_exhibitors()` service functions, (3) create an `_EnrolDialog` view and wire it into the left panel with a button; also simplify the single-click registry add to auto-assign without a prompt.

**Tech Stack:** Python 3.14, peewee ORM, customtkinter, pytest (in-memory SQLite via conftest.py)

---

## File Map

| Action | File |
|---|---|
| Modify | `services/show_participants_service.py` |
| Modify | `tests/test_show_participants_service.py` |
| Create | `views/_enrol_dialog.py` |
| Modify | `views/show_participants_view.py` |

---

## Task 1: Fix `get_participants()` — show exhibitors with ExhNo regardless of entries

The current query requires `EXISTS entries OR EXISTS late_entries`. Remove that condition so any exhibitor with `exh_no IS NOT NULL` appears, even with 0 entries.

**Files:**
- Modify: `services/show_participants_service.py:32-55`
- Modify: `tests/test_show_participants_service.py`

- [ ] **Step 1: Update the existing test that will now be wrong**

In `tests/test_show_participants_service.py`, replace:

```python
def test_get_participants_returns_only_exhibitors_with_entries(test_db):
    from services.show_participants_service import get_participants
    _seed(test_db)
    rows = get_participants()
    assert [r.exh_no for r in rows] == [1, 2]
```

With:

```python
def test_get_participants_returns_exhibitors_with_exh_no(test_db):
    from services.show_participants_service import get_participants
    _seed(test_db)
    # Exhibitor with exh_no=1 has entries; exh_no=2 also has entries.
    # Cupido (exh_no=None) must NOT appear.
    rows = get_participants()
    exh_nos = [r.exh_no for r in rows]
    assert 1 in exh_nos
    assert 2 in exh_nos
    assert None not in exh_nos


def test_get_participants_includes_exhibitor_with_no_entries(test_db):
    from services.show_participants_service import get_participants
    Exhibitor.create(id=10, exh_no=5, name="Zero Entry Person")
    # No ShowEntry or LateEntry for exh_no=5
    rows = get_participants()
    assert any(r.exh_no == 5 for r in rows)
    zero = next(r for r in rows if r.exh_no == 5)
    assert zero.entry_count == 0
    assert zero.benched_count == 0
```

- [ ] **Step 2: Run to verify new test fails**

```
cd benchabird_app
pytest tests/test_show_participants_service.py::test_get_participants_includes_exhibitor_with_no_entries -v
```

Expected: `FAILED` — exhibitor with no entries not returned

- [ ] **Step 3: Fix the query in `services/show_participants_service.py`**

Replace the `WHERE` clause (lines 48–53):

```python
    cursor = db.execute_sql("""
        SELECT
            e.id,
            e.exh_no,
            e.name,
            e.email,
            (SELECT COUNT(*) FROM show_entry WHERE exh_no = e.exh_no) +
            (SELECT COUNT(*) FROM late_entry  WHERE exh_no = e.exh_no) AS entry_count,
            (SELECT COUNT(*) FROM calculated_entry
                WHERE source_entry_auto_num IN
                    (SELECT auto_num FROM show_entry WHERE exh_no = e.exh_no)) +
            (SELECT COUNT(*) FROM calculated_entry
                WHERE source_late_entry_auto_num IN
                    (SELECT auto_num FROM late_entry WHERE exh_no = e.exh_no)) AS benched_count,
            (SELECT COUNT(*) FROM late_entry WHERE exh_no = e.exh_no) AS late_count
        FROM exhibitor e
        WHERE e.exh_no IS NOT NULL
        ORDER BY e.exh_no
    """)
```

- [ ] **Step 4: Run all service tests to verify they pass**

```
pytest tests/test_show_participants_service.py -v
```

Expected: all pass

- [ ] **Step 5: Run full suite**

```
pytest tests/ -q --tb=short
```

Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add services/show_participants_service.py tests/test_show_participants_service.py
git commit -m "fix: get_participants returns all exhibitors with ExhNo regardless of entries"
```

---

## Task 2: Add `get_unenrolled_exhibitors()` and `enrol_exhibitors()`

**Files:**
- Modify: `services/show_participants_service.py`
- Modify: `tests/test_show_participants_service.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_show_participants_service.py`:

```python
def test_get_unenrolled_exhibitors_returns_only_null_exh_no(test_db):
    from services.show_participants_service import get_unenrolled_exhibitors
    _seed(test_db)
    # Seed has Exhibitor id=3 with exh_no=None (Cupido, C.)
    results = get_unenrolled_exhibitors()
    assert all(e.exh_no is None for e in results)
    assert any(e.name == "Cupido, C." for e in results)


def test_get_unenrolled_exhibitors_filters_by_name(test_db):
    from services.show_participants_service import get_unenrolled_exhibitors
    _seed(test_db)
    results = get_unenrolled_exhibitors("Cupido")
    assert len(results) == 1
    assert results[0].name == "Cupido, C."


def test_get_unenrolled_exhibitors_empty_when_all_enrolled(test_db):
    from services.show_participants_service import get_unenrolled_exhibitors
    Exhibitor.create(exh_no=1, name="Only One")
    results = get_unenrolled_exhibitors()
    assert results == []


def test_enrol_exhibitors_assigns_sequential_exh_nos_alphabetically(test_db):
    from services.show_participants_service import enrol_exhibitors
    # Create unenrolled exhibitors — names NOT in alphabetical order on purpose
    z = Exhibitor.create(exh_no=None, name="Zulu, Z.")
    a = Exhibitor.create(exh_no=None, name="Adams, A.")
    m = Exhibitor.create(exh_no=None, name="Meyer, M.")
    count = enrol_exhibitors([z.id, a.id, m.id])
    assert count == 3
    # Should be alphabetical: Adams=1, Meyer=2, Zulu=3
    assert Exhibitor.get_by_id(a.id).exh_no == 1
    assert Exhibitor.get_by_id(m.id).exh_no == 2
    assert Exhibitor.get_by_id(z.id).exh_no == 3


def test_enrol_exhibitors_starts_after_existing_exh_nos(test_db):
    from services.show_participants_service import enrol_exhibitors
    Exhibitor.create(exh_no=5, name="Existing")
    new = Exhibitor.create(exh_no=None, name="New Person")
    enrol_exhibitors([new.id])
    assert Exhibitor.get_by_id(new.id).exh_no == 6


def test_enrol_exhibitors_empty_list_returns_zero(test_db):
    from services.show_participants_service import enrol_exhibitors
    assert enrol_exhibitors([]) == 0
```

- [ ] **Step 2: Run to verify they fail**

```
pytest tests/test_show_participants_service.py::test_get_unenrolled_exhibitors_returns_only_null_exh_no -v
```

Expected: `FAILED` — function not defined

- [ ] **Step 3: Append functions to `services/show_participants_service.py`**

Add after the `assign_exh_no` function:

```python
def get_unenrolled_exhibitors(query: str = "") -> list[Exhibitor]:
    """All exhibitors with no ExhNo assigned, optionally filtered by name."""
    q = (query or "").strip()
    base = Exhibitor.select().where(Exhibitor.exh_no.is_null(True))
    if q:
        base = base.where(Exhibitor.name.contains(q))
    return list(base.order_by(Exhibitor.name))


def enrol_exhibitors(exhibitor_ids: list[int]) -> int:
    """
    Assign sequential ExhNos to the given exhibitors in alphabetical name order.
    Starts from next_available_exh_no(). Returns count enrolled.
    """
    if not exhibitor_ids:
        return 0
    exhibitors = list(
        Exhibitor.select()
        .where(Exhibitor.id.in_(exhibitor_ids))
        .order_by(Exhibitor.name)
    )
    start = next_available_exh_no()
    db = Exhibitor._meta.database
    with db.atomic():
        for i, exhibitor in enumerate(exhibitors):
            exhibitor.exh_no = start + i
            exhibitor.save()
    return len(exhibitors)
```

- [ ] **Step 4: Run to verify they pass**

```
pytest tests/test_show_participants_service.py -v
```

Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add services/show_participants_service.py tests/test_show_participants_service.py
git commit -m "feat: add get_unenrolled_exhibitors and enrol_exhibitors to service"
```

---

## Task 3: Create `views/_enrol_dialog.py`

**Files:**
- Create: `views/_enrol_dialog.py`

No behavioural tests for CTK views. Smoke test only (import test).

- [ ] **Step 1: Write smoke test**

Append to `tests/test_show_participants_view_imports.py`:

```python
def test_enrol_dialog_imports(test_db):
    from views._enrol_dialog import EnrolDialog
    assert EnrolDialog.__name__ == "EnrolDialog"
```

- [ ] **Step 2: Run to verify it fails**

```
pytest tests/test_show_participants_view_imports.py -v
```

Expected: `FAILED` — module not found

- [ ] **Step 3: Create `views/_enrol_dialog.py`**

```python
# views/_enrol_dialog.py
import customtkinter as ctk
from services.show_participants_service import get_unenrolled_exhibitors, enrol_exhibitors


class EnrolDialog(ctk.CTkToplevel):
    """Bulk-enrol exhibitors into the current show by assigning sequential ExhNos."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Enrol Exhibitors for This Show")
        self.geometry("480x520")
        self.resizable(False, True)
        self.grab_set()
        self.after(50, self.lift)
        self._all_exhibitors = []
        self._vars: dict[int, ctk.BooleanVar] = {}
        self._build()
        self._load()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Filter bar
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 4))
        filter_frame.grid_columnconfigure(0, weight=1)
        self._filter_var = ctk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())
        ctk.CTkEntry(
            filter_frame, textvariable=self._filter_var,
            placeholder_text="Filter by name…",
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            filter_frame, text="✕", width=28, height=28,
            fg_color="transparent", text_color=("gray40", "gray60"),
            command=lambda: self._filter_var.set(""),
        ).grid(row=0, column=1, padx=(4, 0))

        # Select All row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=1, column=0, sticky="ew", padx=16, pady=(4, 0))
        self._select_all_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            header, text="Select All",
            variable=self._select_all_var,
            command=self._toggle_all,
        ).pack(side="left")
        self._count_lbl = ctk.CTkLabel(
            header, text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        self._count_lbl.pack(side="right")

        # Scrollable exhibitor list
        self._list = ctk.CTkScrollableFrame(self)
        self._list.grid(row=2, column=0, sticky="nsew", padx=16, pady=8)
        self._list.grid_columnconfigure(1, weight=1)

        # Buttons
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=3, column=0, pady=(4, 16))
        ctk.CTkButton(
            btns, text="Cancel", width=110,
            fg_color="transparent", border_width=1,
            command=self.destroy,
        ).pack(side="left", padx=8)
        self._enrol_btn = ctk.CTkButton(
            btns, text="Enrol Selected (0)", width=180,
            command=self._enrol,
            state="disabled",
        )
        self._enrol_btn.pack(side="left", padx=8)
        self.bind("<Escape>", lambda e: self.destroy())

    def _load(self):
        self._all_exhibitors = get_unenrolled_exhibitors()
        self._vars = {e.id: ctk.BooleanVar(value=False) for e in self._all_exhibitors}
        self._apply_filter()

    def _apply_filter(self):
        q = self._filter_var.get().strip().lower()
        visible = [
            e for e in self._all_exhibitors
            if not q or q in (e.name or "").lower()
        ]
        for child in self._list.winfo_children():
            child.destroy()
        for row_i, exhibitor in enumerate(visible):
            var = self._vars[exhibitor.id]
            row = ctk.CTkFrame(self._list, fg_color="transparent")
            row.grid(row=row_i, column=0, sticky="ew", pady=1)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkCheckBox(
                row, text="", variable=var, width=32,
                command=self._update_counts,
            ).grid(row=0, column=0, padx=(0, 8))
            ctk.CTkLabel(
                row, text=exhibitor.name or "", anchor="w",
            ).grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(
                row,
                text=exhibitor.town or "",
                font=ctk.CTkFont(size=11),
                text_color=("gray40", "gray60"),
                anchor="e",
            ).grid(row=0, column=2, sticky="e", padx=(8, 0))
        total_left = len(self._all_exhibitors)
        self._count_lbl.configure(text=f"{total_left} unenrolled")
        self._update_counts()

    def _toggle_all(self):
        state = self._select_all_var.get()
        q = self._filter_var.get().strip().lower()
        for e in self._all_exhibitors:
            if not q or q in (e.name or "").lower():
                self._vars[e.id].set(state)
        self._update_counts()

    def _update_counts(self):
        selected = sum(1 for v in self._vars.values() if v.get())
        if selected:
            self._enrol_btn.configure(
                text=f"Enrol Selected ({selected})", state="normal",
            )
        else:
            self._enrol_btn.configure(text="Enrol Selected (0)", state="disabled")

    def _enrol(self):
        selected_ids = [eid for eid, v in self._vars.items() if v.get()]
        if not selected_ids:
            return
        enrol_exhibitors(selected_ids)
        self.destroy()
```

- [ ] **Step 4: Run to verify smoke test passes**

```
pytest tests/test_show_participants_view_imports.py -v
```

Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add views/_enrol_dialog.py tests/test_show_participants_view_imports.py
git commit -m "feat: add EnrolDialog for bulk exhibitor enrolment"
```

---

## Task 4: Wire Enrol button into ShowParticipantsView + fix single-click add

**Files:**
- Modify: `views/show_participants_view.py`

- [ ] **Step 1: Add "Enrol…" button to `_build_left()`**

In `views/show_participants_view.py`, replace the header label block in `_build_left()`:

```python
        # Header row with title + Enrol button
        header_row = ctk.CTkFrame(left, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        header_row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header_row, text="Show Participants",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            header_row, text="Enrol…", width=70, height=28,
            command=self._open_enrol_dialog,
        ).grid(row=0, column=1)
```

The old single label was:

```python
        ctk.CTkLabel(
            left, text="Show Participants",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))
```

- [ ] **Step 2: Add `_open_enrol_dialog()` method**

Add this method to `ShowParticipantsView` (after `_show_orphaned`):

```python
    def _open_enrol_dialog(self):
        from views._enrol_dialog import EnrolDialog
        dlg = EnrolDialog(self)
        self.wait_window(dlg)
        self._refresh_left()
```

- [ ] **Step 3: Fix `_add_registry_exhibitor()` — remove the prompt, auto-assign immediately**

Replace the current `_add_registry_exhibitor` method:

```python
    def _add_registry_exhibitor(self, exhibitor):
        if exhibitor.exh_no is None:
            assign_exh_no(exhibitor.id, next_available_exh_no())
            exhibitor = type(exhibitor).__class__  # force reload below
        # Reload from DB to get fresh exh_no
        from models.exhibitor import Exhibitor as ExhibitorModel
        fresh = ExhibitorModel.get_by_id(exhibitor.id)
        self._refresh_left()
        updated = next(
            (p for p in self._participants if p.exh_no == fresh.exh_no), None
        )
        if updated:
            self._select_participant(updated)
```

Wait — there's a simpler way to do this cleanly since we already import `assign_exh_no` and `next_available_exh_no`. Replace the entire `_add_registry_exhibitor` and `_prompt_assign_exh_no` methods with:

```python
    def _add_registry_exhibitor(self, exhibitor):
        if exhibitor.exh_no is None:
            new_no = next_available_exh_no()
            assign_exh_no(exhibitor.id, new_no)
            self._refresh_left()
            updated = next(
                (p for p in self._participants if p.exh_no == new_no), None
            )
            if updated:
                self._select_participant(updated)
        else:
            self._select_participant(ParticipantRow(
                exhibitor_id=exhibitor.id,
                exh_no=exhibitor.exh_no,
                name=exhibitor.name,
                email=exhibitor.email,
                entry_count=0, benched_count=0, late_count=0,
            ))
```

Also delete the `_prompt_assign_exh_no` method entirely — it is no longer used.

- [ ] **Step 4: Run full suite**

```
pytest tests/ -q --tb=short
```

Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add views/show_participants_view.py
git commit -m "feat: add Enrol button to Show Participants + auto-assign ExhNo on single-click add"
```

---

## Self-Review

**Spec coverage:**
- [x] Fix `get_participants()` query → Task 1
- [x] `get_unenrolled_exhibitors()` → Task 2
- [x] `enrol_exhibitors()` (alphabetical, sequential) → Task 2
- [x] Enrol dialog (filter, Select All, count label, disabled button) → Task 3
- [x] Enrol button in left panel header → Task 4
- [x] Single-click auto-assign (no prompt) → Task 4
- [x] `test_get_participants_returns_only_exhibitors_with_entries` renamed/updated → Task 1

**No placeholders:** All steps contain complete code.

**Type consistency:** `enrol_exhibitors(exhibitor_ids: list[int])` defined in Task 2, called in Task 3 `_enrol_dialog.py` and Task 4 `_add_registry_exhibitor`. `get_unenrolled_exhibitors()` defined in Task 2, called in Task 3. All consistent.
