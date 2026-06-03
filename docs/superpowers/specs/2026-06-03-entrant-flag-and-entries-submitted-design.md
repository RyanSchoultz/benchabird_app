# Entrant Flag & Entries Submitted Report — Design Spec
**Date:** 2026-06-03
**Status:** Approved

---

## Problem

1. The Enrol dialog currently shows all 175+ unenrolled exhibitors — too many to scan through. There is no way to pre-flag the ~24 who are actually entering this show before assigning ExhNos.

2. There is no pre-show entries report. The existing "Entries Received" report uses `CalculatedEntry` (benched birds after show day). A pre-show report showing submitted entries from `ShowEntry`, grouped by class and by exhibitor, is missing.

---

## Solution Overview

- Add `is_entrant` boolean field to `Exhibitor` — the flag meaning "this person has submitted entries for this show"
- Exhibitors page gets a "Toggle Entrant" button (same pattern as Toggle Labels) and an Entrant column
- Enrol dialog filters to only show flagged, unenrolled exhibitors
- New "Entries Submitted" report: one PDF with three sections — summary, by class, by exhibitor

---

## Part 1: `is_entrant` Flag

### Data model

**File:** `models/exhibitor.py`

Add field:
```python
is_entrant = BooleanField(default=False)
```

**File:** `main.py` — add to `_migrate_db()`:
```python
"ALTER TABLE exhibitor ADD COLUMN is_entrant BOOLEAN DEFAULT 0",
```

### Reset show data

**File:** `services/reset_service.py`

Add to the atomic reset block:
```python
'entrants_cleared': Exhibitor.update(is_entrant=False).where(
    Exhibitor.is_entrant == True
).execute(),
```

---

## Part 2: Exhibitors Page

**File:** `views/exhibitors_view.py`

### Changes

**Table headers:** Add "Entrant" column after "Labels":
```python
headers=["Exh #", "Name", "Town", "Phone", "Email", "Labels", "Entrant"]
```

**Table data:** Add `"✓" if e.is_entrant else ""` as the last cell.

**Toolbar:** Add "Toggle Entrant" button (same position/style as Toggle Labels):
```python
ctk.CTkButton(toolbar, text="Toggle Entrant", width=120,
              fg_color=("gray80", "gray30"), text_color=("gray10", "gray90"),
              command=self._toggle_entrant).pack(side="right", padx=4)
```

**Method `_toggle_entrant()`:**
```python
def _toggle_entrant(self):
    if not self._selected_pk:
        return
    exhibitor = _repo.get_by_id(self._selected_pk)
    if exhibitor:
        _repo.update(exhibitor, is_entrant=not exhibitor.is_entrant)
    self._load()
```

**Export:** Include `is_entrant` as "Entrant" column (Yes/No).

---

## Part 3: Enrol Dialog Filter

**File:** `services/show_participants_service.py`

`get_unenrolled_exhibitors()` gains a `flagged_only: bool = False` parameter:

```python
def get_unenrolled_exhibitors(query: str = "", flagged_only: bool = False) -> list[Exhibitor]:
    base = Exhibitor.select().where(Exhibitor.exh_no.is_null(True))
    if flagged_only:
        base = base.where(Exhibitor.is_entrant == True)
    if (query or "").strip():
        base = base.where(Exhibitor.name.contains(query.strip()))
    return list(base.order_by(Exhibitor.name))
```

**File:** `views/_enrol_dialog.py`

`_load()` calls `get_unenrolled_exhibitors(flagged_only=True)`:
```python
def _load(self):
    self._all_exhibitors = get_unenrolled_exhibitors(flagged_only=True)
    self._vars = {e.id: ctk.BooleanVar(value=False) for e in self._all_exhibitors}
    self._apply_filter()
```

The dialog also updates its title to reflect the filter:
```
"Enrol Exhibitors for This Show (flagged entrants only)"
```

---

## Part 4: Entries Submitted Report

### Source data

`ShowEntry` (pre-benching), joined to `Exhibitor` and `ClassDef`.

**Not** `CalculatedEntry` — this report shows submitted entries before show day.

### Three sections in one PDF

**Section A — Summary table**

Columns: Exh # · Name · Club · Entry Count  
Sorted by ExhNo ascending.  
Footer row: total exhibitors and total entries.

```
ENTRIES SUBMITTED — SUMMARY
National Open Show, 19 & 20 June 2026

Exh #  Name                Club    Entries
  1    Geldenhuys, J.P.    KVK      20
  2    Meyers, H.           KVK       7
  ...
  24   Smit, Christiaan.   KVK      54
                                   ────
Total: 24 exhibitors · 559 entries
```

**Section B — Entries by Class**

Mirroring Access `0030Q Show_Entries_SQ`. Sorted by `ClassDef.class_seq`.  
Grouped by `ClassDef.bird_type` (section heading) then `ClassDef.main_class` (sub-heading) then class code.  
Each class row shows the class code, colour/description, and lists the exhibitor names and ExhNos below it.

```
ENTRIES BY CLASS

═══ NORWICH CANARY SECTION ════════════════════════════
OPEN CLASS - COCKS
  N1  Yellow: Clear
      Olivier, A  (#17)
      Smit, Jacques  (#8)
  N3  Yellow: H.V. or Foul Green
      Olivier, A  (#17)
      Smit, Jacques  (#8)
```

**Section C — Entries by Exhibitor**

Each entrant on their own block. Sorted by ExhNo.  
Shows class code + description per entry.

```
ENTRIES BY EXHIBITOR

#1  Geldenhuys, J.P.  — 20 entries
────────────────────────────────────
N1     Open Cock — Yellow: Clear
N3     Open Cock — Yellow: H.V. or Foul Green
RF1    Red Factor — Open Cock
...

#2  Meyers, H.  — 7 entries
────────────────────────────────────
SC42   Scotch Fancy — Cock
...
```

### File

**Create:** `services/reports/entries_submitted.py`

Single public function: `generate_entries_submitted(sd=None) -> bytes`

### Reports view

**File:** `views/reports_view.py`

Add to the `reports` list:
```python
("Entries Submitted", "benchabird_entries_submitted.pdf", self._gen_entries_submitted),
```

Add the generator method:
```python
def _gen_entries_submitted(self):
    self._generate(
        lambda sd: __import__('services.reports.entries_submitted',
                              fromlist=['generate_entries_submitted']
                              ).generate_entries_submitted(sd),
        "benchabird_entries_submitted.pdf",
    )
```

---

## File Map

| Action | File |
|---|---|
| Modify | `models/exhibitor.py` — add `is_entrant` field |
| Modify | `main.py` — migration |
| Modify | `services/reset_service.py` — clear is_entrant on reset |
| Modify | `services/show_participants_service.py` — flagged_only param |
| Modify | `views/_enrol_dialog.py` — use flagged_only=True |
| Modify | `views/exhibitors_view.py` — column + Toggle Entrant button |
| Create | `services/reports/entries_submitted.py` — 3-section PDF |
| Modify | `views/reports_view.py` — add Entries Submitted button |

---

## Tests

- `test_exhibitor_has_is_entrant_field` (in test_models.py)
- `test_reset_clears_is_entrant` (in test_reset_service.py)
- `test_get_unenrolled_exhibitors_flagged_only` (in test_show_participants_service.py)
- `test_entries_submitted_pdf_imports` (import smoke test)

---

## Out of Scope

- Bulk-flag exhibitors from a list (one-at-a-time toggle is sufficient for this season)
- The existing "Entries Received" report is unchanged (it uses `CalculatedEntry`, serves a different purpose)
- No changes to Show Participants, Check-in, or Tickets behaviour
