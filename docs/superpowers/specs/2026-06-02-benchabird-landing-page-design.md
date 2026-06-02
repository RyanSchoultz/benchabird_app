# Benchabird Landing Page — Design Spec

**Date:** 2026-06-02  
**Status:** Approved  

---

## Overview

A static HTML landing page for the Benchabird Show Manager desktop application. Replaces the legacy Next.js project at the repo root. Deployed via GitHub Pages from the `benchabird_app/` directory (the repo root on GitHub).

**Live repo:** https://github.com/RyanSchoultz/benchabird_app

---

## Hosting & Deployment

- **Platform:** GitHub Pages
- **Source:** `main` branch, repo root (`/`)
- **Files:** `index.html` + `style.css` at the root of `benchabird_app/`
- **Build step:** None — pure static HTML served directly
- **CDN dependencies:** Lucide icons via `https://unpkg.com/lucide@latest/dist/umd/lucide.js`
- **No Node.js, no build pipeline, no deploy action required**

GitHub Pages must be enabled in the repo settings: Settings → Pages → Source → Deploy from branch → `main` → `/ (root)`.

---

## Visual Theme

**Approach:** Light + Dark accent  
- Page background: white (`#ffffff`) / light grey (`#f8fafc`)  
- Primary accent: blue (`#2563eb`)  
- Dark accent band: navy (`#0f172a`) — used for the screenshot section and the open source strip  
- Body text: `#0f172a` / muted: `#64748b`  
- Icons: Lucide icon set (inline via CDN, no emojis anywhere)  
- Typography: system font stack (`-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`)

---

## Page Structure

Sections in order, top to bottom:

### 1. Nav (sticky)
- Logo: small blue gradient square icon + "Benchabird" wordmark
- Links: Features, Download (anchor links on same page)
- Right: GitHub pill button linking to `https://github.com/RyanSchoultz/benchabird_app`
- Background: white, `backdrop-filter: blur`, 1px bottom border
- Stays fixed at top on scroll

### 2. Hero
- Background: white
- Badge: "Free & Open Source · Windows Desktop" (blue pill, uppercase, Lucide `feather` icon — Lucide has no "bird" icon)
- Headline: "Show management done right." — large, bold, "done right." in blue
- Subtext: one sentence describing the app (replaces Access, offline-first, for cage-bird show organisers)
- CTAs:
  - Primary (blue, filled): "Download for Windows" — links to GitHub Releases latest
  - Secondary (outlined): "View on GitHub" — links to repo
- Meta row below CTAs: v1.0.0 · Windows 10/11 · 64-bit · No installation needed (Lucide tag/monitor/package icons)

### 3. Screenshot Band (dark)
- Background: `#0f172a` (navy)
- Contains a single app screenshot in a macOS-style window frame (rounded top corners, traffic-light dots, no bottom border — bleeds into next section)
- Placeholder: wireframe — to be replaced with real screenshot (`git_assets/image01.png` initially, more to be added)
- Box shadow gives a floating effect upward from the dark band

### 4. Features Grid
- Background: white
- Section label: "What's inside" (small caps, blue)
- Title: "Everything a show needs"
- Subtitle: "From first entry to final report — no spreadsheets, no Access, no internet required."
- 3×2 grid of feature cards (light grey background, blue icon badge, hover border highlight):
  1. **Cage Tickets** — ticket icon — PDF tickets with QR codes and logo watermark
  2. **Rapid Results Entry** — zap icon — keyboard-driven result entry flow
  3. **7 PDF Reports** — file-text icon — in-app preview before print/save
  4. **Special Winners** — trophy icon — assign prizes by exhibit number
  5. **Archives** — archive icon — named database snapshots, restore any show
  6. **Global Search** — search icon — search across all tables, jump to any record

### 5. Screenshot Gallery
- Background: light grey (`#f8fafc`), top/bottom 1px borders
- Section label: "In action"
- Title: "See it for yourself"
- 3-column grid of screenshot slots
- Initially rendered as dashed placeholder boxes (labelled: Dashboard, Results entry, PDF Reports)
- To be replaced with real `<img>` tags pointing to screenshots in `git_assets/` once provided
- Screenshots should have rounded corners and a subtle border

### 6. How It Works
- Background: white
- Section label: "Workflow"
- Title: "From setup to prize ceremony"
- 3 numbered steps connected by a horizontal line:
  1. **Setup & Exhibitors** — enter show details, upload club logo, add exhibitors
  2. **Entries & Tickets** — add class entries, run Calculate, print cage tickets as PDF
  3. **Results & Reports** — enter judging results, assign special winners, print all reports
- Step numbers: filled blue circles, shadow ring in light blue

### 7. Open Source Strip (dark)
- Background: `#0f172a` (navy)
- GitHub logo icon in a blue circle
- Title: "Free and open source"
- Subtitle: "MIT licensed. Built for the cage-bird community."
- Badges row: MIT License · Python · SQLite · Offline-first · No telemetry · No account needed
- CTA: "View on GitHub" (ghost button, dark variant)

### 8. Ko-fi
- Background: white
- Centred card with warm red border/background tint (`#fff5f5`, `#fecaca`)
- Coffee icon in a red circle
- Title: "Enjoying Benchabird?"
- Copy: free forever, buy the developer a coffee
- CTA button (red, `#ff5e5b`): "Support on Ko-fi" with heart icon — links to `https://ko-fi.com/schoultzie`

### 9. Footer
- Background: light grey (`#f8fafc`), 1px top border
- Left: small logo icon + "Benchabird Show Manager · MIT License"
- Right: GitHub, Download, Ko-fi links with small Lucide icons

---

## Files to Create

| File | Purpose |
|---|---|
| `benchabird_app/index.html` | Landing page markup |
| `benchabird_app/style.css` | All styles (extracted from inline) |

The mockup was built with inline `<style>` for iteration speed. The final implementation extracts all CSS into `style.css` and links it from `index.html`.

---

## Assets

| Asset | Source | Usage |
|---|---|---|
| `git_assets/image01.png` | Existing screenshot | Hero screenshot (initial) |
| Additional screenshots | To be provided by user | Gallery section (3 slots) |
| Lucide icons | CDN (`unpkg.com/lucide`) | All icons throughout page |

Screenshots in the gallery use `<img>` tags with `alt` text, `border-radius: 10px`, and `border: 1px solid #e2e8f0`.

---

## Links

| Element | URL |
|---|---|
| GitHub nav pill | `https://github.com/RyanSchoultz/benchabird_app` |
| Download button | `https://github.com/RyanSchoultz/benchabird_app/releases/latest/download/benchabird.exe` |
| View on GitHub buttons | `https://github.com/RyanSchoultz/benchabird_app` |
| Ko-fi button | `https://ko-fi.com/schoultzie` |

> **Note:** The download link assumes a GitHub Release is published with `benchabird.exe` attached. If no release exists yet, the link should point to `https://github.com/RyanSchoultz/benchabird_app/releases` (the releases listing page) instead.

---

## Out of Scope

- No analytics, tracking scripts, or cookies
- No contact form
- No blog or changelog section
- No dark mode toggle (page is light-first; the app is dark — contrast is intentional)
- No server-side rendering
