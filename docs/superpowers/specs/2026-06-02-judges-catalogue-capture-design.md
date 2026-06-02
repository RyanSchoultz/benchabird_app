# Judges Catalogue PDF and Category Capture Design

## Context

The Access workflow uses report `0140 Judges_Catalogue_ R`, surfaced in the legacy switchboard as `4.1 Judges Catalogues`. The exported report definition shows:

- Record source: `0053Q Show_Entries_Calculated_SQ`
- Page title: `JUDGES CATALOGUE`
- Page header fields from show/club details: English and Afrikaans club/show/date fields
- Grouping order: `Seq`, `TYPE`, `MCSeq`, `MAINCLASS`, `ClASSSEQ`, `Class`, `AutoNum`
- Class header fields: `Class`, `Colour`, and `TYPEB`
- Detail row fields: `AutoNum` and `Not benched`
- Detail row marking area: small boxed labels `1`, `2`, `3`, `4` for handwritten judge marks
- Type group footer: page break after each `TYPE`

This report is an offline judging artifact, not an interactive result-entry workflow. Judges complete the printed sheet by hand. The show manager later captures the marked results and then prints result reports.

## Goals

1. Rebuild the Judges Catalogue as a printable PDF in the modern app.
2. Add a category-based result capture screen that mirrors the printed catalogue ordering.
3. Keep the existing Results screen for corrections, scanning, exports, and broad review.
4. De-emphasize Judge Mode once the category capture workflow exists.
5. Allow the show manager to reallocate a bird to another valid class while capturing a judge sheet.

## Non-Goals

- Do not mutate or rely on the original `.mdb` file.
- Do not claim exact Access layout parity until fixture/output comparison is captured.
- Do not build OCR or automatic reading of handwritten sheets.
- Do not replace the existing Results table/export/report workflows.
- Do not require live judging on phones or desktops.

## Proposed Workflow

1. User runs Calculate so `calculated_entry` has the show-day exhibit numbers.
2. User opens Reports or a new Judging area and clicks `Judges Catalogue`.
3. App generates a PDF grouped like the Access report.
4. Judges write placings or NB marks on the printed sheets.
5. Show manager opens `Judging Capture`.
6. Show manager selects a category/species/type.
7. App shows entries for that selected category in the same order as the PDF.
8. If the judge sheet identifies a class correction, the show manager changes that exhibit's class.
9. Show manager selects radio-button results per exhibit.
10. Show manager clicks `Save Category Results`.
11. App bulk-saves class changes, results, and NB flags.
12. User prints Results, Results by Exhibitor, Special Winners, Prize Money, or other post-show reports.

## PDF Design

Add `services/reports/judges_catalogue.py` with `generate_judges_catalogue(sd=None) -> bytes`.

The PDF should use the current ReportLab pattern from `services/reports/*`:

- Use `new_canvas`, page headers, footers, margins, and consistent app styling where sensible.
- Title: `Judges Catalogue`.
- Header: show and club details from `ShowDetails`.
- Group by category/species/type first, then main class, then class.
- Start a new page for each category/species/type, matching the Access type-footer page break.
- For each class, print class code and colour/description.
- For each exhibit, print the exhibit number and marking boxes.

Suggested detail columns:

- Exhibit #
- 1
- 2
- 3
- 4
- 5
- BOB
- R/U BOB
- Champion
- Reserve
- NB

The Access report only visibly exports boxes `1` through `4` plus `Not benched`, but the modern app already supports `1st`, `2nd`, `3rd`, `4th`, `5th`, `BOB`, `R/U BOB`, `Champion`, and `Reserve`. The modern PDF should include the full supported result set unless the user later decides the judging sheet should stay closer to the Access four-box layout.

## Data Source

Use the modern equivalents of Access `0053Q Show_Entries_Calculated_SQ`:

- `calculated_entry.auto_num`
- `calculated_entry.exh_no`
- `calculated_entry.name`
- `calculated_entry.class_code`
- `class_def.class_code` (Access `CLASS`)
- `class_def.bird_type` (Access `TYPE`)
- `class_def.type_b` (Access `TYPEB`)
- `class_def.main_class` (Access `MAINCLASS`)
- `class_def.colour` (Access `COLOUR`)
- `class_def.class_seq` (Access `ClASSSEQ`)
- `species.seq` (Access `Seq`)
- `main_class.mc_seq` (Access `MCSeq`)

The modern schema has direct fields for the report's major grouping and display controls. If rows are missing optional class metadata, group them under `(Unclassified)` or `(Unknown)` and include those rows rather than hiding them.

## Capture Screen Design

Add a dedicated dialog named `Judging Capture`.

Recommended placement:

- Add a button in Results: `Judging Capture`
- Add a report button in Reports: `Judges Catalogue`
- Replace the visible Results toolbar `Judge Mode` button with `Judging Capture`
- Leave the old Judge Mode module in place for now, but do not expose it as the primary judging workflow

The capture screen should:

- Load available categories/species/types from calculated entries joined to class metadata.
- Let the user select one category/species/type.
- Show entries in the same order as the PDF.
- Display row context: exhibit number, class, colour/description, and current saved result/NB state.
- Let the operator change the row's class to any valid `class_def.class_code`.
- Provide mutually exclusive radio buttons per row:
  `1st`, `2nd`, `3rd`, `4th`, `5th`, `BOB`, `R/U BOB`, `Champion`, `Reserve`, `NB`, `Clear`
- Save all selected rows in the current category with one `Save Category Results` button.
- Leave rows unchanged if the operator makes no selection and the row already has an existing result.
- Show a confirmation/status message such as `Saved 18 updates for Red Factor`.

### Class Reallocation

Judging Capture should support class corrections discovered during judging.

For each row, show the current class code and provide a compact `Change Class` control. The control can be a combobox or small dialog, but it must search/select from valid `class_def.class_code` values and should display enough context to avoid mistakes:

- class code
- colour/description
- category/species/type
- main class

The operator may move a bird to any valid class, not only classes inside the current category. If the selected class belongs to a different category/species/type than the currently captured page, show a warning before save:

`This moves exhibit #123 from Gloster to Red Factor. It will disappear from this page after saving.`

On save, the app updates `calculated_entry.class_code` for that AutoNum before reloading the category. If `calculated_entry.source_entry_auto_num` exists, the implementation should also update the linked `show_entry.class_code` for the same source entry so the pre-show entry record and benched record stay aligned. If no source link exists, update only `calculated_entry` and show the correction in reports that are based on benched birds.

Class reallocation should preserve the exhibit AutoNum. Do not reallocate ticket numbers or renumber other birds.

## Saving Semantics

For each row on save:

- A class change updates the exhibit's class while preserving its AutoNum.
- `NB` marks the exhibit Not Benched and clears any placing result.
- A placing result records the result and removes any existing NB flag.
- `Clear` clears the result and removes any NB flag.
- No selection leaves the current result and NB state unchanged.

If both class and result change on the same row, save both changes in one transaction. If either part fails, roll back the row's class/result changes and report the error.

This matches existing `results_service.record_result` and `not_benched_service` behavior.

## Error Handling

- If Calculate has not been run and no calculated entries exist, show a message: `Run Calculate before printing or capturing judging sheets.`
- If class/category metadata is incomplete, still show entries grouped under `(Unclassified)` or `(Unknown)` rather than hiding them.
- If the selected replacement class does not exist in `class_def`, block save and show `Select a valid class`.
- If a class change moves a row out of the active category, warn before saving and reload the category after save.
- If a category has no entries, show an empty state and disable `Save Category Results`.
- If saving fails mid-category, report the error and avoid claiming the whole category was saved.

## Testing

Add focused tests before implementation:

- Report data query returns entries in Access-inspired grouping/order.
- PDF generator returns non-empty PDF bytes and includes `Judges Catalogue`.
- PDF generator handles no calculated entries.
- Category list includes only categories with calculated entries.
- Capture save records placing results and clears NB.
- Capture save records NB and clears placing result.
- Capture save clears both result and NB.
- Capture save updates an exhibit's class and preserves AutoNum.
- Capture save can update class and result in the same transaction.
- Class reallocation rejects invalid class codes.
- Class reallocation to another category removes the row from the current category after reload.
- Existing Results screen still imports and functions after Judge Mode de-emphasis.

## Documentation

Update `README.md`:

- Explain the paper judging workflow.
- Document `Judges Catalogue` under Reports.
- Document `Judging Capture` under Results.
- Document that Judging Capture can correct an exhibit's class while preserving the exhibit number.
- Clarify that judges complete printed sheets and the show manager captures results afterward.

## Design Decisions

1. The PDF includes the full modern result set: `1st`, `2nd`, `3rd`, `4th`, `5th`, `BOB`, `R/U BOB`, `Champion`, `Reserve`, and `NB`.
2. `Judging Capture` is a modal dialog launched from Results. This keeps the main navigation smaller and matches the existing app pattern for focused workflows.
3. Judge Mode is de-emphasized by replacing its toolbar button with `Judging Capture`. The old module can be removed in a later cleanup after the paper workflow has been used successfully.
4. Class reallocation is allowed to any valid class. Moving out of the current category is permitted with a warning because the row will move to the replacement category after save.
5. Class reallocation preserves AutoNum and does not renumber other exhibits.
