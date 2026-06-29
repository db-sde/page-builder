# Verification Checklist

## Completed Checks

- [x] All source templates were analyzed before generating the remaining optimized templates.
- [x] CSS duplication report generated before template generation.
- [x] All optimized templates parse with Jinja.
- [x] No optimized template references `support.js`.
- [x] No optimized template contains custom DC tags or wrappers.
- [x] No optimized template contains `<helmet>`.
- [x] No optimized template contains `<sc-for>` or `<sc-if>`.
- [x] No optimized template contains `onClick="{{ ... }}"`.
- [x] No optimized template contains `style-hover`.
- [x] Each optimized template includes exactly one deferred `/assets/js/public-runtime.js`.
- [x] Shared CSS exists at `/assets/css/base.css`.
- [x] Page-family CSS exists for university, course/specialization, and blog pages.
- [x] Vanilla runtime exists at `/assets/js/public-runtime.js`.

## Visual Parity Checks To Run In Builder

- [ ] Render old and new `university.html` with the same context and compare screenshots at desktop, tablet, and mobile widths.
- [ ] Render old and new `course.html` with the same context and compare screenshots at desktop, tablet, and mobile widths.
- [ ] Render old and new `specialization.html` with the same context and compare screenshots at desktop, tablet, and mobile widths.
- [ ] Render old and new `blog.html` with the same context and compare screenshots at desktop, tablet, and mobile widths.
- [ ] Render listing pages with populated and empty datasets.
- [ ] Open mobile nav and verify links/spacing match prior output.
- [ ] Toggle FAQs and verify answer display behavior.
- [ ] Submit a test lead form only if the page emits `form[data-lead-form]`.
- [ ] Inspect final built HTML and confirm no runtime template placeholders remain except intended static Jinja output during pre-build.

## Dependency Checks To Run On Final Build Output

- [ ] `support.js` is absent.
- [ ] Framework runtime scripts are absent.
- [ ] DC runtime scripts are absent.
- [ ] No `x-dc`, `sc-for`, `sc-if`, or `helmet` tags remain.
- [ ] All page configuration and branding values are visible in server-rendered HTML.
