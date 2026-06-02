# Exhibitor Spreadsheet Import Design

## Goal

Add a CSV/Excel import path for exhibitors so clubs can migrate from spreadsheets without needing Microsoft Access. This import only manages exhibitor records and does not touch entries, classes, results, show settings, or historical data.

## Scope

Supported files:

- `.csv`
- `.xlsx`
- `.xls`

The importer will be launched from the Exhibitors screen with an `Import` button beside the existing Add/Edit/Delete/Export controls.

## Data Mapping

The import service will normalize common spreadsheet column headings into the existing `Exhibitor` fields.

Supported target fields:

- `exh_no`
- `name`
- `address`
- `suburb`
- `town`
- `zip_code`
- `tel_home`
- `tel_work`
- `cell_no`
- `fax_no`
- `email`
- `club`
- `club1`
- `print_address`

Common aliases should be accepted, including legacy MDB/export headings such as `ExhNo`, `Exhibitor #`, `Name`, `Address`, `Suburb`, `Town`, `ZipCode`, `TelHome`, `TelH`, `TelWork`, `TelW`, `Cell`, `CellNo`, `Email`, `E-mail`, `Club`, `Club1`, `PrintAddress`, and `Print Address`.

Unknown columns are ignored.

## Import Behavior

The import is intentionally conservative:

- Rows without a non-empty `name` are skipped and reported as row errors.
- `exh_no` is parsed as an integer when present; invalid values are reported and imported as no exhibitor number only if a name is present.
- `print_address` accepts common truthy values such as `yes`, `true`, `1`, and `y`.
- Existing exhibitors are matched by `exh_no` first when present, then by exact `name`.
- Matched exhibitors are updated.
- Unmatched exhibitors are created.
- Duplicate rows within the same spreadsheet follow the same update rules, so repeated imports are idempotent rather than creating duplicates.

## UI Behavior

`views/exhibitors_view.py` will add an `Import` button. Clicking it opens a file picker for CSV/Excel files. After import, the view reloads and a message box reports:

- Created count
- Updated count
- Skipped/error count
- The first few row-level errors, if any

No long-running background thread is required for this first version; typical exhibitor spreadsheets are small. If large files become common, the import can later move to a threaded dialog.

## Testing

Tests should cover:

- CSV import creates exhibitors.
- XLSX import creates exhibitors using pandas.
- Column aliases map into model fields correctly.
- Re-import updates existing exhibitors rather than duplicating them.
- Bad rows are skipped or partially imported with clear errors.

## Documentation

README should document the new Exhibitors import button, supported file types, and the recommended columns.
