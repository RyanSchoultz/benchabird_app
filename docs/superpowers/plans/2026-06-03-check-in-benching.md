# Check-in Benching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Check-in/Benching as a top-level workflow that searches exhibitors and allocates AutoNum values only to birds that arrive.

**Architecture:** Add a focused `checkin_service` for search, row status, bench, and unbench behavior. Add a `CheckInView` UI that uses the service, wire it into sidebar/dashboard navigation, and make the sidebar scrollable for short screens.

**Tech Stack:** Python, Peewee, CustomTkinter, pytest.

---

## File Structure

- Modify `models/show_entry.py`: add nullable `CalculatedEntry.source_entry_auto_num`.
- Modify `main.py`: migrate existing databases with the new nullable column.
- Create `services/checkin_service.py`: pure check-in search, row listing, benching, and unbenching.
- Create `tests/test_checkin_service.py`: service coverage for search, benching, duplicate prevention, source links, and unbench blocking.
- Create `views/checkin_view.py`: operator UI for search, selected exhibitor entries, and bench/unbench actions.
- Modify `views/main_window.py`: add top-level Check-in and scrollable sidebar navigation.
- Modify `views/dashboard.py`: add Check-in quick action and update workflow wording.
- Modify `views/welcome_view.py`: update workflow wording/shortcut copy.
- Modify `README.md` and `views/help_view.py`: document Check-in/Benching.

---

## Task 1: Data Model and Check-in Service

- [ ] Add `source_entry_auto_num = IntegerField(null=True, index=True)` to `CalculatedEntry`.
- [ ] Add `ALTER TABLE calculated_entry ADD COLUMN source_entry_auto_num INTEGER` to `_migrate_db()`.
- [ ] Write tests in `tests/test_checkin_service.py`.
- [ ] Implement `services/checkin_service.py`.
- [ ] Run `python -m pytest tests\test_checkin_service.py -q`.

## Task 2: Check-in View and Navigation

- [ ] Create `views/checkin_view.py`.
- [ ] Add `("Check-in", "checkin")` to top-level sidebar navigation.
- [ ] Map `checkin` to `CheckInView`.
- [ ] Add `Ctrl+B` shortcut for Check-in.
- [ ] Wrap sidebar nav/admin buttons in a `CTkScrollableFrame`.
- [ ] Add import smoke tests for `CheckInView` and `MainWindow`.
- [ ] Run the check-in/import tests.

## Task 3: Dashboard, Help, README

- [ ] Add Dashboard quick action `Check In Birds`.
- [ ] Update dashboard workflow wording from Calculate to Check-in/Benching.
- [ ] Update welcome workflow wording and tips.
- [ ] Update README and in-app Help with the check-in flow.
- [ ] Run targeted tests.

## Task 4: Verification

- [ ] Run `python -m pytest tests`.
- [ ] Run `python -m PyInstaller benchabird.spec --clean`.
- [ ] Leave changes uncommitted for user testing.
