# Per-Class Entry Limits Design

## Goal

Allow each class definition to optionally define a maximum number of entries. Entry capture should block additions that would exceed the class capacity.

## Data Model

Add `entry_limit` to `class_def`.

Rules:

- `NULL` means unlimited.
- `0` means unlimited.
- Positive integers define the maximum number of entries allowed for that class.

Existing databases should receive the column through startup migration. New databases and generated starter databases should get the field from the Peewee model schema.

## Validation Behavior

Normal show entries and late entries both count toward the same class limit.

When adding a normal entry:

1. Validate the class exists.
2. Validate the exhibitor does not already have the same class entry.
3. Count existing `show_entry` plus `late_entry` rows for the class.
4. If the count is at or above `entry_limit`, block the add with `EntryValidationError`.
5. Otherwise create the entry.

When adding a late entry:

1. Validate the class exists.
2. Count existing `show_entry` plus `late_entry` rows for the class.
3. If the count is at or above `entry_limit`, block the add with `LateEntryValidationError`.
4. Otherwise create the late entry.

Duplicate normal-entry errors should remain more specific than limit errors for the same exhibitor/class combination.

## UI Behavior

The existing entry and late-entry dialogs already show validation errors. No new dialog is required for v1.

Bulk add uses `add_entry`, so class-limit failures appear in its existing error list.

Class-limit management can be done through SQL/editor workflows for this iteration. A dedicated class settings screen can be added later if clubs need non-technical editing.

## Import And Starter DB Behavior

MDB imports should populate class definitions with `entry_limit=None`.

The release starter DB generator creates schema from models, so it will include the column automatically. Reference rows copied from older databases without `entry_limit` should still import cleanly.

## Testing

Tests should cover:

- Unlimited classes allow multiple entries.
- Limit of `1` blocks a second normal entry in the same class.
- Duplicate normal entry still reports the duplicate error before the limit error.
- Bulk add reports a limit error without crashing.
- Late entries count toward the class limit.
- A normal entry is blocked when late entries have already filled the limit.
