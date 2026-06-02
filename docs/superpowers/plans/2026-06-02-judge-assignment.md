# Judge Assignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-class judge assignment and display judges on class-facing PDF reports.

**Architecture:** Extend `ClassDef` with `judge`, migrate existing DBs, leave MDB imports blank, and join `class_def` in Show Catalogue and Results Sheet report queries. No new editing UI in this slice.

**Tech Stack:** Python, Peewee, SQLite, ReportLab, pytest

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `tests/test_models.py` | Modify | Verify `ClassDef.judge` persists |
| `tests/test_import_service.py` | Modify | Verify MDB import leaves class judges blank |
| `tests/test_show_catalogue_pdf.py` | Modify | Verify catalogue generates with judge data |
| `tests/test_results_sheet_pdf.py` | Modify | Verify results sheet generates with judge data |
| `models/class_def.py` | Modify | Add `judge` field |
| `main.py` | Modify | Add startup migration |
| `services/import_service.py` | Modify | Set `judge=None` on class import |
| `services/reports/show_catalogue.py` | Modify | Display judge in class headers |
| `services/reports/results_sheet.py` | Modify | Include judge column |
| `README.md` | Modify | Document judge assignment |

## Task 1: Failing Tests

**Files:**
- Modify: `tests/test_models.py`
- Modify: `tests/test_import_service.py`
- Modify: `tests/test_show_catalogue_pdf.py`
- Modify: `tests/test_results_sheet_pdf.py`

- [ ] **Step 1: Add tests**

Add tests for model persistence, import blank judge, and report generation with judge data.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_models.py tests/test_import_service.py tests/test_show_catalogue_pdf.py tests/test_results_sheet_pdf.py -v`

Expected: failures because `ClassDef.judge` does not exist.

## Task 2: Model, Migration, Import

**Files:**
- Modify: `models/class_def.py`
- Modify: `main.py`
- Modify: `services/import_service.py`

- [ ] **Step 1: Add field**

Add `judge = CharField(max_length=100, null=True)` to `ClassDef`.

- [ ] **Step 2: Add migration**

Add `ALTER TABLE class_def ADD COLUMN judge VARCHAR(100)` to `_migrate_db()`.

- [ ] **Step 3: Update import**

Set `'judge': None` in `_classes`.

- [ ] **Step 4: Run model/import tests**

Run: `python -m pytest tests/test_models.py tests/test_import_service.py -v`

Expected: pass.

## Task 3: Report Updates

**Files:**
- Modify: `services/reports/show_catalogue.py`
- Modify: `services/reports/results_sheet.py`

- [ ] **Step 1: Show Catalogue**

Select `COALESCE(cd.judge, '')`, include it in rows, and append `Judge: <name>` to class headers when present.

- [ ] **Step 2: Results Sheet**

Join `class_def`, select `COALESCE(cd.judge, '')`, add `Judge` to headers, and draw it in a right-side column.

- [ ] **Step 3: Run report tests**

Run: `python -m pytest tests/test_show_catalogue_pdf.py tests/test_results_sheet_pdf.py -v`

Expected: pass.

- [ ] **Step 4: Commit**

Commit message: `feat: add per-class judge assignments`

## Task 4: Docs And Final Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Document `class_def.judge`, blank behavior, and report locations.

- [ ] **Step 2: Run full tests**

Run: `python -m pytest tests/ -v --tb=short`

Expected: all tests pass.

- [ ] **Step 3: Commit docs**

Commit message: `docs: document judge assignment`

- [ ] **Step 4: Check status**

Run: `git status --short --branch`

Expected: clean working tree.
