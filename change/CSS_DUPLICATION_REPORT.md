# CSS Duplication Report

Generated before creating the remaining optimized templates. Source directory: `templates/`.

## Summary

| Template | Style block lines | Inline style attributes | Reset/type duplicated | Header/mobile duplicated | Footer duplicated | Card/grid duplicated | Hero duplicated | Rich content duplicated | Read-more duplicated | Sticky bar duplicated |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| blog.html | 250 | 98 | yes | yes | yes | no | yes | yes | no | no |
| blog_listing.html | 54 | 80 | yes | yes | yes | yes | yes | no | no | no |
| course.html | 315 | 195 | yes | yes | yes | yes | yes | yes | yes | yes |
| programs_listing.html | 34 | 82 | yes | yes | yes | yes | no | no | no | no |
| specialization.html | 319 | 186 | yes | yes | yes | yes | yes | yes | yes | yes |
| specializations_listing.html | 34 | 75 | yes | yes | yes | yes | no | no | no | no |
| university.html | 79 | 203 | yes | yes | yes | yes | yes | no | no | no |

## Classification

- `assets/css/base.css`: reset, typography, top bar, navbar/header, mobile drawer, footer, buttons, forms, shared cards/grids, layout utilities, rich-content overflow hardening, FAQ accordion base states, shared hover replacements, sticky bottom bar, shared responsive behavior.
- `assets/css/university.css`: homepage-only hero sizing, homepage stat strip, homepage feature/testimonial/program card tuning, homepage FAQ spacing.
- `assets/css/course.css`: course and specialization detail layout, stats strips, sidebar rail, placement/certificate grids, read-more content tuning, syllabus area, fee/table responsive tuning, sticky enrollment bar.
- `assets/css/blog.css`: blog listing card/details and blog article body typography, TOC, table scroll wrappers, newsletter CTA, mobile excerpt clamp.

## Duplication Removed

- Every source template repeated the base reset, font family, anchor reset, image max-width, and selection color. These now live once in `base.css`.
- Header/mobile-menu rules and footer grid responsiveness were repeated across all page families. These now live in `base.css`; templates keep only semantic markup and active-link/color values.
- Card grid responsiveness was duplicated by listing, homepage, course, and specialization pages. These now use shared `.card-grid-3`, `.card-grid-4`, `.placement-cert-grid`, and responsive rules in `base.css`.
- Rich text overflow hardening appeared independently in course, specialization, and blog article templates. Shared pieces moved to `base.css`; article-specific typography remains in `blog.css`.
- Course and specialization detail templates duplicated most layout/read-more/sticky behavior. The common detail-page rules now live in `course.css`.

## Remaining Intentional Inline Styles

Some inline styles remain because they are value-bearing template output, not duplicated architecture: server-rendered colors, conditional branding, individual one-off section spacing, dynamic backgrounds, dynamic table row colors, and CMS-safe content containers. These should be gradually converted to utility classes only after screenshot parity is established.
