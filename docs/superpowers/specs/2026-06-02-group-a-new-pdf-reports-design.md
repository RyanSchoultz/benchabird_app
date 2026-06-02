# Group A — New PDF Reports Design Spec

**Date:** 2026-06-02  
**Status:** Approved  
**Part of:** Feature roadmap — Group A (independent, no schema changes)

---

## Overview

Two new PDF reports added to the existing Reports view:

1. **Exhibitor Entry Confirmation Sheet** — printed at check-in, one section per exhibitor listing their submitted entries with ticket numbers. Supports an optional late-entries toggle.
2. **Results by Exhibitor** — printed after judging, one section per exhibitor showing all results, special prizes won, and prize money total.

Both reports follow the existing pattern exactly: a `generate_X(sd=None) -> bytes` function in its own module under `services/reports/`, using `new_canvas`, `draw_page_header`, and `draw_footer` from `services/reports/base.py`. Both get a button added to the 3-column grid in `reports_view.py`.

---

## Existing Pattern Reference

Every report in the codebase follows this structure:

```python
# services/reports/X.py
def generate_X(sd=None) -> bytes:
    buf, c = new_canvas()
    page_num = 1
    y = draw_page_header(c, "Report Title", sd)
    y = _draw_col_headers(c, y)
    for row in rows:
        if y < MARGIN + ROW_H:
            draw_footer(c, page_num); c.showPage(); page_num += 1
            y = draw_page_header(c, "Report Title", sd)
            y = _draw_col_headers(c, y)
        # draw row...
        y -= ROW_H
    draw_footer(c, page_num)
    c.save()
    return buf.getvalue()
```

The `reports_view.py` wires each button to `self._save_and_open(gen_fn, filename)` which runs generation in a background thread and opens `PDFPreviewWindow`.

---

## Report 1: Exhibitor Entry Confirmation Sheet

### Purpose

Printed before or at the show and handed to each exhibitor at check-in. Confirms what entries were submitted under their name, with ticket numbers (if Calculate has been run).

### Signature

```python
# services/reports/entry_confirmation.py
def generate_entry_confirmation(sd=None, include_late: bool = True) -> bytes:
```

### Data Sources

| Table | Usage |
|---|---|
| `exhibitor` | Exhibitor number, name, club, cell/phone |
| `calculated_entry` | Regular entries with ticket numbers (post-Calculate) |
| `show_entry` | Fallback for regular entries if Calculate not yet run |
| `late_entry` | Late entries (included only when `include_late=True`) |
| `class_def` | Class description (`main_class` + `colour`) for each class code |

**Query strategy:** Attempt to load from `calculated_entry`. If the table is empty, fall back to `show_entry` with ticket number shown as `—`. Late entries always come from `late_entry` regardless of Calculate status.

### Layout

For each exhibitor (sorted by `exh_no`):

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ← thick rule between exhibitors
Exhibitor #12  —  J. Smith                [Club Name]
Cell: 082 555 1234
──────────────────────────────────────────  ← thin rule
Ticket #   Class     Description
001        BORD-A    Border Canary Adult Male
002        BORD-B    Border Canary Adult Female
[LATE]     CANARY    Canary Mixed
──────────────────────────────────────────
3 entries  +  1 late entry
```

- Exhibitor sections separated by a 1pt horizontal rule with 4mm vertical gap
- `[LATE]` marker printed in a muted grey/orange where the ticket number would be
- If an exhibitor has no entries and no late entries, they are skipped entirely
- Page break inserts a new `draw_page_header` call; column headers re-drawn after each break

### Columns

| Column | Width | Source |
|---|---|---|
| Ticket # | 20mm | `calculated_entry.auto_num` or `—` |
| Class Code | 22mm | `class_code` |
| Description | remaining | `class_def.main_class + " " + class_def.colour` (truncated to fit) |
| Late marker | 12mm (rightmost) | Static `"LATE"` in grey if from `late_entry` |

### UI — Late Entries Toggle

A `CTkSwitch` widget labelled `"Include late entries"` is added above the button grid in `reports_view.py`. It is `ON` by default. Its state is stored as `self._include_late` (instance attribute, session-only — no database persistence). The confirmation sheet generator is called as:

```python
gen_fn = lambda sd: generate_entry_confirmation(sd, include_late=self._include_late.get())
self._save_and_open(gen_fn, "benchabird_entry_confirmation.pdf")
```

The toggle affects only the Entry Confirmation Sheet; all other report buttons ignore it.

---

## Report 2: Results by Exhibitor

### Purpose

Printed after judging is complete. Groups every result under its exhibitor — useful for prize-giving announcements and as a reference for communicating results to participants.

Exhibitors with zero results (no result rows and not in `not_benched`) are excluded from the report. If `calculated_entry` is entirely empty (Calculate has not been run), the report renders a single page with the standard header and the message "No calculated entries found. Run Calculate before generating this report."

### Signature

```python
# services/reports/results_by_exhibitor.py
def generate_results_by_exhibitor(sd=None) -> bytes:
```

### Data Sources

| Table | Usage |
|---|---|
| `exhibitor` | Exhibitor name, number |
| `calculated_entry` | Ticket numbers and class codes |
| `result` | Result values per exhibit number |
| `not_benched` | NB flag per exhibit number |
| `special_winner` | Which specials this exhibitor won |
| `special_list` | Prize description and cash amount |

### Query Strategy

Single SQL query grouping all results and NB entries per exhibitor:

```sql
SELECT ce.exh_no, e.name, ce.auto_num AS ticket_no, ce.class_code,
       COALESCE(r.result, '') AS result,
       CASE WHEN nb.exhibit_no IS NOT NULL THEN 1 ELSE 0 END AS is_nb
FROM calculated_entry ce
LEFT JOIN exhibitor e ON ce.exh_no = e.exh_no
LEFT JOIN result r ON ce.auto_num = r.exhibit_no
LEFT JOIN not_benched nb ON ce.auto_num = nb.exhibit_no
WHERE r.exhibit_no IS NOT NULL OR nb.exhibit_no IS NOT NULL
ORDER BY ce.exh_no, ce.auto_num
```

Special prizes fetched per exhibitor in a second query:

```sql
SELECT sw.special_nr, sl.description, sl.cash
FROM special_winner sw
JOIN special_list sl ON sw.special_nr = sl.special_nr
WHERE sw.exhibit_no IN (
    SELECT auto_num FROM calculated_entry WHERE exh_no = ?
)
```

### Layout

For each exhibitor section:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ← thick rule
Exhibitor #12  —  J. Smith
──────────────────────────────────────────
Ticket #   Class     Result
001        BORD-A    1st
002        BORD-B    BOB
003        CANARY    [NB — printed in red]
──────────────────────────────────────────
Special prizes:
  Champion Open Budgie
  Best in Show Reserve
──────────────────────────────────────────
Prize money: R 250
```

- Sections where the exhibitor has no special prizes: omit the "Special prizes:" block
- Sections where prize money is 0 or null: omit the "Prize money:" line
- NB rows: `result` column prints `Not Benched` in red (`setFillColorRGB(0.8, 0.1, 0.1)`)
- Page break logic identical to all other reports

### Columns

| Column | Width | Source |
|---|---|---|
| Ticket # | 20mm | `calculated_entry.auto_num` |
| Class Code | 25mm | `class_code` |
| Result | remaining | `result.result` or `"Not Benched"` in red |

---

## Files Changed

| File | Action |
|---|---|
| `services/reports/entry_confirmation.py` | Create |
| `services/reports/results_by_exhibitor.py` | Create |
| `views/reports_view.py` | Modify — add toggle + 2 new buttons |
| `tests/test_entry_confirmation_pdf.py` | Create |
| `tests/test_results_by_exhibitor_pdf.py` | Create |

No model changes. No migration. No new tables.

---

## Testing Strategy

Both test modules follow the pattern established by `tests/test_exhibitor_list_pdf.py` and `tests/test_results_sheet_pdf.py`:

- Use in-memory SQLite via `conftest.py` fixtures
- Seed minimal data: at least 2 exhibitors, entries, results
- Assert `generate_X()` returns non-empty bytes
- Assert `len(pdf_bytes) > 1000` (non-trivial PDF)
- Assert no exception is raised with empty tables (graceful empty-state handling)

For `entry_confirmation`:
- Test with `include_late=True` and `include_late=False` — byte lengths differ when late entries exist
- Test fallback to `show_entry` when `calculated_entry` is empty

For `results_by_exhibitor`:
- Test that exhibitors with no results are excluded
- Test NB rows are included
- Test special prizes block appears when specials are assigned
- Test prize money line appears only when cash > 0

---

## Out of Scope

- Filtering by exhibitor (print one exhibitor's sheet only) — future enhancement
- Email delivery — explicitly deferred
- Styling/colour branding beyond the existing base.py watermark
