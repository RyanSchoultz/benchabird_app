# Show Participants — Design Spec
**Date:** 2026-06-03  
**Status:** Approved

---

## Problem

The app currently has three separate nav pages — **Exhibitors**, **Entries**, and **Check-in** — that all revolve around the same entity: a person entered in the current show. Navigating between them is disjointed, and the entry creation flow has a critical gap: the "Exhibitor #" field is a free-text number with no lookup against the master registry, meaning orphaned entries (ExhNo with no matching Exhibitor) can be created silently. The Access database had an explicit validation query (`0151Q Show_Entries_Without_Exhibitors_Q`) to catch this — the app does not.

**Late Entries** is also a separate page, but is functionally identical to a regular entry with a "late" flag.

---

## Context: ExhNo

`ExhNo` is a **per-show number assigned by the organiser** to each participant. It is stored on the `Exhibitor` record (master registry). Out of 199 registered exhibitors, only those actively entering a show have an ExhNo set (24 in the 2023 dataset). `ShowEntry` and `LateEntry` rows reference this number to link an entry to a person.

`Exhibitors` is a master registry of all registered club members — past, present, and future. Not all exhibitors are show participants. This distinction is preserved: the Exhibitors page remains unchanged as a contact/registry management tool.

---

## Decision

- **Keep** Exhibitors as a standalone master registry page (unchanged).
- **Replace** Entries + Check-in + Late Entries with a single **Show Participants** page.
- **Modernise** the Calculate macro into smart auto-triggering rather than a manual button.

---

## Navigation Changes

**Removed from nav:** Entries, Check-in, Late Entries  
**Added to nav:** Show Participants (between Exhibitors and Results)

```
Dashboard
Search
Show Setup
Exhibitors            ← unchanged
Show Participants     ← NEW
Results
Special Winners
...
```

**Keyboard shortcuts:**  
- `Ctrl+B` (was Check-in) → Show Participants  
- `Ctrl+E` (was Entries) → Show Participants  

**Files:**
- `views/main_window.py` — update `NAV`, `_make_view`, shortcut bindings
- `views/show_participants_view.py` — new file
- `views/entries_view.py` — removed from nav (file deleted)
- `views/checkin_view.py` — removed from nav (file deleted)
- `views/late_entries_view.py` — removed from nav (file deleted)

---

## Page Layout

Two-panel layout, same structure as the current Check-in view.

```
┌──────────────────────────┬──────────────────────────────────────────┐
│  LEFT (300px fixed)      │  RIGHT (fills remainder)                 │
│                          │                                          │
│  [Search…           ] [✕]│  #12  Van Niekerk, Gerhard               │
│  [All] [Unbenched] [Late]│  14 entries · 9 benched · 0 late         │
│                          │                                          │
│  #3  Abrahams, Dante     │  [Select Unbenched] [Clear] [Bench ▶]    │
│  12 entries · 12 benched │  [+ Add Entry]  [+ Add Late Entry]       │
│                          │  ──────────────────────────────────────  │
│  #4  Abrahams, D.        │  ☐  RF168  Red Factor Cock   Benched #4  │
│  6 entries · 4 benched   │  ☐  SC42   Stafford Clear    LATE  #7   │
│                          │  ☑  NC221  Norwich Clear      Not benched│
│  ...                     │  ☐  NC223  Norwich Buff       Benched #9 │
│                          │  ...                                     │
└──────────────────────────┴──────────────────────────────────────────┘
```

### Left Panel

- Shows only exhibitors with at least one `ShowEntry` or `LateEntry`.
- Sorted by ExhNo ascending.
- Search box searches name, ExhNo, email, and class code across current participants **and** the master registry (to support adding new participants — see below).
- Filter chips:
  - **All** — all participants
  - **Unbenched** — entry count > benched count
  - **Late** — has at least one `LateEntry`

### Right Panel

- **Header:** ExhNo badge + name + summary counts (entries / benched / late)
- **Action bar:** Select Unbenched · Clear · Bench Selected · Unbench Selected · + Add Entry · + Add Late Entry
- **Entries list columns:** Checkbox · Class code · Description (from ClassGlossary) · Status badge

**Status badges:**
| Badge | Meaning |
|---|---|
| `Benched #N` | CalculatedEntry exists, auto_num = N |
| `Not benched` | No CalculatedEntry for this ShowEntry |
| `LATE` | Comes from LateEntry table |
| `Has result` | Result recorded — unbench blocked |
| `NB` | Marked Not Benched — unbench blocked |
| `Special winner` | Linked special winner — unbench blocked |

`LateEntry` rows appear inline with all other entries. They are distinguished only by the `LATE` badge. No separate section.

---

## Auto-Calculate (Modernised)

The manual "Run Calculate" button is removed. Calculate runs automatically based on show state.

### State Machine

| Show state | Trigger | Behaviour |
|---|---|---|
| No CalculatedEntries exist | Entry added or removed | Auto-calculate silently |
| CalculatedEntries exist, none from individual bench (`source_entry_auto_num` all NULL) | Entry added or removed | Auto-calculate silently |
| Benching has started (any `source_entry_auto_num` IS NOT NULL) | Entry added or removed | Show `⚠ Entries changed — Recalculate?` inline notice on affected exhibitor's panel |
| Results recorded in `Result` table | Any | Block recalculate entirely — show is underway |

### Recalculate Warning

Shown inline at the top of the right panel (not a global alert). Includes a **Recalculate** button with a one-line confirmation:

> "This will reassign bench numbers for all unbenched entries. Continue?"

### Detection Logic

```python
def _benching_started() -> bool:
    return CalculatedEntry.select().where(
        CalculatedEntry.source_entry_auto_num.is_null(False)
    ).exists()

def _results_recorded() -> bool:
    from models.results import Result
    return Result.select().where(Result.result.is_null(False)).exists()
```

---

## Adding an Exhibitor to the Show

**Problem with current flow:** Entry dialog asks for raw ExhNo number — no name lookup, no validation that the number exists in the registry.

**New flow:**

The left panel search box searches both current participants and the full Exhibitors master registry. If a registry match is found who is not yet in the current show, it appears with a `+ Add to show` affordance.

Selecting it:
1. If the exhibitor already has an ExhNo → drops into their right panel ready to add entries.
2. If the exhibitor has no ExhNo → shows an inline prompt: `Assign an exhibitor number for this show:` with a field pre-filled with `max(current ExhNos) + 1`. The number is validated as unique before saving to `Exhibitor.exh_no`.

This eliminates the need to navigate to the Exhibitors page to assign an ExhNo.

---

## ExhNo Validation

On Show Participants load, a query checks for `ShowEntry` rows whose `exh_no` has no matching `Exhibitor` record (mirrors Access `0151Q`):

```sql
SELECT se.auto_num, se.exh_no, se.class_code
FROM show_entry se
LEFT JOIN exhibitor e ON se.exh_no = e.exh_no
WHERE e.id IS NULL
```

If any orphaned entries are found, a warning banner appears at the top of the left panel:

> `⚠ 3 entries have no matching exhibitor — click to review`

Clicking it filters the left panel to an "Unmatched" group showing the orphaned entries so the organiser can correct them.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Duplicate entry (same ExhNo + class) | Inline warning on class code selection before save |
| Class limit exceeded | Inline error at save time |
| Unbench blocked (result / NB / special winner) | Checkbox disabled, status badge explains reason |
| Exhibitor no ExhNo when adding to show | Inline assign-number prompt, auto-suggests next available |
| Orphaned ExhNo entries | Warning banner on left panel, filter to "Unmatched" group |
| Recalculate mid-show | Confirmation required, explicit warning about number reassignment |

---

## Data Sources

| Data | Source |
|---|---|
| Participants list | `ShowEntry` + `LateEntry` grouped by `exh_no`, joined to `Exhibitor` |
| Entry descriptions | `ClassGlossary.description` keyed by `class_code` |
| Bench status | `CalculatedEntry` — exists = benched, `auto_num` = bench number |
| Blocked reason | `Result`, `NotBenched`, `SpecialWinner` tables |
| Show state | `CalculatedEntry.source_entry_auto_num` + `Result.result` |

---

## Implementation Notes

**Late entry benching:** The current `bench_entries` service in `checkin_service.py` only reads from `ShowEntry`. Late entries must also be benchable in the new flow (a late entry arrives, is entered, and is benched on the same day). The implementation must extend `bench_entries` (or add a parallel path) to accept `LateEntry` rows, creating a `CalculatedEntry` with `source_entry_auto_num` referencing the late entry's `auto_num`. The `LateEntry.auto_num` sequence is independent of `ShowEntry.auto_num` — the service must not assume they share a namespace.

---

## Out of Scope

- The Exhibitors master registry page is unchanged.
- Results, Special Winners, Tickets, Reports pages are unchanged.
- The `LateEntry` table structure is unchanged — late entries continue to be stored separately. The change is UI-only.
- No changes to how bench numbers are formatted or printed on tickets.
