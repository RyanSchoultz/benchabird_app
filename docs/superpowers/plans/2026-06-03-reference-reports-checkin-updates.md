# Reference Reports Check-in Updates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add seeded class glossary data with species grouping, non-destructive check-in allocation ordering, Access catalogue reports 4.1-4.4, and a manual update checker.

**Architecture:** Keep imported `class_def`/`species` as source of truth and add a denormalized `class_glossary` table for fast UI browsing. Keep global `0010_calculate` as legacy admin behavior while Check-in uses a focused allocator. Add report/update services behind the existing Reports and Help/UI patterns.

**Tech Stack:** Python, Peewee, CustomTkinter, ReportLab, urllib, pytest, PyInstaller.

---

## File Structure

- Create `models/class_glossary.py`: denormalized glossary table.
- Modify `models/__init__.py`: include `ClassGlossary` in `ALL_MODELS`.
- Modify `main.py`: create and seed glossary table at startup.
- Modify `services/import_service.py`: reseed glossary after class/species import.
- Modify `services/class_glossary_service.py`: seed/search/list from `class_glossary`.
- Modify `views/notes_view.py`: species filter/group headings.
- Modify `services/checkin_service.py`: sorted non-destructive allocation helper.
- Create `services/reports/special_lists.py`: Access 4.2 report.
- Create `services/reports/marked_catalogue.py`: Access 4.4 report.
- Modify `views/reports_view.py`: catalogue group buttons 4.1-4.4.
- Create `services/update_service.py`: version check, release asset parsing, download staging, helper script text.
- Modify `views/help_view.py`: add Check for Updates button and startup changelog popup support if appropriate.
- Modify `README.md`: document workflows.
- Add tests under `tests/` for each service/view import path.

## Task 1: Seeded Class Glossary

- [x] Add failing tests in `tests/test_class_glossary_seed_service.py` for model creation, seeding from `ClassDef`/`Species`, ordering, species filters, and search.
- [x] Run `python -m pytest tests\test_class_glossary_seed_service.py -q` and verify failure.
- [x] Create `models/class_glossary.py`.
- [x] Add `ClassGlossary` to `models/__init__.py`.
- [x] Update `services/class_glossary_service.py` with `seed_class_glossary`, `list_species_filters`, and table-backed `list_class_glossary`.
- [x] Update `main.py` startup to create/seed the table.
- [x] Update `services/import_service.py` to reseed after import.
- [x] Run glossary seed tests and verify pass.

## Task 2: Species Filter UI

- [x] Add/update view tests for importing `NotesView` and helper functions.
- [x] Update `views/notes_view.py` to add an `All species` dropdown and species group headings.
- [x] Keep render cap/debounce behavior.
- [x] Run `python -m pytest tests\test_class_glossary_service.py tests\test_class_glossary_seed_service.py tests\test_class_glossary_view_imports.py tests\test_class_glossary_view_rendering.py -q`.

## Task 3: Check-in Allocation Ordering

- [x] Add failing tests in `tests/test_checkin_service.py` proving selected entries for one exhibitor are allocated by `ClassDef.class_seq` then source entry number.
- [x] Update `services/checkin_service.py` so `bench_entries` sorts selected entries using class sequence before allocating exhibit numbers.
- [x] Keep skip behavior for already-benched entries.
- [x] Run `python -m pytest tests\test_checkin_service.py -q`.

## Task 4: Catalogue Reports 4.1-4.4

- [x] Add PDF tests for new `special_lists` and `marked_catalogue` reports.
- [x] Implement `services/reports/special_lists.py`.
- [x] Implement `services/reports/marked_catalogue.py`.
- [x] Update `views/reports_view.py` to expose `4.1 Judges Catalogue`, `4.2 Special Lists`, `4.3 Catalogue`, and `4.4 Marked Catalogue`.
- [x] Run report tests and report view import tests.

## Task 5: Update Service

- [x] Add tests in `tests/test_update_service.py` for semantic version comparison, latest exe asset selection, and dev-mode replacement guard.
- [x] Implement `services/update_service.py` using stdlib `urllib.request` and no new dependency.
- [x] Add a Help view button for manual update checks.
- [x] In frozen mode only, allow download/restart via generated PowerShell helper.
- [x] Store pending changelog text for display on next launch.
- [x] Run update service tests.

## Task 6: Documentation and Verification

- [x] Update README and Help text for class glossary/species, check-in allocation, catalogue reports 4.1-4.4, and manual updates.
- [x] Run `python -m pytest tests`.
- [x] Run `python -m PyInstaller benchabird.spec --clean`.
- [x] Leave application changes uncommitted for user testing.
