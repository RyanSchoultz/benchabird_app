# Landing Page Show-Day Refresh Design

**Date:** 2026-06-03
**Status:** Approved for planning

## Scope

Refresh the public static landing page at `benchabird_app/index.html` so it reflects the current Benchabird show-day workflow.

This is a content and structure refresh, not a full visual redesign. The existing `style.css`, page layout, GitHub Pages setup, download links, screenshot assets, Ko-fi section, and footer structure remain in place unless a small wording update is needed.

## Problem

The current landing page is still weighted toward the older story of entries, QR scanning, and generic results entry. The application now has a clearer show-day workflow:

1. Search exhibitors and bench arrived birds in Show Participants.
2. Print Judges Catalogue sheets for handwritten judging.
3. Capture completed judging sheets through Show Day Capture.
4. Assign special winners, validate issues, and publish printable outputs.

The landing page should describe this workflow plainly, without claiming that legacy Access macros or reports are migrated unless working replacement screens and reports exist.

## Goals

- Make the hero describe the practical show-day value: benching to final results.
- Replace stale QR-results emphasis with the current paper judging sheet plus capture workflow.
- Highlight Show Participants, Judges Catalogue, Show Day Capture, Validation/Publish, reports, and archives.
- Keep the page static and easy to deploy through GitHub Pages.
- Preserve the current light page style, screenshot band, gallery, open-source section, Ko-fi section, and download CTAs.

## Non-Goals

- No full landing-page redesign.
- No new screenshots in this pass.
- No JavaScript feature work beyond the existing Lucide/lightbox script.
- No changes to the Python desktop app.
- No changes to release publishing or GitHub Pages settings.
- No claims that unmapped Access macros are migrated.

## Content Updates

### Hero

The hero should move from the generic "Show management done right" story to the specific show-day workflow.

Recommended direction:

- Headline: `Run show day from benching to results.`
- Supporting copy: Benchabird replaces legacy Access workflows with an offline Windows app for check-in, judging sheets, result capture, and printable reports.
- Badge and CTA structure stay the same.
- Meta row should keep Windows, no install, offline, and judging/reporting oriented claims.

### Feature Grid

Replace the existing six feature cards with:

1. **Show Participants**: search exhibitors by name, email, number, or class, then bench arrived birds and allocate exhibit numbers.
2. **Judges Catalogue**: print Access-style judging sheets grouped for handwritten placings and NB marks.
3. **Show Day Capture**: capture completed judge pages with radio-button placings, NB marks, and class reallocations.
4. **Validation & Publish**: review missing results, duplicate placings, and special-winner issues before producing outputs.
5. **PDF Reports**: preview, print, and save catalogue, marked catalogue, results, specials, prize money, tickets, and exhibitor outputs.
6. **Archives**: save named snapshots before resets or major show-day changes.

### Gallery Captions

Keep the existing screenshots and lightbox behavior. Update captions so they do not overpromise new screenshots:

- `PDF Reports`: emphasize printable show outputs, including Judges Catalogue and marked catalogue.
- `SQL Editor`: keep as an advanced/admin tool.
- `Help Guide`: emphasize the built-in how-to for show-day workflows.

### Workflow Section

Replace the previous setup-entry-results flow with three show-day steps:

1. **Check in & bench**: search arriving exhibitors, bench present birds, add late entries where needed.
2. **Print judging sheets**: generate Judges Catalogue sheets for judges to complete by hand.
3. **Capture & publish**: enter placings and NB marks, assign specials, validate, then print final results.

### Open Source, Ko-fi, Footer

Keep the section structure and links. Minor copy updates are allowed if needed to remove stale claims.

## Files

| File | Change |
|---|---|
| `benchabird_app/index.html` | Update landing page copy, feature cards, gallery captions, workflow steps, and relevant alt text/meta copy |
| `benchabird_app/style.css` | No planned change |

## Verification

- Open `benchabird_app/index.html` locally or serve it statically.
- Confirm `style.css` loads.
- Confirm existing images in `git_assets/` still load.
- Confirm Lucide icons render after page load.
- Confirm download, GitHub, and Ko-fi links remain unchanged.
- Confirm there is no horizontal scroll at mobile widths from the content changes.

## Acceptance Criteria

- The landing page clearly describes the current show-day workflow.
- No stale "QR results scanning" first-order positioning remains.
- The page still works as a static GitHub Pages page.
- No app code or database files are changed by this task.
