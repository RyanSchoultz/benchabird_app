# Exhibitor Spreadsheet Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add CSV/Excel exhibitor import from the Exhibitors screen without affecting entries, classes, results, or show data.

**Architecture:** Create a focused `services/exhibitor_import_service.py` that reads a spreadsheet path, normalizes column aliases, upserts exhibitors, and returns an import summary. Wire that service into `views/exhibitors_view.py` through a file picker and message box. Keep legacy full-MDB import unchanged.

**Tech Stack:** Python, pandas, Peewee, CustomTkinter, pytest

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `tests/test_exhibitor_import_service.py` | Create | Validate CSV/XLSX import behavior and error summaries |
| `services/exhibitor_import_service.py` | Create | Parse spreadsheet rows and upsert exhibitors |
| `views/exhibitors_view.py` | Modify | Add Import button and result message |
| `README.md` | Modify | Document supported file types and columns |

## Task 1: Failing Service Tests

**Files:**
- Create: `tests/test_exhibitor_import_service.py`

- [ ] **Step 1: Write tests**

Cover CSV creation, XLSX creation, alias mapping, idempotent update, and bad row handling.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_exhibitor_import_service.py -v`

Expected: `ModuleNotFoundError: No module named 'services.exhibitor_import_service'`.

## Task 2: Import Service

**Files:**
- Create: `services/exhibitor_import_service.py`

- [ ] **Step 1: Implement result dataclass**

Expose `ImportSummary(created: int, updated: int, skipped: int, errors: list[str])`.

- [ ] **Step 2: Implement `import_exhibitors_from_spreadsheet(path) -> ImportSummary`**

Behavior:

- Read `.csv` with `pd.read_csv`.
- Read `.xlsx`/`.xls` with `pd.read_excel`.
- Normalize known column aliases to `Exhibitor` fields.
- Skip rows without `name`.
- Parse `exh_no` as int when possible.
- Parse `print_address` as bool.
- Match existing exhibitors by `exh_no` first, then by exact `name`.
- Update matches, create non-matches.
- Return created/updated/skipped/errors counts.

- [ ] **Step 3: Run focused tests**

Run: `python -m pytest tests/test_exhibitor_import_service.py -v`

Expected: all tests pass.

- [ ] **Step 4: Commit**

Commit message: `feat: add exhibitor spreadsheet import service`

## Task 3: Exhibitors UI Wiring

**Files:**
- Modify: `views/exhibitors_view.py`

- [ ] **Step 1: Add Import button**

Place an `Import` button near Export in the toolbar.

- [ ] **Step 2: Add `_import_spreadsheet` handler**

Use `tkinter.filedialog.askopenfilename` with CSV/Excel file types. Call `import_exhibitors_from_spreadsheet`, reload the table, and show a `messagebox.showinfo` summary. On exceptions, show `messagebox.showerror`.

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/test_exhibitor_import_service.py -v`

Expected: service tests still pass.

- [ ] **Step 4: Commit**

Commit message: `feat: wire exhibitor spreadsheet import UI`

## Task 4: Documentation And Final Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Document the Exhibitors Import button, file types, and recommended columns.

- [ ] **Step 2: Run full tests**

Run: `python -m pytest tests/ -v --tb=short`

Expected: all tests pass.

- [ ] **Step 3: Commit**

Commit message: `docs: document exhibitor spreadsheet import`

- [ ] **Step 4: Check status**

Run: `git status --short --branch`

Expected: clean working tree.
