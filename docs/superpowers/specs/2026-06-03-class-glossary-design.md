# Class Glossary Design

## Context

The legacy Access database stores class-description data in `Classes_T`. The modern app already imports this into `class_def`:

- `Classes_T.CLASS` -> `class_def.class_code`
- `Classes_T.TYPE` -> `class_def.bird_type`
- `Classes_T.MAINCLASS` -> `class_def.main_class`
- `Classes_T.COLOUR` -> `class_def.colour`
- `Classes_T.AFRBESK` -> `class_def.afrbesk`
- `Classes_T.TYPEB` -> `class_def.type_b`
- `Classes_T.ClASSSEQ` -> `class_def.class_seq`

Access reports use this data as class descriptions. For example, exhibitor-list report controls combine `[Colour] & " " & [AFRBESK]` as the printable class description.

The current modern app has a `Notes` sidebar section backed by `notes_brochure`. That screen is less useful for the show-day workflow than a searchable class glossary.

## Goals

1. Replace the visible `Notes` section with `Class Glossary`.
2. Show a read-only glossary of class codes and descriptions from `class_def`.
3. Let users search by class code, type/category, main class, colour/description, Afrikaans text, and `TYPEB`.
4. Preserve existing notes data and imports; do not delete `notes_brochure`.
5. Update README and in-app Help to describe the glossary.

## Non-Goals

- Do not delete or mutate the original Access `.mdb` file.
- Do not delete the modern `NotesBrochure` model or imported notes data.
- Do not add class editing in this pass.
- Do not change class import mapping unless a defect is found.
- Do not redesign class setup or class-limit management.

## Proposed UI

Rename the sidebar item:

- From: `Notes`
- To: `Class Glossary`

The existing route key can remain `notes` for a smaller change, but the view class should present itself as `Class Glossary`.

The screen should be read-only and include:

- Page title: `Class Glossary`
- Search/filter field with placeholder such as `Filter by class, type, main class, or description...`
- Scrollable rows or a table with columns:
  - `Class`
  - `Type`
  - `Main Class`
  - `Description`
  - `Extra`

Description should be built from:

```text
colour + " " + afrbesk
```

If only one value exists, show that value. `Extra` should show `type_b` when present.

Rows should be ordered by:

1. `bird_type`
2. `main_class`
3. `class_seq`
4. `class_code`

## Data Source

Use `models.class_def.ClassDef`.

No new table is needed. The glossary is a read-only browse surface for existing class metadata.

## Error Handling

- If no classes exist, show `No class definitions found. Import legacy data or add classes first.`
- If a search has no matches, show `No matching classes.`
- Missing optional fields should render as blank text, not errors.

## Testing

Add focused tests:

- A pure formatter builds description from `colour` and `afrbesk`.
- Filtering matches class code, bird type, main class, colour, Afrikaans text, and `type_b`.
- The glossary view imports successfully.
- Main navigation contains `Class Glossary` and still routes through the existing `notes` key.

## Documentation

Update:

- `README.md` feature table and user guide.
- `views/help_view.py` sidebar/navigation text.
- Any project layout comments that still describe `notes_view.py` only as brochure notes.

## Design Decisions

1. The glossary is read-only for this pass.
2. The app keeps the existing `notes` route key to avoid a broad navigation migration.
3. Existing `notes_brochure` data remains available in the database but is no longer the primary sidebar screen.
