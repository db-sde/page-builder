# tasks/current.md — Current Sprint

Last updated: 2026-07-24

---

## 🔴 High Priority

- [ ] **Fix `primary_domain` for sitemap/canonical URLs**
  The sitemap and canonical `<link>` tags may point to the wrong domain if
  `metadata.json["primary_domain"]` is absent. Fallback to `LEAD_BASE_URL` is incorrect.
  Fix: read `primary_domain` from `metadata.json` explicitly; fail clearly if missing.

- [ ] **Add unit tests for ingestion pipeline**
  `parser.py`, `extractor.py`, `adapter.py` have zero test coverage.
  Regressions here are only caught manually through the Review UI.

---

## 🟡 Medium Priority

- [ ] **Responsive CSS refinement (768–1024px)**
  Minor layout issues exist on intermediate screen widths.
  The grid/card layouts need testing and CSS fixes in this range.

- [ ] **Contact app loading states**
  Form inputs in `contact/src/App.jsx` have no loading indicator during submission.
  Add spinner/disabled state to the submit button while the webhook call is in flight.

- [ ] **Generalise GA tag injection**
  `builder.py`'s `_finalize_html()` hardcodes the GA ID for `nmims-2`.
  Move GA ID to `metadata.json["ga_id"]` and apply it for any workspace that has this key.

---

## 🔵 Blocked

- None currently identified.

---

## ✅ Completed Today

- Created `.agent/` project memory system (2026-07-24)
