# Release Starter Database Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a release-only starter database flow that bundles a clean DB with synthetic `_Demo` exhibitors while preserving the local development DB.

**Architecture:** Add a focused script that creates `release/benchabird.db` from the current schema and safe reference data. Update PyInstaller packaging to bundle that starter artifact as `benchabird.db`. Tests validate the generated database contract and packaging path.

**Tech Stack:** Python, SQLite, Peewee models, pytest, PyInstaller spec

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `scripts/create_starter_db.py` | Create | Generate and validate the release starter DB without mutating local `benchabird.db` |
| `tests/test_create_starter_db.py` | Create | Verify starter DB contents and source DB preservation |
| `benchabird.spec` | Modify | Bundle `release/benchabird.db` as `benchabird.db` |
| `README.md` | Modify | Document the release DB generation step and local/dev DB separation |
| `release/.gitignore` | Create | Keep generated starter DB out of git while preserving the release directory |

## Task 1: Failing Tests For Starter DB Script

**Files:**
- Create: `tests/test_create_starter_db.py`

- [ ] **Step 1: Add tests**

Create tests that build a temporary source DB with reference rows and historical/show rows, run `create_starter_db`, and assert the destination has only approved data.

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m pytest tests/test_create_starter_db.py -v`

Expected: import error because `scripts.create_starter_db` does not exist.

## Task 2: Starter DB Generator

**Files:**
- Create: `scripts/create_starter_db.py`

- [ ] **Step 1: Implement script**

The module should expose:

```python
DEFAULT_SOURCE = ROOT / "benchabird.db"
DEFAULT_DEST = ROOT / "release" / "benchabird.db"
REFERENCE_TABLES = ("class_def", "species", "main_class")
EMPTY_TABLES = (
    "show_entry", "calculated_entry", "late_entry", "result", "not_benched",
    "special_winner", "special_list", "hall_of_fame", "ticket_number",
    "brochure_sequence", "notes_brochure", "number_seq",
)
DEMO_EXHIBITORS = (
    {"exh_no": 1, "name": "Alpha_Demo", "town": "Demo Town", "club": "Demo Club"},
    {"exh_no": 2, "name": "Beta_Demo", "town": "Demo Town", "club": "Demo Club"},
    {"exh_no": 3, "name": "Gamma_Demo", "town": "Demo Town", "club": "Demo Club"},
)
```

Implementation requirements:

- Create the destination schema using `ALL_MODELS` bound to a temporary Peewee `SqliteDatabase`.
- Copy only `class_def`, `species`, and `main_class` rows from the source DB if those tables exist.
- Create one safe starter `show_details` row with generic Benchabird values.
- Insert only the synthetic `_Demo` exhibitors.
- Validate that every exhibitor name ends with `_Demo`.
- Validate that every table in `EMPTY_TABLES` has zero rows.
- Never overwrite the source DB.
- Replace an existing destination DB only when it is not the source path.
- Provide a CLI entry point for `python scripts/create_starter_db.py`.

- [ ] **Step 2: Run focused tests**

Run: `python -m pytest tests/test_create_starter_db.py -v`

Expected: all starter DB script tests pass.

- [ ] **Step 3: Generate local release starter DB**

Run: `python scripts/create_starter_db.py`

Expected: `release/benchabird.db` is created and validation output reports demo exhibitors and empty operational tables.

- [ ] **Step 4: Commit**

Commit message: `feat: add release starter database generator`

## Task 3: Release Packaging And Docs

**Files:**
- Modify: `benchabird.spec`
- Modify: `README.md`
- Create: `release/.gitignore`

- [ ] **Step 1: Update PyInstaller spec**

Change the data bundle entry from:

```python
('benchabird.db', '.'),
```

to:

```python
('release/benchabird.db', '.'),
```

- [ ] **Step 2: Add release directory gitignore**

Create `release/.gitignore`:

```gitignore
*
!.gitignore
```

- [ ] **Step 3: Update README build section**

Document:

- Local development still uses `benchabird.db`.
- Releases use `release/benchabird.db`.
- Run `python scripts/create_starter_db.py` before `python -m PyInstaller benchabird.spec --clean`.
- The starter DB contains reference classes/categories and synthetic `_Demo` exhibitors only.

- [ ] **Step 4: Run focused validation**

Run:

```powershell
python -m pytest tests/test_create_starter_db.py -v
python scripts/create_starter_db.py
```

Expected: tests pass and starter DB is regenerated.

- [ ] **Step 5: Commit**

Commit message: `chore: package starter database for releases`

## Task 4: Final Verification

- [ ] **Step 1: Run full tests**

Run: `python -m pytest tests/ -v --tb=short`

Expected: all tests pass.

- [ ] **Step 2: Verify git status**

Run: `git status --short --branch`

Expected: clean working tree, branch ahead of origin only by local commits.
