# Show Day QOL Design

## Goal

Add two quality-of-life workflows for show-day operations:

- **Judge Mode:** a streamlined Results workflow for a steward/operator entering
  results on behalf of a judge.
- **Print Exhibitor Bundle:** a one-exhibitor PDF pack containing the documents
  and show information relevant to that exhibitor.

These features should build on the QR scanning, Results, Tickets, and Reports
work already in place. They should reduce show-day friction without moving core
authority away from the desktop app.

## Scope

This design covers the user experience and service boundaries for both features.
Implementation should be staged. Judge Mode and Exhibitor Bundle can be planned
and built separately after this design is approved.

The features do not replace existing Results, Reports, Tickets, or Exhibitors
views. They add focused workflows on top of those screens.

## Recommended Approach

Use a staged QOL release:

1. Build Judge Mode as a focused Results sub-mode.
2. Build Print Exhibitor Bundle as a report/bundle workflow launched from
   Reports, with a later optional shortcut from Exhibitors.

This avoids crowding existing screens and keeps testing straightforward. Judge
Mode is about entering results quickly. Exhibitor Bundle is about assembling PDF
documents. The two workflows should share existing data and helpers where
possible, but their UI and services should remain separate.

## Feature 1: Judge Mode

### Purpose

Judge Mode is for a steward or show operator who records decisions while the
judge works through birds. The judge does not need direct app access. The
operator uses the desktop app, scanner input, and keyboard shortcuts to keep the
process moving.

### User Flow

1. User opens Results.
2. User switches from normal Results entry to Judge Mode.
3. User optionally filters/selects a class.
4. User scans or types a cage-ticket QR/exhibit number.
5. App resolves the scan through the existing scan parser.
6. App shows the resolved exhibit context:
   - Exhibit/ticket number
   - Exhibitor number
   - Class code
   - Exhibitor name, if available
   - Current result or Not Benched status, if already recorded
7. User selects a placing/result or marks Not Benched.
8. Save records the result and returns focus to the scan field.
9. Recent entries are shown so mistakes can be spotted quickly.

### UI Shape

Judge Mode should feel denser and more operational than the normal Results
screen:

- Large scan/exhibit field with scanner buttons nearby.
- Result buttons or segmented controls for common placings.
- Clear resolved-exhibit context panel.
- One-click Not Benched.
- Recent results list with exhibit number, class, result, and NB state.
- Optional class filter to reduce visual noise during a judging session.

Normal Results should remain available for broad review, filtering, export, and
clear-all actions. Judge Mode should not expose destructive actions like Clear
All Results.

### Data And Behavior

Judge Mode should reuse:

- `parse_scan_to_auto_num` for QR/plain-number resolution.
- `record_result` for saving results.
- `mark_not_benched`, `unmark_not_benched`, and `is_not_benched` for NB state.
- Existing webcam and mobile scanner callbacks where practical.

Judge Mode should add a small service/query helper only if needed to resolve
display context from `CalculatedEntry`, `Result`, and `NotBenched`.

### Error Handling

- Empty scans show the existing scan parser error.
- Unknown or ambiguous legacy QR payloads show parser errors.
- Scans for exhibits outside the selected class should warn before saving or
  require the user to clear the class filter.
- Re-saving an already recorded result should update the result, consistent with
  existing Results behavior.
- Scanner failures should leave manual entry available.

### Testing

Automated tests should cover:

- Resolving scanned exhibit context.
- Class filter match and mismatch behavior.
- Saving a result through Judge Mode helper logic.
- Marking and unmarking Not Benched.
- Updating an existing result.

UI wiring can be verified with compile/import checks plus focused service tests.

## Feature 2: Print Exhibitor Bundle

### Purpose

Print Exhibitor Bundle gives the show secretary a quick way to search for an
exhibitor and generate one PDF containing the paperwork related to that
exhibitor's exhibition.

### Default Bundle Contents

The bundle should include, when available:

- Exhibitor details/contact summary.
- Entry Confirmation for that exhibitor.
- Cage tickets for that exhibitor.
- Late entries for that exhibitor.
- Results by Exhibitor section, only if results exist.
- Address label section, only if the exhibitor is flagged for address-label
  printing.

The bundle should not include unrelated exhibitors' records.

### User Flow

1. User opens Reports.
2. User clicks `Exhibitor Bundle`.
3. A searchable exhibitor selector dialog opens.
4. User searches by exhibitor number, name, email, or club.
5. User selects an exhibitor.
6. User confirms bundle options:
   - Include tickets
   - Include late entries
   - Include results if available
   - Include address label if flagged
7. App generates a single PDF and opens it in the existing PDF preview window.
8. User prints or saves from the preview.

### UI Shape

The first implementation should live in Reports to avoid crowding the
Exhibitors and Tickets views. A future shortcut can be added from Exhibitors
once the service is proven.

The selector dialog should be practical:

- Search field at the top.
- Results table/list with exhibitor number, name, club, and entry count.
- Generate button disabled until an exhibitor is selected.
- Clear status message when no matching exhibitor is found.

### Service Shape

Create a focused bundle service, likely `services/reports/exhibitor_bundle.py`.
It should own:

- Selecting the exhibitor by `exh_no`.
- Loading regular calculated entries or raw entries, matching existing entry
  confirmation behavior.
- Loading late entries.
- Loading ticket assignments for that exhibitor.
- Loading result and Not Benched state for the exhibitor's entries.
- Rendering a single PDF with clear section headings.

The service should reuse existing report base helpers for headers, footers, and
watermark/logo behavior. It may reuse ticket drawing logic if that helper is
made safely reusable, but it should not force a risky refactor of ticket PDF
generation during the first implementation.

### Error Handling

- No exhibitor selected: Generate stays disabled.
- Exhibitor has no entries: generate a valid PDF with exhibitor details and a
  clear "No entries found" message.
- Tickets unavailable because Calculate has not been run: include entry rows and
  show "Run Calculate to generate cage tickets."
- Results unavailable: omit the Results section unless requested, or include a
  short "No results recorded yet" note when the option is enabled.
- Address label unavailable because the exhibitor is not flagged: omit that
  section by default.

### Testing

Automated tests should cover:

- Empty/no-entry exhibitor bundle still produces a valid PDF.
- Bundle includes calculated entries and ticket numbers when Calculate data is
  present.
- Bundle includes late entries when requested.
- Bundle grows when results are present.
- Bundle includes address details only when the exhibitor is flagged.
- Missing exhibitor raises a clear service error.

UI wiring can be verified with compile/import checks and focused service tests.

## Documentation

README and in-app Help should document:

- Judge Mode as a steward/operator workflow.
- Judge Mode does not replace normal Results review/export.
- Exhibitor Bundle default contents.
- The need to run Calculate before cage tickets are available in bundles.
- Results sections appear only after results have been recorded.

## Open Questions For Implementation Planning

- Whether Judge Mode should be a toggle within Results or a separate sidebar
  item. The recommended first version is a toggle/button within Results.
- Whether the Exhibitor Bundle should initially include address labels as a
  dedicated section or as a small printable label block. The recommended first
  version is a small section inside the bundle PDF.
- Whether class filter mismatches in Judge Mode should block saves or warn. The
  recommended first version is to block saves until the filter is cleared or a
  matching exhibit is scanned.

