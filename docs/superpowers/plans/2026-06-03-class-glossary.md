# Class Glossary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the visible Notes screen with a read-only Class Glossary sourced from `class_def`.

**Architecture:** Add a small pure service for class glossary formatting/filtering, then update the existing `notes` route view to render the glossary while preserving the route key and existing notes data/model. Navigation/docs copy change from Notes to Class Glossary.

**Tech Stack:** Python, Peewee, CustomTkinter, pytest.

---

## File Structure

- Create `services/class_glossary_service.py`: glossary row dataclass, description formatting, listing/filtering.
- Create `tests/test_class_glossary_service.py`: pure formatting/filtering/order tests.
- Modify `views/notes_view.py`: replace brochure note editor with read-only glossary UI.
- Create `tests/test_class_glossary_view_imports.py`: import smoke test.
- Modify `views/main_window.py`: visible sidebar label from `Notes` to `Class Glossary`, keep key `notes`.
- Modify `README.md` and `views/help_view.py`: update feature/help text.

---

## Task 1: Service

- [x] Write failing `tests/test_class_glossary_service.py`.
- [x] Run `python -m pytest tests\test_class_glossary_service.py -q` and verify failure.
- [x] Implement `services/class_glossary_service.py`.
- [x] Run service tests and verify pass.

## Task 2: UI and Navigation

- [x] Replace `views/notes_view.py` with read-only Class Glossary UI.
- [x] Add import smoke test.
- [x] Rename sidebar label to `Class Glossary`.
- [x] Run `python -m pytest tests\test_class_glossary_service.py tests\test_class_glossary_view_imports.py -q`.

## Task 3: Documentation and Verification

- [x] Update README and Help text.
- [x] Run `python -m pytest tests`.
- [x] Run `python -m PyInstaller benchabird.spec --clean`.
- [x] Leave changes uncommitted for user testing.
