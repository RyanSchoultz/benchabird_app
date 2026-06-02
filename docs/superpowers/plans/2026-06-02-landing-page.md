# Benchabird Landing Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static HTML/CSS landing page for the Benchabird Show Manager desktop app, deployed via GitHub Pages from the `benchabird_app/` repo root.

**Architecture:** Two files — `index.html` (markup) and `style.css` (all styles). No build step, no framework, no JavaScript except Lucide icons via CDN. The page uses a light/white theme with a dark navy accent band around the app screenshot. All external links are hardcoded per the spec.

**Tech Stack:** HTML5, CSS3, Lucide icons CDN (`unpkg.com/lucide@latest/dist/umd/lucide.js`), GitHub Pages (branch: `main`, root: `/`)

**Spec:** `docs/superpowers/specs/2026-06-02-benchabird-landing-page-design.md`  
**Approved mockup:** `.superpowers/brainstorm/733-1780380809/landing-v3.html`

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `benchabird_app/index.html` | Create | Full page markup |
| `benchabird_app/style.css` | Create | All styles |
| `benchabird_app/.nojekyll` | Create | Tells GitHub Pages not to run Jekyll |
| `benchabird_app/.gitignore` | Modify | Add `.superpowers/` |

---

## Task 1: Create `style.css`

**Files:**
- Create: `benchabird_app/style.css`

- [ ] **Step 1: Create style.css with all styles**

Create `benchabird_app/style.css` with the following content (extracted and organised from the approved mockup):

```css
/* ── RESET & BASE ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #ffffff;
  color: #0f172a;
  font-size: 15px;
  line-height: 1.6;
}

img { display: block; max-width: 100%; height: auto; }
a { text-decoration: none; }
i[data-lucide] { display: inline-block; vertical-align: middle; flex-shrink: 0; }

/* ── NAV ── */
nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 56px;
  border-bottom: 1px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.95);
  position: sticky;
  top: 0;
  backdrop-filter: blur(12px);
  z-index: 100;
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  font-size: 1.05rem;
  color: #0f172a;
}

.nav-logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-links {
  display: flex;
  gap: 24px;
  align-items: center;
}

.nav-links a {
  color: #64748b;
  font-size: 0.88rem;
  transition: color 0.2s;
}

.nav-links a:hover { color: #0f172a; }

.nav-gh {
  display: inline-flex !important;
  align-items: center;
  gap: 6px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 7px 14px;
  color: #374151 !important;
  font-size: 0.84rem !important;
  transition: background 0.2s !important;
}

.nav-gh:hover { background: #e2e8f0 !important; }

/* ── HERO ── */
.hero {
  text-align: center;
  padding: 88px 56px 72px;
  max-width: 860px;
  margin: 0 auto;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #2563eb;
  border-radius: 20px;
  padding: 5px 14px;
  font-size: 0.76rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 26px;
  font-weight: 600;
}

.hero h1 {
  font-size: 3.2rem;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.03em;
  margin-bottom: 18px;
  color: #0f172a;
}

.hero h1 span { color: #2563eb; }

.hero p {
  font-size: 1.1rem;
  color: #64748b;
  max-width: 500px;
  margin: 0 auto 38px;
  line-height: 1.65;
}

.hero-ctas {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #2563eb;
  color: #fff;
  padding: 13px 26px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  transition: background 0.2s, transform 0.15s;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.3);
}

.btn-primary:hover { background: #1d4ed8; transform: translateY(-1px); }

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 1px solid #d1d5db;
  color: #374151;
  padding: 13px 26px;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.95rem;
  transition: background 0.2s, border-color 0.2s;
}

.btn-secondary:hover { background: #f9fafb; border-color: #9ca3af; }

.hero-note {
  font-size: 0.79rem;
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  margin-top: 4px;
}

.hero-note span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

/* ── SCREENSHOT BAND ── */
.screenshot-band {
  background: #0f172a;
  padding: 56px 56px 0;
}

.screenshot-wrap { max-width: 880px; margin: 0 auto; }

.screenshot-frame {
  border-radius: 12px 12px 0 0;
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-bottom: none;
  overflow: hidden;
  box-shadow: 0 -4px 60px rgba(0, 0, 0, 0.4), 0 24px 60px rgba(0, 0, 0, 0.5);
}

.screenshot-titlebar {
  background: #252535;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.dot { width: 11px; height: 11px; border-radius: 50%; }
.dot-red    { background: #ff5f57; }
.dot-yellow { background: #febc2e; }
.dot-green  { background: #28c840; }

.screenshot-img {
  display: block;
  width: 100%;
}

/* ── SECTION SHARED ── */
.section {
  max-width: 900px;
  margin: 0 auto;
  padding: 88px 56px;
}

.section-label {
  text-align: center;
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #2563eb;
  margin-bottom: 10px;
  font-weight: 700;
}

.section-title {
  text-align: center;
  font-size: 1.85rem;
  font-weight: 700;
  margin-bottom: 10px;
  color: #0f172a;
}

.section-sub {
  text-align: center;
  color: #64748b;
  font-size: 0.95rem;
  margin-bottom: 44px;
}

/* ── FEATURES GRID ── */
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.feature-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 22px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.feature-card:hover {
  border-color: #93c5fd;
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.07);
}

.feature-icon {
  width: 38px;
  height: 38px;
  background: #eff6ff;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14px;
  color: #2563eb;
}

.feature-card h4 { font-size: 0.9rem; font-weight: 600; margin-bottom: 6px; color: #111827; }
.feature-card p  { font-size: 0.82rem; color: #6b7280; line-height: 1.55; }

/* ── GALLERY ── */
.gallery-band {
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
  padding: 88px 56px;
}

.gallery-inner { max-width: 900px; margin: 0 auto; }

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 44px;
}

.gallery-img {
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  width: 100%;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.gallery-placeholder {
  border-radius: 10px;
  border: 2px dashed #cbd5e1;
  background: #fff;
  height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #94a3b8;
  font-size: 0.8rem;
}

/* ── HOW IT WORKS ── */
.workflow-steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  position: relative;
}

.workflow-steps::before {
  content: '';
  position: absolute;
  top: 24px;
  left: calc(16.66% + 12px);
  right: calc(16.66% + 12px);
  height: 1px;
  background: #bfdbfe;
  z-index: 0;
}

.step { text-align: center; padding: 0 16px; position: relative; z-index: 1; }

.step-number {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #2563eb;
  color: #fff;
  font-weight: 700;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  box-shadow: 0 0 0 6px #fff, 0 0 0 7px #bfdbfe;
}

.step h4 { font-size: 0.9rem; font-weight: 600; margin-bottom: 6px; color: #111827; }
.step p  { font-size: 0.82rem; color: #6b7280; line-height: 1.55; }

/* ── OPEN SOURCE STRIP ── */
.oss-strip {
  background: #0f172a;
  color: #e2e8f0;
  padding: 80px 56px;
  text-align: center;
}

.oss-icon {
  width: 52px;
  height: 52px;
  background: rgba(59, 130, 246, 0.15);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  color: #60a5fa;
}

.oss-strip h3 { font-size: 1.5rem; font-weight: 700; margin-bottom: 8px; color: #f1f5f9; }

.oss-strip p {
  color: #64748b;
  font-size: 0.92rem;
  margin-bottom: 28px;
  max-width: 440px;
  margin-left: auto;
  margin-right: auto;
}

.oss-badges {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 28px;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 6px;
  padding: 5px 12px;
  font-size: 0.78rem;
  color: #94a3b8;
}

.btn-secondary-dark {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.13);
  color: #e2e8f0;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.btn-secondary-dark:hover { background: rgba(255, 255, 255, 0.12); }

/* ── KO-FI ── */
.kofi-section { padding: 88px 56px; text-align: center; }

.kofi-card {
  max-width: 460px;
  margin: 0 auto;
  background: #fff5f5;
  border: 1px solid #fecaca;
  border-radius: 14px;
  padding: 44px 36px;
}

.kofi-icon-wrap {
  width: 54px;
  height: 54px;
  background: #fee2e2;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  color: #dc2626;
}

.kofi-card h3 { font-size: 1.2rem; font-weight: 700; margin-bottom: 8px; color: #111827; }
.kofi-card p  { color: #6b7280; font-size: 0.88rem; margin-bottom: 24px; line-height: 1.65; }

.btn-kofi {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #ff5e5b;
  color: #fff;
  padding: 12px 26px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.9rem;
  transition: background 0.2s, transform 0.15s;
  box-shadow: 0 4px 16px rgba(255, 94, 91, 0.25);
}

.btn-kofi:hover { background: #e84d4a; transform: translateY(-1px); }

/* ── FOOTER ── */
footer {
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  padding: 28px 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #9ca3af;
  font-size: 0.82rem;
}

footer a { color: #6b7280; transition: color 0.2s; }
footer a:hover { color: #374151; }

.footer-logo { display: flex; align-items: center; gap: 8px; }

.footer-logo-icon {
  width: 22px;
  height: 22px;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.footer-links { display: flex; gap: 20px; align-items: center; }
.footer-links a { display: inline-flex; align-items: center; gap: 5px; }

/* ── UTILITY ── */
.gh-svg { fill: currentColor; }
```

- [ ] **Step 2: Open `benchabird_app/index.html` in a browser (once created) to confirm stylesheet loads**

No file to open yet — this step validates once Task 2 is done. Move on.

- [ ] **Step 3: Commit**

```bash
cd benchabird_app
git add style.css
git commit -m "feat: add landing page stylesheet"
```

---

## Task 2: Create `index.html` — shell and head

**Files:**
- Create: `benchabird_app/index.html`

- [ ] **Step 1: Create the HTML shell**

Create `benchabird_app/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Benchabird Show Manager — free, offline-first Windows desktop app for cage-bird show organisers.">
  <title>Benchabird Show Manager</title>
  <link rel="stylesheet" href="style.css">
  <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js" defer></script>
</head>
<body>

  <!-- sections go here — added task by task -->

  <script>
    document.addEventListener('DOMContentLoaded', () => lucide.createIcons());
  </script>
</body>
</html>
```

- [ ] **Step 2: Open `benchabird_app/index.html` in a browser**

Open the file directly (`file:///.../benchabird_app/index.html`). Confirm:
- Page loads with no console errors
- Page background is white
- No 404 for `style.css` (check Network tab)

- [ ] **Step 3: Commit**

```bash
cd benchabird_app
git add index.html
git commit -m "feat: add landing page HTML shell"
```

---

## Task 3: Nav

**Files:**
- Modify: `benchabird_app/index.html` — add nav inside `<body>` before the script tag

- [ ] **Step 1: Add the nav markup**

Insert inside `<body>`, before `<script>`:

```html
<!-- NAV -->
<nav>
  <a class="nav-logo" href="#">
    <div class="nav-logo-icon">
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z"/>
        <line x1="16" y1="8" x2="2" y2="22"/>
        <line x1="17.5" y1="15" x2="9" y2="15"/>
      </svg>
    </div>
    Benchabird
  </a>
  <div class="nav-links">
    <a href="#features">Features</a>
    <a href="#download">Download</a>
    <a href="https://github.com/RyanSchoultz/benchabird_app" class="nav-gh" target="_blank" rel="noopener">
      <svg width="15" height="15" viewBox="0 0 24 24" class="gh-svg" aria-hidden="true"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>
      GitHub
    </a>
  </div>
</nav>
```

- [ ] **Step 2: Verify in browser**

Reload `index.html`. Confirm:
- Nav is visible and sticks to top when page is taller than viewport (add temporary `<div style="height:2000px"></div>` if needed, remove after)
- Logo icon renders (blue gradient square with feather SVG)
- "Benchabird" wordmark appears
- GitHub pill has correct background
- No horizontal scroll

- [ ] **Step 3: Commit**

```bash
cd benchabird_app
git add index.html
git commit -m "feat: add landing page nav"
```

---

## Task 4: Hero section

**Files:**
- Modify: `benchabird_app/index.html` — add hero after `</nav>`

- [ ] **Step 1: Add the hero markup**

Insert after `</nav>`:

```html
<!-- HERO -->
<section class="hero" id="download">
  <div class="hero-badge">
    <i data-lucide="feather" width="13" height="13"></i>
    Free &amp; Open Source &nbsp;&middot;&nbsp; Windows Desktop
  </div>
  <h1>Show management<br><span>done right.</span></h1>
  <p>Benchabird replaces your legacy Access database with a fast, offline-first desktop app built for cage-bird show organisers.</p>
  <div class="hero-ctas">
    <a href="https://github.com/RyanSchoultz/benchabird_app/releases/latest/download/benchabird.exe"
       class="btn-primary">
      <i data-lucide="download" width="17" height="17"></i>
      Download for Windows
    </a>
    <a href="https://github.com/RyanSchoultz/benchabird_app"
       class="btn-secondary" target="_blank" rel="noopener">
      <svg width="16" height="16" viewBox="0 0 24 24" class="gh-svg" aria-hidden="true"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>
      View on GitHub
    </a>
  </div>
  <div class="hero-note">
    <span><i data-lucide="tag" width="12" height="12"></i> v1.0.0</span>
    <span><i data-lucide="monitor" width="12" height="12"></i> Windows 10 / 11 &middot; 64-bit</span>
    <span><i data-lucide="package" width="12" height="12"></i> No installation needed</span>
  </div>
</section>
```

- [ ] **Step 2: Verify in browser**

Reload `index.html`. Confirm:
- Hero badge shows feather icon + text (check Lucide loaded — if icon is missing, the CDN script may not have fired yet; hard-reload with Ctrl+Shift+R)
- "done right." is blue (`#2563eb`)
- Both CTA buttons are present and sized correctly
- Meta row shows three items with small icons

- [ ] **Step 3: Commit**

```bash
cd benchabird_app
git add index.html
git commit -m "feat: add landing page hero section"
```

---

## Task 5: Screenshot band

**Files:**
- Modify: `benchabird_app/index.html` — add dark screenshot band after `</section>` (hero)

- [ ] **Step 1: Add the screenshot band markup**

Insert after the hero `</section>`:

```html
<!-- SCREENSHOT BAND -->
<div class="screenshot-band">
  <div class="screenshot-wrap">
    <div class="screenshot-frame">
      <div class="screenshot-titlebar" aria-hidden="true">
        <div class="dot dot-red"></div>
        <div class="dot dot-yellow"></div>
        <div class="dot dot-green"></div>
      </div>
      <img
        src="git_assets/image01.png"
        alt="Benchabird Show Manager — dashboard view showing show statistics and entry table"
        class="screenshot-img"
      >
    </div>
  </div>
</div>
```

- [ ] **Step 2: Verify in browser**

Reload `index.html`. Confirm:
- Dark navy band is visible below the hero
- The app screenshot (`git_assets/image01.png`) loads inside the frame
- Window chrome (traffic-light dots) appears above the screenshot
- Frame has rounded top corners only (bottom edge bleeds into next section seamlessly)
- Screenshot fills the full width of the frame

- [ ] **Step 3: Commit**

```bash
cd benchabird_app
git add index.html
git commit -m "feat: add screenshot band with app image"
```

---

## Task 6: Features grid

**Files:**
- Modify: `benchabird_app/index.html` — add features section after the screenshot band

- [ ] **Step 1: Add the features markup**

Insert after the screenshot band `</div>`:

```html
<!-- FEATURES -->
<section class="section" id="features">
  <div class="section-label">What's inside</div>
  <h2 class="section-title">Everything a show needs</h2>
  <p class="section-sub">From first entry to final report — no spreadsheets, no Access, no internet required.</p>
  <div class="features-grid">
    <div class="feature-card">
      <div class="feature-icon"><i data-lucide="ticket" width="20" height="20"></i></div>
      <h4>Cage Tickets</h4>
      <p>Print PDF tickets with exhibit number, class, exhibitor name, and a QR code. Club logo watermarked on every page.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon"><i data-lucide="zap" width="20" height="20"></i></div>
      <h4>Rapid Results Entry</h4>
      <p>Keyboard-driven flow — exhibit number, result, Enter. Chain through hundreds of entries without lifting your hands.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon"><i data-lucide="file-text" width="20" height="20"></i></div>
      <h4>7 PDF Reports</h4>
      <p>Results sheet, show catalogue, prize money, address tags, exhibitor list — preview in-app before printing.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon"><i data-lucide="trophy" width="20" height="20"></i></div>
      <h4>Special Winners</h4>
      <p>Assign special prizes by exhibit number. Manage the full prize list with trophy types and cash amounts.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon"><i data-lucide="archive" width="20" height="20"></i></div>
      <h4>Archives</h4>
      <p>Save named snapshots of the entire database. Restore any previous show — perfect before a season reset.</p>
    </div>
    <div class="feature-card">
      <div class="feature-icon"><i data-lucide="search" width="20" height="20"></i></div>
      <h4>Global Search</h4>
      <p>Search exhibitors, entries, results, and special winners at once. Jump directly to any record in one click.</p>
    </div>
  </div>
</section>
```

- [ ] **Step 2: Verify in browser**

Reload `index.html`. Confirm:
- Six cards appear in a 3×2 grid
- Each card has a blue icon badge, bold title, and grey description
- Hovering a card gives a blue border highlight
- "Features" nav link scrolls to this section

- [ ] **Step 3: Commit**

```bash
cd benchabird_app
git add index.html
git commit -m "feat: add features grid section"
```

---

## Task 7: Screenshot gallery

**Files:**
- Modify: `benchabird_app/index.html` — add gallery section after features

- [ ] **Step 1: Add gallery markup with placeholders**

Insert after the features `</section>`:

```html
<!-- SCREENSHOT GALLERY -->
<div class="gallery-band">
  <div class="gallery-inner">
    <div class="section-label">In action</div>
    <h2 class="section-title">See it for yourself</h2>
    <p class="section-sub">A closer look at the key views.</p>
    <div class="gallery-grid">
      <!--
        Replace each gallery-placeholder div with an <img> when screenshots are ready:
        <img src="git_assets/screenshot-dashboard.png" alt="Dashboard" class="gallery-img">
      -->
      <div class="gallery-placeholder">
        <i data-lucide="image" width="28" height="28"></i>
        <span>Dashboard</span>
      </div>
      <div class="gallery-placeholder">
        <i data-lucide="image" width="28" height="28"></i>
        <span>Results entry</span>
      </div>
      <div class="gallery-placeholder">
        <i data-lucide="image" width="28" height="28"></i>
        <span>PDF Reports</span>
      </div>
    </div>
  </div>
</div>
```

- [ ] **Step 2: Verify in browser**

Reload `index.html`. Confirm:
- Light grey band appears below features
- Three dashed placeholder boxes appear in a 3-column grid
- Each has a grey image icon and label text

- [ ] **Step 3: Commit**

```bash
cd benchabird_app
git add index.html
git commit -m "feat: add screenshot gallery section (placeholders)"
```

---

## Task 8: How it works

**Files:**
- Modify: `benchabird_app/index.html` — add workflow section after gallery

- [ ] **Step 1: Add the workflow markup**

Insert after the gallery band closing `</div>`:

```html
<!-- HOW IT WORKS -->
<section class="section">
  <div class="section-label">Workflow</div>
  <h2 class="section-title">From setup to prize ceremony</h2>
  <p class="section-sub">A typical show runs in a few clear steps — Benchabird guides you through each one.</p>
  <div class="workflow-steps">
    <div class="step">
      <div class="step-number">1</div>
      <h4>Setup &amp; Exhibitors</h4>
      <p>Enter show details, upload your club logo, and add all registered exhibitors.</p>
    </div>
    <div class="step">
      <div class="step-number">2</div>
      <h4>Entries &amp; Tickets</h4>
      <p>Add class entries, run Calculate to assign ticket numbers, then print cage tickets as PDF.</p>
    </div>
    <div class="step">
      <div class="step-number">3</div>
      <h4>Results &amp; Reports</h4>
      <p>Enter judging results, assign special winners, then generate and print all seven PDF reports.</p>
    </div>
  </div>
</section>
```

- [ ] **Step 2: Verify in browser**

Reload `index.html`. Confirm:
- Three numbered circles appear, connected by a horizontal blue line
- Numbers are filled blue circles with a white ring/shadow effect
- Steps are evenly spaced in a 3-column layout

- [ ] **Step 3: Commit**

```bash
cd benchabird_app
git add index.html
git commit -m "feat: add how-it-works workflow section"
```

---

## Task 9: Open source strip

**Files:**
- Modify: `benchabird_app/index.html` — add OSS section after workflow

- [ ] **Step 1: Add the OSS strip markup**

Insert after the workflow `</section>`:

```html
<!-- OPEN SOURCE -->
<div class="oss-strip">
  <div class="oss-icon">
    <svg width="24" height="24" viewBox="0 0 24 24" class="gh-svg" aria-hidden="true"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>
  </div>
  <h3>Free and open source</h3>
  <p>MIT licensed. Built for the cage-bird community. Fork it, contribute, or just use it — no strings attached.</p>
  <div class="oss-badges">
    <span class="badge"><i data-lucide="scale" width="12" height="12"></i> MIT License</span>
    <span class="badge"><i data-lucide="database" width="12" height="12"></i> Python &middot; SQLite</span>
    <span class="badge"><i data-lucide="wifi-off" width="12" height="12"></i> Offline-first</span>
    <span class="badge"><i data-lucide="shield-off" width="12" height="12"></i> No telemetry</span>
    <span class="badge"><i data-lucide="user-x" width="12" height="12"></i> No account needed</span>
  </div>
  <a href="https://github.com/RyanSchoultz/benchabird_app"
     class="btn-secondary-dark" target="_blank" rel="noopener">
    <svg width="16" height="16" viewBox="0 0 24 24" class="gh-svg" aria-hidden="true"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>
    View on GitHub
  </a>
</div>
```

- [ ] **Step 2: Verify in browser**

Reload `index.html`. Confirm:
- Dark navy band with GitHub circle icon appears
- Five badge pills render in a row (wrapping on narrow screens is fine)
- "View on GitHub" ghost button is visible on the dark background

- [ ] **Step 3: Commit**

```bash
cd benchabird_app
git add index.html
git commit -m "feat: add open source strip section"
```

---

## Task 10: Ko-fi and footer

**Files:**
- Modify: `benchabird_app/index.html` — add Ko-fi section and footer

- [ ] **Step 1: Add Ko-fi and footer markup**

Insert after the OSS strip closing `</div>`:

```html
<!-- KO-FI -->
<section class="kofi-section">
  <div class="kofi-card">
    <div class="kofi-icon-wrap">
      <i data-lucide="coffee" width="24" height="24"></i>
    </div>
    <h3>Enjoying Benchabird?</h3>
    <p>It's free to use and always will be. If it saves you time at your next show, consider buying the developer a coffee.</p>
    <a href="https://ko-fi.com/schoultzie" class="btn-kofi" target="_blank" rel="noopener">
      <i data-lucide="heart" width="16" height="16"></i>
      Support on Ko-fi
    </a>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <div class="footer-logo">
    <div class="footer-logo-icon" aria-hidden="true">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z"/><line x1="16" y1="8" x2="2" y2="22"/></svg>
    </div>
    <span>Benchabird Show Manager &nbsp;&middot;&nbsp; MIT License</span>
  </div>
  <div class="footer-links">
    <a href="https://github.com/RyanSchoultz/benchabird_app" target="_blank" rel="noopener">
      <svg width="14" height="14" viewBox="0 0 24 24" class="gh-svg" aria-hidden="true"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>
      GitHub
    </a>
    <a href="https://github.com/RyanSchoultz/benchabird_app/releases/latest/download/benchabird.exe">
      <i data-lucide="download" width="13" height="13"></i>
      Download
    </a>
    <a href="https://ko-fi.com/schoultzie" target="_blank" rel="noopener">
      <i data-lucide="coffee" width="13" height="13"></i>
      Ko-fi
    </a>
  </div>
</footer>
```

- [ ] **Step 2: Verify in browser**

Scroll to the bottom of the page. Confirm:
- Ko-fi card is centred, warm red border, coffee icon in red circle
- "Support on Ko-fi" red button is visible
- Footer is light grey with logo left and three links right
- All three footer links have small icons

- [ ] **Step 3: Scroll through the entire page**

Scroll from top to bottom in one pass. Confirm the full section order:
Nav → Hero → Screenshot band → Features → Gallery → Workflow → OSS strip → Ko-fi → Footer

- [ ] **Step 4: Commit**

```bash
cd benchabird_app
git add index.html
git commit -m "feat: add ko-fi section and footer"
```

---

## Task 11: GitHub Pages setup

**Files:**
- Create: `benchabird_app/.nojekyll`
- Modify: `benchabird_app/.gitignore`

- [ ] **Step 1: Create `.nojekyll`**

Create an empty file `benchabird_app/.nojekyll`. This tells GitHub Pages to skip Jekyll processing, which is required when filenames or directories start with underscores or when serving plain HTML directly.

```bash
cd benchabird_app
type nul > .nojekyll   # Windows (PowerShell: New-Item .nojekyll -ItemType File)
```

Or via the Write tool: create `benchabird_app/.nojekyll` with empty content.

- [ ] **Step 2: Add `.superpowers/` to `.gitignore`**

Open `benchabird_app/.gitignore` and append:

```
.superpowers/
```

This keeps the brainstorm mockup files out of the repo.

- [ ] **Step 3: Commit**

```bash
cd benchabird_app
git add .nojekyll .gitignore
git commit -m "chore: add .nojekyll and gitignore update for GitHub Pages"
```

- [ ] **Step 4: Enable GitHub Pages in repo settings**

In the GitHub repo (https://github.com/RyanSchoultz/benchabird_app):
1. Go to **Settings → Pages**
2. Under **Source**, select **Deploy from a branch**
3. Branch: `main` · Folder: `/ (root)`
4. Click **Save**

After the next push, GitHub will serve `index.html` at `https://ryanschoultz.github.io/benchabird_app/`.

---

## Task 12: Final verification

- [ ] **Step 1: Check all links**

Open `index.html` locally and verify each link:

| Link | Expected target |
|---|---|
| Nav logo | `#` (page top) |
| Nav Features | `#features` (scrolls to features grid) |
| Nav Download | `#download` (scrolls to hero) |
| Nav GitHub | `https://github.com/RyanSchoultz/benchabird_app` |
| Hero Download button | `https://github.com/RyanSchoultz/benchabird_app/releases/latest/download/benchabird.exe` |
| Hero View on GitHub | `https://github.com/RyanSchoultz/benchabird_app` |
| OSS View on GitHub | `https://github.com/RyanSchoultz/benchabird_app` |
| Ko-fi button | `https://ko-fi.com/schoultzie` |
| Footer GitHub | `https://github.com/RyanSchoultz/benchabird_app` |
| Footer Download | `https://github.com/RyanSchoultz/benchabird_app/releases/latest/download/benchabird.exe` |
| Footer Ko-fi | `https://ko-fi.com/schoultzie` |

- [ ] **Step 2: Check all Lucide icons rendered**

Open browser DevTools → Elements. Search for `i[data-lucide]`. All should have been replaced with `<svg>` elements by `lucide.createIcons()`. If any `<i>` tags remain, the CDN script didn't fire — ensure the `defer` attribute and `DOMContentLoaded` listener are both present.

- [ ] **Step 3: Push to GitHub**

```bash
cd benchabird_app
git push origin main
```

Wait ~60 seconds for GitHub Pages to build. Visit `https://ryanschoultz.github.io/benchabird_app/` and confirm the page is live.

- [ ] **Step 4: Smoke-test the live page**

On the live GitHub Pages URL, verify:
- Page loads (no 404)
- `style.css` loads (no 404 in Network tab)
- Screenshot image loads (`git_assets/image01.png` — relative path)
- Lucide icons all render (no blank squares)
- Download button link resolves (GitHub will 404 until a Release is published — that's expected; confirm the URL is correct)
