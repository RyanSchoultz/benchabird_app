# Landing Page Show-Day Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh the static Benchabird landing page so it describes the current show-day workflow from benching through judging capture and final reports.

**Architecture:** This is an HTML-only content update to the existing static GitHub Pages landing page. The existing CSS, screenshot assets, lightbox script, download links, GitHub links, and Ko-fi links stay in place.

**Tech Stack:** HTML5, existing CSS in `benchabird_app/style.css`, existing Lucide CDN script, static local file verification.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `benchabird_app/index.html` | Public static landing page markup and copy | Update hero, meta description, feature cards, gallery captions, workflow steps, and stale alt text |
| `benchabird_app/style.css` | Existing landing page styles | No planned change |

## Task 1: Refresh Landing Page Copy

**Files:**
- Modify: `benchabird_app/index.html`

- [ ] **Step 1: Update the page metadata**

In `benchabird_app/index.html`, replace the current meta description with:

```html
<meta name="description" content="Benchabird Show Manager: free, offline-first Windows desktop app for cage-bird show organisers. Check in and bench birds, print judging sheets, capture results, and publish reports.">
```

- [ ] **Step 2: Update the hero copy**

In the hero section, replace:

```html
<h1>Show management<br><span>done right.</span></h1>
<p>Benchabird replaces your legacy Access database with a fast, offline-first desktop app built for cage-bird show organisers &mdash; no account, no internet, no installation required.</p>
```

with:

```html
<h1>Run show day<br><span>from benching to results.</span></h1>
<p>Benchabird replaces legacy Access workflows with a fast, offline-first Windows app for check-in, judging sheets, result capture, and printable reports.</p>
```

In the hero note, replace:

```html
<span><i data-lucide="qr-code" width="12" height="12"></i> QR results scanning</span>
```

with:

```html
<span><i data-lucide="clipboard-check" width="12" height="12"></i> Judging capture</span>
```

- [ ] **Step 3: Replace the six feature cards**

Inside `<div class="features-grid">`, replace the six existing `.feature-card` blocks with:

```html
<div class="feature-card">
  <div class="feature-icon"><i data-lucide="users" width="20" height="20"></i></div>
  <h4>Show Participants</h4>
  <p>Search by name, email, number, or class, then bench arrived birds and allocate exhibit numbers as they arrive.</p>
</div>
<div class="feature-card">
  <div class="feature-icon"><i data-lucide="clipboard-list" width="20" height="20"></i></div>
  <h4>Judges Catalogue</h4>
  <p>Print Access-style judging sheets grouped by category and class for handwritten placings and not-benched marks.</p>
</div>
<div class="feature-card">
  <div class="feature-icon"><i data-lucide="clipboard-check" width="20" height="20"></i></div>
  <h4>Show Day Capture</h4>
  <p>Capture completed judge pages with radio-button placings, NB marks, and class reallocations before saving each category.</p>
</div>
<div class="feature-card">
  <div class="feature-icon"><i data-lucide="shield-check" width="20" height="20"></i></div>
  <h4>Validation &amp; Publish</h4>
  <p>Review missing results, duplicate placings, and special-winner issues before generating final outputs.</p>
</div>
<div class="feature-card">
  <div class="feature-icon"><i data-lucide="file-text" width="20" height="20"></i></div>
  <h4>PDF Reports</h4>
  <p>Preview, print, and save catalogue, marked catalogue, results, specials, prize money, tickets, and exhibitor reports.</p>
</div>
<div class="feature-card">
  <div class="feature-icon"><i data-lucide="archive" width="20" height="20"></i></div>
  <h4>Archives</h4>
  <p>Save named database snapshots before resets or major show-day changes, then restore previous shows when needed.</p>
</div>
```

- [ ] **Step 4: Update gallery captions and alt text**

For the report screenshot, keep `src="git_assets/image02.png"` and replace the `alt` value with:

```html
alt="Benchabird Reports view with printable catalogue, judges catalogue, marked catalogue, results, specials, and exhibitor outputs"
```

Replace its caption subtext with:

```html
<div class="caption-sub">Printable show outputs, including judging sheets</div>
```

For the SQL screenshot, keep the current title and replace its caption subtext with:

```html
<div class="caption-sub">Advanced database access for trusted power users</div>
```

For the Help screenshot, replace its caption subtext with:

```html
<div class="caption-sub">Built-in how-to for setup, benching, capture, and reports</div>
```

- [ ] **Step 5: Update the workflow section**

In the `<!-- HOW IT WORKS -->` section, replace the subtitle and three steps with:

```html
<p class="section-sub">On show day, Benchabird keeps the paper workflow familiar while making capture and publishing faster.</p>
<div class="workflow-steps">
  <div class="step">
    <div class="step-number">1</div>
    <h4>Check in &amp; bench</h4>
    <p>Search arriving exhibitors, bench present birds, allocate exhibit numbers, and add late entries where needed.</p>
  </div>
  <div class="step">
    <div class="step-number">2</div>
    <h4>Print judging sheets</h4>
    <p>Generate the Judges Catalogue for judges to complete by hand, grouped by category, main class, and class.</p>
  </div>
  <div class="step">
    <div class="step-number">3</div>
    <h4>Capture &amp; publish</h4>
    <p>Enter placings and NB marks, assign special winners, validate issues, then print final results and catalogues.</p>
  </div>
</div>
```

- [ ] **Step 6: Search for stale positioning**

Run:

```powershell
rg -n "QR Results|QR results|Rapid Results|run Calculate|Entries &amp; Tickets|Results &amp; Reports|7 PDF Reports" benchabird_app\index.html
```

Expected output: no matches.

## Task 2: Verify Static Page

**Files:**
- Read: `benchabird_app/index.html`
- Read: `benchabird_app/style.css`
- Read: `benchabird_app/git_assets/image01.png`
- Read: `benchabird_app/git_assets/image02.png`
- Read: `benchabird_app/git_assets/image03.png`
- Read: `benchabird_app/git_assets/image04.png`

- [ ] **Step 1: Confirm local assets exist**

Run:

```powershell
Test-Path benchabird_app\style.css
Test-Path benchabird_app\git_assets\image01.png
Test-Path benchabird_app\git_assets\image02.png
Test-Path benchabird_app\git_assets\image03.png
Test-Path benchabird_app\git_assets\image04.png
```

Expected output: five `True` lines.

- [ ] **Step 2: Inspect changed HTML**

Run:

```powershell
rg -n "Run show day|Show Participants|Judges Catalogue|Show Day Capture|Validation &amp; Publish|Check in &amp; bench|Capture &amp; publish|Judging capture" benchabird_app\index.html
```

Expected output: matches for each refreshed phrase.

- [ ] **Step 3: Confirm external links remain unchanged**

Run:

```powershell
rg -n "github.com/RyanSchoultz/benchabird_app|releases/latest/download/benchabird.exe|ko-fi.com/schoultzie" benchabird_app\index.html
```

Expected output: GitHub repository, latest exe download, and Ko-fi links are still present.

- [ ] **Step 4: Commit the HTML change after verification**

Run:

```powershell
git -C benchabird_app add index.html
git -C benchabird_app commit -m "docs: refresh landing page show-day workflow"
```

Expected output: one commit that modifies `index.html`.

## Self-Review

- Spec coverage: the plan updates the hero, features, gallery captions, workflow section, stale claims, and static verification.
- Placeholder scan: no placeholder or deferred implementation language remains.
- Type consistency: HTML class names and existing section names match the current landing page.
