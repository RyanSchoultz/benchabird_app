# Release Starter Database Design

## Goal

Benchabird releases should ship with a clean starter SQLite database so a club can start a new show without importing or cleaning historical data. Local development should continue to use the current working `benchabird.db`, including legacy/imported data when useful.

## Decision

Use a separate release-only starter database artifact. The development database remains `benchabird.db` in the project root. Release packaging will bundle the starter artifact as `benchabird.db` inside the PyInstaller executable.

This keeps development convenient while ensuring first-run release users receive a clean database.

## Starter Database Contents

The starter database must include the full application schema and reference data needed to run a normal show.

Include:

- Empty operational tables, including exhibitors, show entries, calculated entries, late entries, results, not-benched rows, and special winners.
- Default show settings structure, including any safe default `show_details` row if one exists or is created by the generation script.
- Reference catalogue tables used to classify entries, including `class_def`, `species`, and `main_class`.
- Other reference-only tables only if they are required for normal setup and do not contain historical club, exhibitor, entry, judging, or show result data.

Exclude:

- Real historical show data.
- Sample club names, exhibitor names, addresses, contact details, and emails.
- Entries, ticket allocations, calculated entries, results, not-benched records, late entries, special winners, archives, or copied show-year data.

## Files And Data Flow

Add a generated starter DB file outside the development DB path, preferably:

`release/benchabird-starter.db`

Add a script:

`scripts/create_starter_db.py`

The script will:

1. Open the current development database as the source.
2. Create a fresh SQLite destination database.
3. Create the application schema using the existing Peewee models.
4. Copy approved reference rows from the source into the destination.
5. Leave operational/show-specific tables empty.
6. Validate that blocked tables have zero rows in the destination.

Update `benchabird.spec` so PyInstaller packages:

`release/benchabird-starter.db` as `benchabird.db`

The runtime app does not need to know about the starter file. Existing first-run behavior already copies bundled `benchabird.db` beside the executable when no user database exists.

## Development Behavior

Local app runs continue to read and write:

`benchabird.db`

The starter generation script must not overwrite or mutate this file. It only reads from it and writes a separate starter DB.

Developers can keep using the legacy/imported DB locally while release builds use the clean starter artifact.

## Release Behavior

Before building a release exe, run:

`python scripts/create_starter_db.py`

Then build with the existing PyInstaller command. The release executable will contain the generated starter DB under the bundled name `benchabird.db`.

On first launch, the app copies that bundled clean starter DB to the executable folder. Existing user databases are not replaced.

## Validation

Add tests or script-level checks for:

- The starter DB file is created.
- Required schema tables exist.
- Reference tables such as `class_def`, `species`, and `main_class` are copied when present.
- Operational tables are empty.
- The source development DB is not modified.
- `benchabird.spec` points at the starter DB, not the development DB.

The release checklist should document that the starter DB generation step must run before building the exe.

## Risks And Uncertainty

The exact boundary between reference-only and show-specific tables should be verified against the current model list before implementation. Tables with names that sound reference-like but contain club-specific history must stay out of the starter DB unless explicitly approved.

The current `main.py` first-launch behavior opens the import wizard when the exhibitor table is empty. Because the clean starter DB intentionally has no exhibitors, implementation should review whether that wizard should still open for starter releases or whether a clean starter DB should navigate directly to the welcome/setup flow. This is a product decision to confirm during planning.
