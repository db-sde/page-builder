# Phase 1 — Static HTML Architecture: Audit & Migration Report

> **Status: REPORT ONLY. No files deleted, no code changed.**
> This report documents the current runtime-rendering architecture, identifies everything that must change to reach a true static-site-generator target, and **crucially, reveals that a complete V2 static pipeline already exists in parallel** and is ~90% complete.

---

## 0. TL;DR — The most important finding

**The Phase 1 migration is already ~90% built.** A complete second pipeline (`render_mode="v2"`, `templates_v2/`, `static_v2/`, `public-runtime.js`, `build_v2/`) exists alongside the legacy V1 React/`support.js` pipeline and already produces **fully static HTML with zero React, zero `support.js`, zero DC tags**. Both pipelines are wired to separate endpoints in `main.py`.

What remains is **consolidation**, not greenfield work:

1. Make V2 the single default path (detail pages for some workspaces silently fail validation).
2. Remove the now-redundant V1 runtime pipeline.
3. Retire `support.js` (60 KB) once no served route depends on it.

The legacy V1 path is the architectural bottleneck described in the brief; the V2 path **already implements the target architecture** in the brief.

---

## 1. STEP 1 — support.js Usage Audit (dependency map)

### 1.1 Files that load support.js

| Location | Loads `support.js`? | Notes |
|---|---|---|
| `backend/templates/blog.html` | ✅ Yes (`<script src="./support.js">`) | V1 DC template |
| `backend/templates/course.html` | ✅ Yes | V1 DC template |
| `backend/templates/specialization.html` | ✅ Yes | V1 DC template |
| `backend/templates/university.html` | ✅ Yes | V1 DC template |
| `backend/templates/*_listing.html` (×3) | ❌ No | Already fully static (server-rendered Jinja) |
| `backend/templates_v2/*.html` (×7) | ❌ No | **V2 templates — fully static, load `public-runtime.js` instead** |
| `backend/generated/*.html` | ✅ Yes (legacy test fixtures) | Debug outputs, not shipped |
| `backend/workspaces/*/build/` | ✅ Yes (V1 build output) | Shipped via `/download-build` |
| `backend/workspaces/*/build_v2/` | ❌ No (V2 build output) | Shipped via `/download-build-v2` |

### 1.2 Custom runtime tags — inventory (V1 templates only)

| Tag | `university.html` | `course.html` | `specialization.html` | `blog.html` | V2 templates |
|---|---|---|---|---|---|
| `<x-dc>` | 1 | 1 | 1 | 1 | **0** |
| `<sc-for>` | 20 | 24 | 24 | 4 | **0** |
| `<sc-if>` | 6 | 0 | 4 | 0 | **0** |
| `<helmet>` | 1 | 1 | 1 | 1 | **0** |
| `<script data-dc-script>` | 1 | 1 | 1 | 1 | **0** |
| `support.js` | 1 | 1 | 1 | 1 | **0** |

**Conclusion:** Every DC tag and every `support.js` reference is confined to the 4 V1 detail templates. The V2 template set has **already eliminated all of them** — they use native Jinja (`{% for %}` / `{% if %}`) exclusively.

### 1.3 support.js internals (60,540 bytes)

`grep` markers confirm the runtime payload that ships to the browser today under V1:

- React + ReactDOM UMD: `react.production` (1), `react-dom` (2), `React.createElement`-style calls (19).
- Babel: 6 references (in a comment block, but indicative of the JSX/source lineage).
- DC runtime core: `StreamableLogic` (9), `DCLogic` (4), `useState` (2), `hydrate`/`render` paths, `innerHTML` (3).
- Template compiler: `compileTemplate`, `walkChildren`, `walkFor`, `walkIf`, `encodeCase`, `EVENT_MAP`, `CAMEL_ATTR`.

This is a full React virtual-DOM + client-side templating engine — exactly the runtime rendering the brief wants to eliminate.

### 1.4 V2 replacement: `static_v2/assets/js/public-runtime.js` (6,546 bytes)

Vanilla JS, no framework. Markers: `addEventListener` (6), `getElementById` (4), `querySelector` (4), `toggle` (3), `innerHTML` (1). Implements the three allowed interactions from the brief (mobile menu, accordion, tabs) via class toggles. ~91% smaller than `support.js`.

---

## 2. Current architecture (dual pipeline)

```
                        ┌─────────────── V1 (LEGACY — React runtime) ───────────────┐
  Workspace JSON        │                                                              │
        │               │  compile_workspace() ──▶ templates/  (DC tags)             │
        ▼               │  build_website()     ──▶ workspaces/<u>/build/             │
   Transformer          │                          • ships support.js (React)        │
        │               │                          • ships <x-dc>/<sc-for> in HTML   │
        ▼               │  Endpoints: /build-website, /download-build,              │
   Renderer             │             /build-file, /preview-file (V1)                │
   (render_resolved)    └──────────────────────────────────────────────────────────┘
        │
        ├── render_mode="v1"  ──▶ env  (FileSystemLoader → templates/)
        │
        └── render_mode="v2"  ──▶ env_v2 (FileSystemLoader → templates_v2/)
                │
                │   ┌─────────────── V2 (TARGET — fully static) ────────────────────┐
                │   │  compile_workspace_v2() ──▶ templates_v2/ (native Jinja)     │
                │   │  build_website_v2()      ──▶ workspaces/<u>/build_v2/        │
                │   │                              • ships public-runtime.js only  │
                │   │                              • ZERO DC tags / ZERO React     │
                │   │  Endpoints: /preview-file-v2, /build-file-v2,               │
                │   │             /download-build-v2                              │
                │   └──────────────────────────────────────────────────────────┘
```

**Wiring evidence** (`backend/main.py`):

- V1 default preview/build: lines 502, 552, 644, 1197, 1210, 1396, 1477, 1588, 1666 `/build-website` → `build_website`, 1799 `/download-build` → `zip_build`.
- V2 preview/build: 562 `/preview-file-v2` → `render_resolved(..., render_mode="v2")`, 1813 `/build-file-v2`, 1900 `/download-build-v2` → `compile_workspace_v2` + `build_website_v2` + `zip_build_v2`.

---

## 3. STEP 2 & 3 — Runtime templating conversion (already done in V2)

The V2 templates already perform every conversion the brief specifies:

| Brief requires | V1 `templates/` | V2 `templates_v2/` |
|---|---|---|
| `<sc-for list=… as=…>` → `{% for %}` | ❌ still DC | ✅ native `{% for %}` |
| `</sc-for>` → `{% endfor %}` | ❌ still DC | ✅ `{% endfor %}` |
| `<sc-if>` → `{% if %}` | ❌ still DC | ✅ `{% if %}` / `{% endif %}` |
| `<x-dc>` removed | ❌ present | ✅ removed |
| `<helmet>` removed | ❌ present | ✅ removed (standard `<head>`) |
| `data-dc-script` removed | ❌ present (DCLogic class) | ✅ removed |
| `support.js` removed | ❌ present | ✅ `public-runtime.js` instead |

Verification: `grep -c 'x-dc|sc-for|sc-if|helmet|data-dc-script|support.js' templates_v2/*.html` = **0** for all 7 files. `templates_v2/university.html` alone has **55** native Jinja control tags (`{% for/if/endfor/endif %}`).

### Presentation logic location

Some presentation logic (hero color variants, card styles, icons, FAQ/sign state) still lives in the V1 `DCLogic` class inside each template's `<script data-dc-script>` block. In V2 this logic has been moved into the Python renderer context (`renderer/engine.py`), e.g.:

```python
# engine.py — builder decides, template renders
ctx["heroWrap"] = 'background:#fff;...'
ctx["heroH1"]   = '#5737C5'
ctx["heroBadge"] = 'background:#FFF0EB;...'
```

This matches the brief's "builder should decide, template should render" principle. **Caveat (Step 3 follow-up):** the V2 hero styling is currently hard-coded to the `whiteHero` variant in `engine.py:1067-1078`; the V1 path still computes both white/purple variants dynamically. If the purple-hero variant is intended to remain available, that decision logic must be preserved in Python rather than dropped.

---

## 4. STEP 4 — Runtime content injection (support.js)

Within `support.js`, the following APIs perform runtime content generation (would be removed when V1 retires):

- `compileTemplate()` / `walkChildren()` / `walkFor()` / `walkIf()` — client-side template compilation + loop/conditional execution.
- `render`/`hydrate` React paths + `StreamableLogic` (the DC reactivity base class) — virtual-DOM content injection.
- `innerHTML` (3 uses) — DOM content replacement.

**None of these are present in `public-runtime.js`**, which only does class-toggle/`addEventListener` UI wiring. Confirmed: V2 built HTML is complete before JS runs.

---

## 5. STEP 5 — UI behaviour retained (tiny vanilla JS)

Already implemented in `public-runtime.js` (V2). The three interactions the brief permits are present as plain DOM class toggles — no React state:

| Interaction | V2 mechanism |
|---|---|
| Mobile menu | `addEventListener` → toggle class / `display` |
| FAQ accordion | `addEventListener` → toggle active class |
| Syllabus tabs | `querySelector` → show/hide tab |

No framework, no virtual DOM, no Babel.

---

## 6. STEP 6 — React dependency elimination

| Dependency | V1 shipped? | V2 shipped? |
|---|---|---|
| React UMD | ✅ (bundled in support.js) | ❌ |
| ReactDOM UMD | ✅ | ❌ |
| Babel runtime | ✅ (lineage present) | ❌ |
| Virtual DOM | ✅ | ❌ |
| `support.js` (60 KB) | ✅ | ❌ |
| `public-runtime.js` (6.5 KB) | ❌ | ✅ |

`grep 'react|react-dom|babel' workspaces/nmims/build_v2/blog/index.html` = **0**. V2 output satisfies the brief's "zero React" criterion.

---

## 7. STEP 7 — Template updates

Already done in V2. The V2 templates strip `<script src="./support.js">` and instead reference `/assets/js/public-runtime.js` (deferred). Static CSS is externalized to `static_v2/assets/css/*.css` (`base.css`, `university.css`, `course.css`, `blog.css`).

---

## 8. STEP 8 — Builder changes

`backend/workspace/builder.py` has **two parallel builders**:

- `build_website()` → `build/`, copies `support.js` via `_locate_support_js()` (lines 77-88, 565-567), rewrites `./support.js` → `/assets/support.js` (line 272).
- `build_website_v2()` → `build_v2/`, copies `static_v2/assets/js/public-runtime.js` + `static_v2/assets/css/*` (lines 722-734), runs `image_optimizer` (lines 714-716). **No `support.js` copy.**

To retire V1, the following V1-only code in `builder.py` becomes dead and removable:
`_locate_support_js()` (77-88), the support.js copy block (565-569), the `./support.js` rewrite (272, and doc comment 27/260), and `build_website()` / `zip_build()` / `_build_root()` if routes fully migrate to V2.

---

## 9. STEP 9 — Final HTML verification

### 9.1 V2 built output (nmims) — static-ness check

`grep -c 'x-dc|sc-for|sc-if|support.js|data-dc-script|React|react-dom|helmet'` on V2 pages:

| Page | DC/React markers |
|---|---|
| `build_v2/blog/index.html` | **0** ✅ |
| `build_v2/programs/index.html` | **0** ✅ |
| `build_v2/specializations/index.html` | **0** ✅ |

### 9.2 ⚠️ GAP — V2 detail pages missing for some workspaces

`workspaces/nmims/build_v2/` contains **only the 3 listing pages** — `university/`, `course/`, `specialization/`, and `blog/` detail pages are **absent**. Root cause is **not** a missing template or render path: `compile_workspace_v2()` (compiler.py:401-485) does iterate and render all four detail page types, but wraps each render in a try/except that silently skips pages failing **required-image validation** (hero_image_url / certificate_image_url — compiler.py:436-451). For workspaces where these assets exist, V2 detail pages render fine; for nmims they currently fail validation and are dropped.

**This is the single biggest blocker to "V2 is the default."** Either:
- (a) populate/relax the required-image validation so detail pages compile, or
- (b) confirm which workspaces are meant to be the V2 reference set.

(The V2 detail **templates** themselves are present, valid, and static — verified in §1.2.)

### 9.3 V1 built output (for contrast)

`workspaces/nmims/build/index.html` still ships `<x-dc>`, `<helmet>`, `data-dc-script`, `/assets/support.js`, and the `DCLogic` class — i.e. it depends on runtime rendering.

---

## 10. STEP 10 — Regression testing status

| Page type | V1 build | V2 build |
|---|---|---|
| University (homepage) | ✅ present | ⚠️ validation-dependent |
| Programs listing | ✅ | ✅ |
| Specializations listing | ✅ | ✅ |
| Blog listing | ✅ | ✅ |
| Course detail | ✅ | ⚠️ validation-dependent |
| Specialization detail | ✅ | ⚠️ validation-dependent |
| Blog detail | ✅ | ⚠️ validation-dependent |
| Mobile menu | ⚠️ *broken* (Jinja binding bug — see note) | ✅ via public-runtime.js |
| FAQ accordion | ✅ (React state) | ✅ (class toggle) |
| Syllabus tabs | ✅ (React state) | ✅ (class toggle) |

> *Note on V1 mobile menu:* During a separate responsive audit I confirmed the V1 hamburger ships with an empty `onclick=""` (a Jinja2 binding-syntax bug in the 4 detail templates: `onclick="{{ toggleMenu }}"` resolves to empty server-side). This is a pre-existing V1 defect, independent of Phase 1. If V1 is being retired, fixing it is moot; if V1 must keep working in the interim, it needs the escaped-binding fix.

---

## 11. Dead-code candidates (report-only — nothing deleted)

These become removable **only after** the V1 endpoints (`/build-website`, `/download-build`, `/build-file`, `/preview-file`-non-v2, `/compile-workspace`) are switched off and V2 is confirmed as the sole default. I have **not** verified that no external system/frontend still calls the V1 endpoints — that must be confirmed before deletion.

### Files (candidate for removal once V1 retires)
- `backend/support.js` — entire file (60 KB). Loaded only by V1 templates + V1 build output.
- `backend/templates/*.html` (university, course, specialization, blog) — the 4 DC-tagged templates; superseded by `templates_v2/`.
  - *Caution:* the 3 V1 listing templates (`blog_listing`, `programs_listing`, `specializations_listing`) are **already static** and may be kept or folded into `templates_v2` — recommend keeping until V2 listings are confirmed byte-equivalent.
- `backend/generated/*.html` — legacy debug/test fixtures (`cu_test_output.html`, `specialization_test_*`, `generated/course/*.dc.html`). All load `support.js`; not part of any build.

### Functions/methods (V1-only, in `workspace/builder.py`)
- `_locate_support_js()` (77-88)
- support.js copy block in `build_website()` (565-569)
- `./support.js` rewrite in `_rewrite_html()` (272)
- `build_website()`, `zip_build()`, `_build_root()` — *only* if all routes move to V2.

### In `main.py` (V1 endpoints)
- `get_support_js()` + `/support.js` route (375-387) and the `support.js` branch (370-371).
- V1 build/compile/download endpoints if V2 becomes sole path — **needs frontend confirmation first**.

### In `workspace/compiler.py`
- `_render_page(..., render_mode="v1")` default branch and `compile_workspace()` (V1) — *only* after V1 endpoints are removed.

> **These are candidates, not confirmed dead code.** Several are reachable via still-live V1 endpoints. Full deletion safety requires confirming the frontend's build/preview UI has migrated to the V2 endpoints. I did **not** delete any of them.

---

## 12. Deliverables summary

### 12.1 Files that would be modified (to make V2 the default — *not yet done*)
- `backend/main.py` — flip default build/preview/download to V2; gate V1 behind a flag or remove.
- `backend/workspace/compiler.py` — promote `compile_workspace_v2` to the default; resolve the required-image validation that drops detail pages.
- `backend/workspace/builder.py` — promote `build_website_v2` to default; remove `support.js` packaging.
- (Optional) Resolve hero-variant decision logic (white/purple) in Python so V2 keeps feature parity with V1.

### 12.2 Runtime features removed (when V1 retires)
- React + ReactDOM UMD runtime
- Babel lineage
- Virtual-DOM hydration/render
- DC client-side template compiler (`walkFor`/`walkIf`/`compileTemplate`/`encodeCase`)
- `StreamableLogic`/`DCLogic` reactivity system
- Runtime `innerHTML` content injection

### 12.3 Runtime features retained (already in V2)
- Mobile menu toggle — vanilla `addEventListener` + class toggle (`public-runtime.js`)
- FAQ accordion — vanilla class toggle
- Syllabus tab switching — vanilla `querySelector` show/hide

### 12.4 Builder changes
- `build_website_v2` already packages `public-runtime.js` + external CSS + optimized images and omits `support.js`. Promote it to the sole builder; retire `build_website`/`zip_build` after endpoint migration.

### 12.5 Template changes
- Already complete in `templates_v2/`: all `<x-dc>`, `<sc-for>`, `<sc-if>`, `<helmet>`, `data-dc-script`, and `support.js` removed; native Jinja throughout; external CSS + `public-runtime.js` only.

### 12.6 Validation results (proof)
- `templates_v2/*.html`: 0 DC tags, 0 `support.js`, 55 native Jinja control tags in university alone. ✅
- `workspaces/nmims/build_v2/blog/index.html`: 0 React/support/DC markers. ✅
- V2 ships only `public-runtime.js` (6.5 KB), no React/ReactDOM/Babel. ✅
- ⚠️ V2 detail pages absent from nmims `build_v2/` due to required-image validation failure — **must be resolved before V2 can be the sole default**.

### 12.7 Final target architecture (already implemented in V2)
```
Workspace JSON → Transformer → Renderer (env_v2) → Jinja → FINAL HTML → public-runtime.js (tiny) → Browser
```

---

## 13. Recommended next actions (in order)

1. **Confirm with frontend** whether the build/preview UI already calls V2 endpoints. This determines whether V1 can be removed or must remain temporarily.
2. **Resolve V2 detail-page gap** (§9.2) — fix required-image validation for the target workspaces so `build_v2/` emits detail pages.
3. **Promote V2 to default** in `main.py` (preview/build/download endpoints).
4. **Verify byte-level parity** of V2 listing pages vs V1 listing pages (both are static; confirm equal output).
5. **Preserve hero-variant decision logic** in Python if the purple hero must still be reachable.
6. **Then** remove V1 runtime (`support.js`, 4 DC templates, V1 builder/compiler branches, V1 endpoints) per §11 — guarded by step 1's confirmation.
7. Re-run regression (Step 10) on nmims / nodia / chandigarh-university once detail pages build.

---

*Prepared as an audit/report only. No files were modified or deleted in producing this document.*
