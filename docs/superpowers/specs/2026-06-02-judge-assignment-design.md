# Judge Assignment Design

## Goal

Allow a judge name to be assigned to each class definition and display that judge on class-facing reports.

## Data Model

Add `judge` to `class_def`.

Rules:

- `NULL` or blank means no judge assigned.
- Judge assignment is per class code.
- Existing databases receive the column through startup migration.
- New and starter databases receive the column through the Peewee model schema.

## Import Behavior

MDB class imports should set `judge=None`. The legacy class source does not currently provide a class-level judge assignment.

## Report Behavior

Show Catalogue:

- Join `class_def.judge` with calculated entries.
- Class section headers include `Judge: <name>` when a judge is assigned.
- If no judge is assigned, the header remains unchanged.

Results Sheet:

- Join `class_def.judge` through `calculated_entry.class_code`.
- Add a `Judge` column with the assigned judge name.
- Blank judge values are allowed.

## UI Behavior

For v1, judge assignment is managed through SQL Editor or database/spreadsheet workflows. A later Class Settings screen can expose both `entry_limit` and `judge` for non-technical editing.

## Testing

Tests should cover:

- `ClassDef` accepts `judge`.
- MDB import leaves `judge=None`.
- Show Catalogue generates a valid PDF when classes have judges.
- Results Sheet generates a valid PDF when classes have judges.
- Existing empty report states remain valid.

## Documentation

README should document `class_def.judge` and that assigned judges appear on Show Catalogue and Results Sheet.
