# Show Participants — Enrol & Query Fix Design Spec
**Date:** 2026-06-03
**Status:** Approved

---

## Problem

Two related issues in Show Participants:

1. **Bug — empty participant list:** `get_participants()` requires exhibitors to have at least one `ShowEntry` or `LateEntry` to appear. Exhibitors with an ExhNo but no entries yet are invisible. The page shows "No participants found." even when exhibitors have been assigned to the show.

2. **Workflow gap — no bulk enrolment:** There is no way to select multiple exhibitors from the master registry and enrol them in a show at once. The current search `+` flow adds one person at a time and shows an ExhNo prompt. The correct pre-show workflow is: enrol all entrants first (assign ExhNos), then add their class entries.

---

## Correct Mental Model

**ExhNo = enrolled in this show.** An exhibitor is a show participant as soon as they have an ExhNo — entries come after. The participant list must reflect this.

Workflow:
```
1. Enrol exhibitors (assign ExhNos in bulk)
2. Add class entries per exhibitor
3. Show day: bench arrived birds
```

---

## Changes

### 1. Fix `get_participants()` query

**File:** `services/show_participants_service.py`

Remove the `AND (EXISTS entries OR EXISTS late_entries)` condition. The only requirement to appear in Show Participants is `exh_no IS NOT NULL`.

```sql
-- Before
WHERE e.exh_no IS NOT NULL
  AND (
    EXISTS (SELECT 1 FROM show_entry WHERE exh_no = e.exh_no)
    OR EXISTS (SELECT 1 FROM late_entry WHERE exh_no = e.exh_no)
  )

-- After
WHERE e.exh_no IS NOT NULL
```

Exhibitors with 0 entries appear with `entry_count = 0, benched_count = 0`.

The **Unbenched filter chip** is unchanged (`entry_count > benched_count`) — an exhibitor with 0 entries does not appear under Unbenched because there is nothing to bench yet.

### 2. New service functions

**File:** `services/show_participants_service.py`

```python
def get_unenrolled_exhibitors(query: str = "") -> list[Exhibitor]:
    """All exhibitors with exh_no IS NULL, optionally filtered by name."""

def enrol_exhibitors(exhibitor_ids: list[int]) -> int:
    """
    Assign sequential ExhNos to selected exhibitors.
    Order: alphabetical by name.
    Starting value: next_available_exh_no().
    Returns count enrolled.
    """
```

### 3. Enrol dialog

**File:** `views/_enrol_dialog.py`

A `CTkToplevel` dialog:

```
┌─────────────────────────────────────────────────┐
│  Enrol Exhibitors for This Show                 │
│  [Filter by name…                          ] [✕]│
│  ──────────────────────────────────────────────  │
│  ☑ Select All                    24 of 175 left │
│  ──────────────────────────────────────────────  │
│  ☐  Abrahams, Andre.    Cape Town               │
│  ☑  Botha, Jan.         Johannesburg            │
│  ☑  De Villiers, P.     Pretoria                │
│  ...                                             │
│  ──────────────────────────────────────────────  │
│     [Cancel]        [Enrol Selected  (2)  ▶]    │
└─────────────────────────────────────────────────┘
```

**Behaviour:**
- Only shows exhibitors with `exh_no IS NULL`
- Filter narrows list live; "Select All" selects all currently visible rows
- Enrol button label shows selected count; disabled when 0 selected
- On confirm: calls `enrol_exhibitors(selected_ids)` → ExhNos auto-assigned sequentially in alphabetical name order
- Dialog closes; left panel refreshes

### 4. Show Participants view updates

**File:** `views/show_participants_view.py`

- Add **Enrol…** button next to "Show Participants" header in left panel
- `_open_enrol_dialog()` method opens `_EnrolDialog`, waits, then calls `_refresh_left()`
- `_add_registry_exhibitor()`: remove the ExhNo prompt — just call `assign_exh_no(exhibitor.id, next_available_exh_no())` and select the exhibitor immediately

---

## Updated Left Panel Header

```
┌────────────────────────────────┐
│ Show Participants  [Enrol…]    │
│ [Search…                  ] [✕]│
│ [All] [Unbenched] [Late]       │
└────────────────────────────────┘
```

---

## File Map

| Action | File |
|---|---|
| Modify | `services/show_participants_service.py` |
| Create | `views/_enrol_dialog.py` |
| Modify | `views/show_participants_view.py` |
| Modify | `tests/test_show_participants_service.py` |

---

## Test Changes

- `test_get_participants_returns_only_exhibitors_with_entries` — rename and update: exhibitors with ExhNo but no entries **should** now appear
- Add `test_get_participants_includes_exhibitors_with_no_entries`
- Add `test_get_unenrolled_exhibitors_returns_only_null_exh_no`
- Add `test_get_unenrolled_exhibitors_filters_by_name`
- Add `test_enrol_exhibitors_assigns_sequential_exh_nos_alphabetically`
- Add `test_enrol_exhibitors_skips_already_enrolled`

---

## Out of Scope

- Changing the order of ExhNo assignment (alphabetical is the default; manual reordering is done via the Exhibitors page)
- Bulk un-enrolment (covered by Reset Data which clears all ExhNos)
- Changing how entries, benching, or late entries work
