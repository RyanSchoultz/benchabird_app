# Show Day Capture - Design Spec
**Date:** 2026-06-03  
**Status:** Approved

---

## Problem

The current app exposes **Results**, **Special Winners**, and **Special Prizes** as separate top-level destinations. That mirrors the legacy Access switchboard more than the real show-day workflow.

At the show, judges complete the printed Judges Catalogue sheets. The show manager then captures the completed sheet details, marks not-benched birds, records placings, assigns special winners, checks the data, and prints the final outputs. These tasks are operationally one workflow, even though Access split them into separate forms and macros.

The modern app should not copy the Access macros 1:1. It should preserve the proven data relationships while presenting a cleaner show-day capture process.

---

## Legacy Evidence

The Access application grouped post-judging work under `5. Results`:

| Legacy menu | Action | Object |
|---:|---|---|
| 5.1 | Not Benched Entries | `0070 Not_Benched_M` |
| 5.2 | Special Winners | `0080 Specialwin_M` |
| 5.3 | Results | `0130 Results_M` |
| 5.4 | Update Hall of Fame | `0160 Hall_of_Fame_M` |

`Special Prizes` are different. The prize list is reference/setup data, maintained under show-schedule administration through `0140 Special_Lists_M`.

The verified shared reference is calculated-entry `AutoNum`. Runtime verification shows this is the exhibit/ticket/catalogue/special-winner/certificate number used by the Access outputs. `0051T Results_Clear_T` is a blank/template workspace, not a model to preserve directly. `Special_Winners_T` stores one special number mapped to one exhibit number, with `"Special"` as a marker.

---

## Decision

Add a new top-level **Show Day Capture** workspace.

The first rollout will **add** this screen while keeping the existing **Results** and **Special Winners** screens available as fallback tools during testing. The dashboard quick action should point to **Show Day Capture**.

**Special Prizes** remains a setup/reference screen. It is related to show-day capture, but it is not a live capture task. The new workspace may link to it for convenience, but it should not absorb prize-list CRUD in the first version.

---

## Navigation

Add **Show Day Capture** between **Show Participants** and **Results**.

```
Dashboard
Search
Show Setup
Exhibitors
Show Participants
Show Day Capture      <- new primary show-day result workflow
Results               <- temporary fallback
Special Winners       <- temporary fallback
Special Prizes        <- setup/reference data
Tickets
Reports
...
```

`Ctrl+R` should continue to work during rollout. In the first version it can navigate to the existing Results screen to avoid surprising users. After the fallback period, it can be moved to Show Day Capture.

---

## Workspace Structure

Use a hybrid staged workspace: one screen with a top stage strip and tab-like content areas.

Stages:

1. **Judging Capture**
2. **Special Winners**
3. **Validation**
4. **Publish**

The stage strip should show small status counters:

| Counter | Meaning |
|---|---|
| Categories reviewed | Categories/pages saved through Judging Capture |
| Results entered | Non-blank rows in `result` |
| NB | Rows in `not_benched` |
| Specials assigned | Rows in `special_winner` with an exhibit number |
| Issues | Current validation issue count |

The header should also show a short next-action message, such as:

- `Print Judges Catalogue before capture`
- `3 categories still need review`
- `Special winners ready to assign`
- `2 validation issues need attention`
- `Ready to publish final reports`

---

## Stage 1: Judging Capture

This stage is the main show-manager entry surface after judges return completed paper sheets.

It should reuse the existing Judging Capture behavior as the core:

- Select category/page.
- Show classes and exhibits in Judges Catalogue order.
- Choose placing with radio buttons.
- Mark `NB`.
- Clear a captured placing or NB mark.
- Reallocate a bird to another class when the judge sheet indicates a correction.
- Save at the end of the category/page with `Save Category Results`.

The first implementation may embed or adapt the existing `_judging_capture_dialog.py` content into the workspace. A modal fallback is acceptable if embedding it cleanly would create too much risk, but the navigation should still originate from the Show Day Capture workspace.

### Category Status

Add category/page completion status:

| Status | Meaning |
|---|---|
| Not started | No saved results or NB marks for that category |
| In progress | Some entries in the category have results or NB marks |
| Complete | All benched entries in the category have result or NB status |

Completion is a workflow aid, not a hard rule. The manager can still move to later stages for corrections or partial shows.

---

## Stage 2: Special Winners

This stage assigns special prize winners after category results are captured.

Special winners should be editable at any time, but the recommended flow is results first, specials second.

The stage should show:

- Special number.
- Description.
- Prize/cash details.
- Current winner exhibit number.
- Winner name, class, and result if assigned.
- Assignment status.

Assignment should support:

- Search by exhibit number.
- Search by exhibitor name.
- Search by class code or class description.
- Search/filter by captured result.
- Manual exhibit-number entry for corrections and unusual cases.

Candidate lists should prefer benched exhibits with captured results. The app should still allow a manual override because show rules and historical data may contain edge cases.

---

## Stage 3: Validation

Validation should surface problems that would make final reports misleading.

Initial issue checks:

| Issue | Detection | Action |
|---|---|---|
| Category not started | Category has benched entries but no results or NB marks | Jump to Judging Capture category |
| Category incomplete | Some benched entries in category have neither result nor NB | Jump to Judging Capture category |
| Duplicate placing | Same class has more than one exhibit with same placing value | Jump to Judging Capture class/category |
| Special missing winner | `special_list` row has no matching `special_winner.exhibit_no` | Jump to Special Winners |
| Special assigned to NB | `special_winner.exhibit_no` exists in `not_benched` | Jump to Special Winners |
| Result for unbenched exhibit | `result.exhibit_no` has no matching `calculated_entry.auto_num` | Jump to Results fallback or show correction action |
| Special for unbenched exhibit | `special_winner.exhibit_no` has no matching `calculated_entry.auto_num` | Jump to Special Winners |

Validation should be advisory in the first version. It should not block publishing, because some shows may intentionally leave fields blank.

---

## Stage 4: Publish

Publish groups post-capture outputs in one place.

Initial buttons:

- Marked Catalogue
- Results Sheet
- Special Winners
- Prize Money
- Results by Exhibitor
- 4.4 Marked Catalogue

Future buttons:

- Certificates
- Hall of Fame update
- Special Tickets

Report generation should use the existing report preview/save behavior from the Reports page. This stage is a convenience launchpad, not a duplicate PDF engine.

---

## Data Flow

| Task | Tables/services |
|---|---|
| Category capture | `calculated_entry`, `result`, `not_benched`, class/category reference data |
| Class reallocation | Existing judging catalogue capture service updates calculated entry class data |
| Special assignment | `special_list`, `special_winner`, `calculated_entry`, `result`, `not_benched` |
| Validation | Read-only checks over `calculated_entry`, `result`, `not_benched`, `special_list`, `special_winner` |
| Publish | Existing report services |

No legacy Access result template table should be recreated. The app should continue using the modern `result`, `not_benched`, `special_list`, and `special_winner` models.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Saving category with no selected changes | Show a calm "No changes to save" message |
| Duplicate placing selected | Allow save, but surface validation issue |
| Special winner exhibit number not found | Block normal assignment and show error; allow manual override only if explicitly provided in the assignment dialog |
| Special winner is NB | Allow save, surface validation issue |
| Report generated before validation is clean | Allow generation, show warning count in Publish stage |
| Existing fallback screens modify data | Refresh counters and validation when Show Day Capture regains focus |

---

## Testing

Add focused coverage for:

- Show Day Capture view imports without starting the app.
- Summary counters from seeded results, NB rows, special winners, and calculated entries.
- Validation detects missing specials, NB specials, duplicate placings, and orphan result references.
- Publish stage calls the existing report-generation functions.
- Navigation wiring exposes the new screen while preserving Results and Special Winners as fallback screens.

Manual verification:

1. Bench a small set of birds through Show Participants.
2. Open Show Day Capture.
3. Capture one category result set.
4. Assign at least one special winner.
5. Confirm validation counters update.
6. Generate Marked Catalogue and Results Sheet from Publish.

---

## Rollout

Version 1:

- Add Show Day Capture.
- Keep Results and Special Winners in the sidebar.
- Keep Special Prizes as setup/reference.
- Dashboard quick action points to Show Day Capture.
- Publish stage launches existing report services.

After testing:

- Move `Ctrl+R` to Show Day Capture.
- Remove old Results and Special Winners from primary navigation or move them to an admin/fallback area.
- Consider adding Certificates and Hall of Fame update as follow-up milestones.

---

## Out of Scope

- Rewriting the report PDF engines.
- Recreating Access macros 1:1.
- Removing the existing Results and Special Winners screens in the first version.
- Reworking Special Prizes CRUD beyond linking to it from the new workflow.
- Implementing Certificates or Hall of Fame update.
- Changing the verified exhibit-number mapping.
