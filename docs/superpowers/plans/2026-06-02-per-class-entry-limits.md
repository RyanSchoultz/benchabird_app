# Per-Class Entry Limits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional class capacity limits and enforce them for normal and late entries.

**Architecture:** Extend `ClassDef` with `entry_limit`, migrate existing DBs at startup, and centralize limit counting in entry services. Existing entry dialogs surface validation errors without new UI.

**Tech Stack:** Python, Peewee, SQLite, pytest, CustomTkinter

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `tests/test_entry_service.py` | Modify | Add normal-entry and bulk-add class limit tests |
| `tests/test_late_entry_service.py` | Create | Add late-entry class limit tests |
| `models/class_def.py` | Modify | Add `entry_limit` field |
| `main.py` | Modify | Add startup migration for existing DBs |
| `services/import_service.py` | Modify | Preserve MDB import behavior with `entry_limit=None` |
| `services/entry_service.py` | Modify | Enforce limits for normal entries |
| `services/late_entry_service.py` | Modify | Enforce limits for late entries |
| `README.md` | Modify | Document class limit behavior |

## Task 1: Failing Tests

**Files:**
- Modify: `tests/test_entry_service.py`
- Create: `tests/test_late_entry_service.py`

- [ ] **Step 1: Add normal entry limit tests**

Tests:

- unlimited class allows multiple different exhibitors.
- limit 1 blocks second normal entry.
- duplicate error appears before limit error.
- bulk add reports limit errors.

- [ ] **Step 2: Add late entry limit tests**

Tests:

- late entry respects a limit filled by normal entries.
- normal entry respects a limit filled by late entries.

- [ ] **Step 3: Verify RED**

Run: `python -m pytest tests/test_entry_service.py tests/test_late_entry_service.py -v`

Expected: failures because `ClassDef.entry_limit` does not exist and limit enforcement is not implemented.

## Task 2: Model, Migration, And Import

**Files:**
- Modify: `models/class_def.py`
- Modify: `main.py`
- Modify: `services/import_service.py`

- [ ] **Step 1: Add field**

Add `entry_limit = IntegerField(null=True)` to `ClassDef`.

- [ ] **Step 2: Add startup migration**

Add `ALTER TABLE class_def ADD COLUMN entry_limit INTEGER` to `main._migrate_db()`.

- [ ] **Step 3: Update MDB import**

Set `'entry_limit': None` in `_classes`.

- [ ] **Step 4: Run model-focused tests**

Run: `python -m pytest tests/test_models.py tests/test_import_service.py -v`

Expected: pass.

## Task 3: Entry Limit Enforcement

**Files:**
- Modify: `services/entry_service.py`
- Modify: `services/late_entry_service.py`

- [ ] **Step 1: Add shared count/check helpers**

Count `ShowEntry` and `LateEntry` rows for the class code. Treat `None` and `0` as unlimited.

- [ ] **Step 2: Enforce in normal entries**

Call the helper after duplicate validation and before creating the entry.

- [ ] **Step 3: Enforce in late entries**

Call the helper before creating the late entry.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_entry_service.py tests/test_late_entry_service.py -v`

Expected: all focused tests pass.

- [ ] **Step 5: Commit**

Commit message: `feat: enforce per-class entry limits`

## Task 4: Docs And Final Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Document `class_def.entry_limit`, unlimited behavior for blank/0, and that normal plus late entries count together.

- [ ] **Step 2: Run full tests**

Run: `python -m pytest tests/ -v --tb=short`

Expected: all tests pass.

- [ ] **Step 3: Commit docs**

Commit message: `docs: document per-class entry limits`

- [ ] **Step 4: Check status**

Run: `git status --short --branch`

Expected: clean working tree.
