# Required Renderer / Builder Changes

The optimized templates no longer compute page data in a client runtime. The builder must provide all values server-side before rendering.

## Global Context

- `seo_title`
- `meta_description`
- `canonical_url`
- `og_image_url`
- `branding_favicon`
- `branding_logo`
- `university_name`
- `university_letter`
- `university_slug`
- `homepage_href`
- `programs_listing_href`
- `specs_listing_href`
- `blog_listing_href`
- `lead_url_apply`
- `lead_url_enquiry`
- `lead_url_brochure`
- `lead_url_whatsapp`
- `lead_url_fees`
- `lead_url_syllabus`
- `site.email`
- `site.phone`
- `site.whatsapp`
- `site.address`
- `site.copyright`
- `site.topbar_text`

## Former DC Values Now Required Server-Side

- Homepage:
  - `heroWrap`
  - `heroH1`
  - `heroSub`
  - `heroBadge`
  - `heroSecBtn`
  - `heroStatLabel`
  - `heroStatDivider`
  - `heroImg`
  - `heroImgText`
  - `programs`
  - `specs`
  - `features`
  - `admission`
  - `banks`
  - `financing`
  - `recruiters`
  - `testimonials`
  - `faqs`
  - `posts`
- Course detail:
  - `heroWrap`
  - `heroCrumb`
  - `heroH1`
  - `heroSub`
  - `heroBadge`
  - `heroChip`
  - `heroSecBtn`
  - `heroImg`
  - `heroImgText`
  - `stats`
  - `rail`
  - `highlights`
  - `specs`
  - `fees`
  - `admission`
  - `syllabusTabs`
  - `sems`
  - `jobs`
  - `reviews`
  - `faqs`
- Specialization detail:
  - `stats`
  - `rail`
  - `highlights`
  - `fees`
  - `admission`
  - `syllabusTabs`
  - `sems`
  - `otherSpecs`
  - `jobs`
  - `reviews`
  - `faqs`
- Blog detail:
  - `toc`
  - `related`
  - `faqs`
- Listing pages:
  - `programs`
  - `specializations`
  - `blog_posts`

## Data Shape Notes

- FAQ items should include:
  - `q` or rendered question text
  - `a` or rendered answer text
  - `sign`, usually `-` for the first open item and `+` for closed items
  - `disp`, usually `block` for the first open item and `none` for closed items
  - Homepage FAQ items may use `isOpen` to server-render initial display.
- Course and specialization `syllabusTabs` should include:
  - `label`
  - `bg`
  - `color`
  - `border`
- For full interactive syllabus tabs, the builder should emit all year panels with:
  - wrapper: `data-syllabus-tabs`
  - buttons: `data-syllabus-tab`
  - panels: `data-syllabus-panel`
- Values that were previously JS-computed style strings must now be produced by the builder. This keeps branding and white/dark hero variants identical without client rendering.

## Build Output Requirements

- Copy these assets to the public build:
  - `/assets/css/base.css`
  - `/assets/css/university.css`
  - `/assets/css/course.css`
  - `/assets/css/blog.css`
  - `/assets/js/public-runtime.js`
- Do not copy `support.js` into production pages.
- Do not inject framework runtime scripts.
- Render templates to final HTML before publishing.
