# Check-in and Benching Workflow Design

## Context

The current Entries page is a pre-show entry management screen. It lets an operator add raw `show_entry` rows, run `Calculate`, and view the resulting `calculated_entry` rows. Today `Calculate` allocates an AutoNum to every entered bird, whether or not that bird physically arrives at the show.

The desired show-day workflow is different: when an exhibitor arrives, the operator should check in or bench only the birds that are physically present. Those benched birds should receive exhibit numbers. Judging sheets, cage tickets, result capture, and result reports should then operate from the benched set.

This design intentionally changes `calculated_entry` from "all entries after Calculate" to "entries that have been benched and allocated an exhibit number".

## Goals

1. Replace the operator-facing use of the Entries page with a Check-in page.
2. Let the operator search by exhibitor name, email, exhibitor number, or exhibit/exhibitor number text.
3. Show all pre-entered birds/classes for the selected exhibitor.
4. Let the operator select which birds arrived and allocate AutoNum values only to those selected birds.
5. Keep raw entry management available for corrections and late changes, but make it secondary to show-day check-in.
6. Ensure Judges Catalogue, Tickets, Results, and result reports naturally use only benched birds.

## Non-Goals

- Do not mutate the original Access `.mdb` file.
- Do not remove the raw `show_entry` table or pre-show entry management.
- Do not build a full kiosk/self-service exhibitor check-in flow.
- Do not require barcode scanning for check-in in the first implementation.
- Do not redesign late entries in this pass, beyond preserving current behavior.
- Do not delete the existing calculate service until replacement behavior is verified.

## Proposed Workflow

1. Before the show, staff enter/import exhibitors and their class entries as raw `show_entry` rows.
2. On show day, the operator opens `Check-in`.
3. The operator searches by name, email, exhibitor number, or exhibit/exhibitor number text.
4. The operator selects the matching exhibitor.
5. The page shows that exhibitor's entered birds/classes.
6. The operator ticks the birds that physically arrived.
7. The operator clicks `Bench Selected`.
8. The app creates `calculated_entry` rows for newly benched birds and assigns the next available AutoNum values.
9. Cage tickets and Judges Catalogue are printed from the benched set.
10. Results are captured from Judges Catalogue sheets and reports are printed from the same benched set.

## Navigation and Naming

Rename the user-facing sidebar item from `Entries` to `Check-in`.

The existing route/view can initially remain `entries` / `EntriesView` internally to keep the change smaller. The UI labels, help text, README, dashboard workflow labels, and keyboard shortcut descriptions should use `Check-in`.

Recommended visible page title: `Check-in / Benching`.

The page should lead with search and benching controls. Entry management actions should remain available as secondary controls, for example:

- `+ Add Entry`
- `Bulk Edit`
- `Show All Entries`
- `Export`

## Data Model

Use the existing tables with one small compatibility migration:

- `show_entry`: pre-show entered birds/classes.
- `calculated_entry`: benched birds with allocated AutoNum.
- `result`: judging result by AutoNum.
- `not_benched`: remains available for result/judging correction workflows.

Add nullable `calculated_entry.source_entry_auto_num`, pointing back to `show_entry.auto_num`.

This link is needed because an exhibitor may intentionally have multiple birds in the same class. Without the source entry link, the app cannot safely tell which specific raw entry has already been benched. Existing databases can migrate safely because the new column is nullable. Older calculated rows without a source link should still display, but check-in should label them as legacy allocations and block unbenching from the Check-in page.

## AutoNum Allocation

When benching selected birds:

- Find the current maximum `calculated_entry.auto_num`.
- Assign the next numbers sequentially to newly benched selections.
- Do not renumber existing benched birds.
- Do not rebuild `calculated_entry` wholesale during check-in.
- Copy `source_entry_auto_num`, `exh_no`, exhibitor `name`, and `class_code` into each new `calculated_entry` row.

This preserves ticket numbers already issued earlier in the day.

The old `Run Calculate (0010)` action should no longer be the primary workflow. If it remains accessible during the transition, label it clearly as an administrative bulk allocation action and document that it benches all entries.

## Search Behavior

The search service for check-in should return exhibitor matches using:

- Exhibitor name, partial and case-insensitive.
- Email, partial and case-insensitive.
- Exhibitor number, exact numeric match.
- Class/exhibit-related text:
  - raw `show_entry.class_code`
  - existing benched `calculated_entry.auto_num`
  - existing benched `calculated_entry.class_code`

Search results should show enough context to pick the right person:

- Exhibitor number
- Name
- Email or town/club if available
- Total entries
- Benched count

## Check-in Page Design

The page should have three main regions:

1. Search bar and results list.
2. Selected exhibitor summary.
3. Entry checklist/table.

The entry checklist should show:

- Checkbox
- Class code
- Class description/colour where available
- Current status:
  - `Not benched`
  - `Benched #123`
  - `Has result` when result data prevents unbenching

Actions:

- `Bench Selected`: benches checked, not-yet-benched rows.
- `Unbench Selected`: removes benched rows only if no result, special winner, or dependent record exists.
- `Select All Not Benched`
- `Clear Selection`

If an entry is already benched, its checkbox should be checked by default or visibly disabled depending on the action mode. The first implementation can keep this simple: checked rows mean "should be benched after save".

## Unbenching Rules

Unbenching should be conservative:

- Allowed when the `calculated_entry` row has no result and no NB flag.
- Blocked if a result exists.
- Blocked if a Not Benched flag exists.
- Blocked if a special winner references the AutoNum.

When blocked, the UI should explain which dependency prevents removal. This avoids orphaning results or reports.

## Downstream Effects

Because Tickets, Judges Catalogue, Judging Capture, Results, and most reports already use `calculated_entry`, they should naturally operate on benched birds only.

README and help text must clarify:

- Entries are pre-show intentions.
- Check-in/benching allocates actual exhibit numbers.
- Print cage tickets and Judges Catalogue after benching.
- Result capture happens after judges complete the Judges Catalogue.

Dashboard and welcome workflow text should change from `Run Calculate` to `Check in / bench birds`.

## Error Handling

- No search matches: show `No exhibitors found`.
- Selected exhibitor has no entries: show `No entries found for this exhibitor`.
- Benching already-benched rows: skip them and report that they were already benched.
- Attempting to unbench rows with dependencies: block those rows and list the reason.
- Missing class metadata: still show the class code and group description as blank or `Unknown`.
- AutoNum allocation failure: run benching in one transaction, roll back newly attempted rows, and do not claim success.

## Testing

Add focused tests before implementation:

- Search finds exhibitors by name, email, exhibitor number, raw class code, and existing AutoNum.
- Selected exhibitor entry list includes raw entries and current benched status.
- Benching selected entries creates `calculated_entry` rows with next available AutoNum values.
- Benched rows store `source_entry_auto_num` so duplicate same-class entries are tracked separately.
- Benching skips already-benched entries without duplicating them.
- Unbenching removes safe `calculated_entry` rows.
- Unbenching blocks rows with result, NB, or special winner dependencies.
- Existing ticket/report/judging tests continue to pass using `calculated_entry`.
- UI import smoke tests cover the renamed Check-in page.

## Documentation

Update `README.md` and in-app Help:

- Rename the workflow step from Entries/Calculate to Check-in/Benching where show-day operations are described.
- Explain that raw entries are still managed through Check-in's secondary entry management controls.
- Explain that AutoNum/exhibit numbers are allocated at check-in.
- Explain that cage tickets and Judges Catalogue should be printed after benching.

## Design Decisions

1. `calculated_entry` represents benched birds for the modern workflow.
2. AutoNum values are allocated incrementally at check-in and are not renumbered once issued.
3. Raw entry management remains available but secondary.
4. The first implementation adds one nullable source-link column to make duplicate same-class entries safe.
5. Unbenching is intentionally conservative to protect results and reports.
