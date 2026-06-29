# DegreeBaba Production Render Migration Report

## What Changed

- Converted all optimized templates in `change/` to server-rendered Jinja:
  - `university.html`
  - `course.html`
  - `specialization.html`
  - `blog.html`
  - `blog-listing.html`
  - `programs-listing.html`
  - `specializations-listing.html`
- Moved metadata from `<helmet>` into real `<head>` markup:
  - title
  - description
  - canonical
  - favicon
  - OpenGraph title/description/url/image
  - Twitter card
  - Google font preconnect/font stylesheet
- Replaced DC loops and conditionals with Jinja:
  - `<sc-for>` to `{% for %}`
  - `<sc-if>` to `{% if %}`
  - escaped runtime expressions to normal `{{ value }}`
- Replaced production client runtime with `assets/js/public-runtime.js`.
- Extracted duplicated shared CSS into `assets/css/base.css`.
- Added page-family CSS:
  - `assets/css/university.css`
  - `assets/css/course.css`
  - `assets/css/blog.css`
- Kept `assets/css/blog-post.css` as a compatibility alias importing `blog.css`.
- Added `CSS_DUPLICATION_REPORT.md` documenting the CSS architecture before generating the remaining templates.

## What Was Removed

- `support.js` production dependency.
- React and ReactDOM dependency assumptions.
- DC runtime component script blocks.
- `<x-dc>` wrappers.
- `<helmet>` wrappers.
- `<sc-for>` / `<sc-if>` custom tags.
- `onClick="{{ ... }}"` runtime handlers.
- `style-hover` runtime attributes.
- Client-side render value generation from `DCLogic.renderVals()`.

## What Remains

- Pure server-rendered HTML/Jinja templates.
- Shared CSS plus page-family CSS.
- A small vanilla runtime for public interactions only:
  - mobile menu
  - FAQ accordion
  - optional syllabus tabs when builder emits panel markup
  - optional lead form POSTs
  - blog article table wrappers
  - mobile article excerpt toggle
- Some inline styles remain intentionally for dynamic, value-bearing output such as branded colors, dynamic backgrounds, dynamic table rows, one-off section spacing, and CMS-safe rich text containers.

## Required Public Interactions

- Mobile navigation drawer: handled by `#mobile-menu-btn` and `#mobile-drawer`.
- FAQ accordion: handled by `.faq-btn` / `data-faq-answer`.
- Lead forms: supported via `form[data-lead-form]`; link-only CTAs still work without JS.
- Syllabus tabs: supported via `data-syllabus-tabs`, `data-syllabus-tab`, and `data-syllabus-panel` if the renderer emits all panels.
- Blog article table overflow: handled by wrapping `.article-body table`.
- Blog mobile excerpt expansion: handled by `#hero-excerpt`.

## Verification Performed

- Parsed every optimized HTML file with Jinja.
- Checked all optimized templates for removed dependencies and custom tags.
- Verified each optimized template includes exactly one deferred `/assets/js/public-runtime.js`.
- Verified metadata and stylesheet imports are in real `<head>` elements.
