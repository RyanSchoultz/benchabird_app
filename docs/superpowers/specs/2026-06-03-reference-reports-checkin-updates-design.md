# Reference Data, Catalogue Reports, Check-in Allocation, and Updates Design

## Context

Recent show-day workflow changes moved Benchabird away from the legacy Access pattern of calculating every entry before the show. The modern flow is:

1. Raw intended entries live in `show_entry`.
2. Show-day check-in benches only birds that physically arrive.
3. Benched birds live in `calculated_entry` and receive exhibit numbers.
4. Tickets, judging sheets, catalogues, and results use benched birds.

The legacy Access database also has static reference data that rarely changes:

- `Classes_T` imports into `class_def`.
- `Species_T` imports into `species`.

The visible Class Glossary currently reads `class_def` directly and formats rows at runtime. The live imported data has thousands of rows, so the glossary should use a prebuilt lookup table.

Access catalogue menu `4. Catalogues` maps to:

- `4.1 Judges Catalogues` -> `0140 Judges_Catalogue_ R`
- `4.2 Special Lists` -> `0190 Special_Lists_R`
- `4.3 Catalogue` -> `0130 Catalogue_R`
- `4.4 Marked Catalogue` -> `0135 Marked_Catalogue_R`

The modern app already has first versions of Judges Catalogue and Show Catalogue. It does not yet expose the full 4.1-4.4 set using Access terminology, nor does it have an app self-update workflow.

## Goals

1. Add a dedicated `class_glossary` table seeded from `class_def` and `species`.
2. Use `species` only as Class Glossary filters/group headings for now, not as a separate screen.
3. Seed/reseed the glossary on app launch and after legacy import.
4. Keep the existing `class_def` and `species` tables as the source of truth.
5. Make Check-in allocation follow legacy calculate ordering for the selected exhibitor without running destructive global `0010_calculate`.
6. Surface downloadable catalogue reports for Access menu items 4.1-4.4.
7. Add a manual "Check for Updates" service that checks GitHub releases, downloads a newer Windows exe, restarts through a helper, and shows changelog on next launch.

## Non-Goals

- Do not mutate the original MDB file.
- Do not delete imported `class_def`, `species`, or `notes_brochure` data.
- Do not add class/species editing in this pass.
- Do not make Species a top-level navigation item in this pass.
- Do not auto-update silently. User confirmation is required before download/restart.
- Do not replace the currently running exe directly from inside itself. Windows cannot reliably overwrite a running executable.

## Reference Data Design

Create a `ClassGlossary` model/table with precomputed display fields:

- `class_code`
- `bird_type`
- `species_seq`
- `species_heading`
- `species_subheading`
- `main_class`
- `description`
- `extra`
- `class_seq`
- `search_text`

The seed service reads all `ClassDef` rows, left-joins/matches `Species` by `bird_type`, and writes a fast browse/search table. Description is still built as `colour + " " + afrbesk`, omitting blanks.

Ordering:

1. `species_seq`
2. `species_heading`
3. `main_class`
4. `class_seq`
5. `class_code`

The Class Glossary UI shows species headings/grouping and a filter dropdown for species headings. Search reads `class_glossary.search_text`.

## Check-in Allocation Design

Legacy `calculate_entries()` remains an admin/global rebuild that deletes and recreates all calculated rows. It should be documented as a legacy bulk action.

Check-in uses a new non-destructive allocator:

1. Accept selected `ShowEntry.auto_num` values for one exhibitor.
2. Sort selected entries by `ClassDef.class_seq`, then `ShowEntry.auto_num`.
3. Allocate the next available `CalculatedEntry.auto_num` values.
4. Preserve `source_entry_auto_num` so the app knows which raw entry was benched.
5. Skip already-benched source entries.

This gives each checked-in user the same class-sequence ordering spirit as `0010_calculate` without rebuilding other exhibitors or benching absent birds.

## Catalogue Reports Design

Reports page should expose the catalogue group explicitly:

- `4.1 Judges Catalogue` -> existing `generate_judges_catalogue`
- `4.2 Special Lists` -> new PDF based on special prize definitions and winners where available
- `4.3 Catalogue` -> existing show catalogue generator, renamed/exported with Access numbering
- `4.4 Marked Catalogue` -> new PDF showing benched entries plus result, NB, and special winner markings

Each report remains downloadable through the existing PDF preview window with Save As and Print.

## Update Service Design

Add a manual update checker:

1. Read `APP_VERSION` from `config.py`.
2. Query GitHub latest release metadata.
3. Compare semantic versions.
4. Find a `.exe` release asset.
5. Prompt user with version and changelog.
6. Download the asset to a temp/staging file.
7. Write a small PowerShell helper script in the app directory.
8. Start the helper, close the current app, replace the exe, restart the new exe.
9. Store the changelog in a local text file so the relaunched app can show it in a popup.

For source/dev runs, the checker may report update availability but should not try to replace `python.exe`.

## Error Handling

- Glossary seeding should be idempotent and tolerate missing optional species/class fields.
- Check-in should report skipped source entries instead of failing the whole operation.
- Reports should generate valid PDFs even when no data exists, with a human-readable message.
- Update checks should show clear messages for offline/network errors, missing release assets, invalid versions, or source/dev mode.

## Testing

Add focused tests for:

- `ClassGlossary` model creation through `ALL_MODELS`.
- Seeding from `class_def` and `species`.
- Search/filter/order using the seeded table.
- Check-in allocation order by class sequence for selected exhibitor entries.
- Catalogue report generators return valid PDFs for empty and populated data.
- Update version comparison and release asset selection without real network calls.

## Documentation

Update README and Help:

- Class Glossary uses seeded reference data and species filters.
- `Run Calculate (0010)` is a legacy/admin global rebuild.
- Check-in allocates exhibit numbers for selected arrived birds.
- Reports include Access catalogue items 4.1-4.4.
- Updates are checked manually from the app and require user confirmation.
