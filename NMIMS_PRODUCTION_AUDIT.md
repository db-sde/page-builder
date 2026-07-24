# NMIMS Production Hardening & SEO Verification

Audit date: 24 July 2026 (Asia/Kolkata)  
Production site: `https://www.nmimsonline.co/`  
Workspace: `backend/workspaces/nmims-2`

## Verdict

**NOT PRODUCTION READY yet.**

The canonical, sitemap, robots, metadata, internal-link, and structured-data paths pass. The current production deployment still fails the historical redirect requirement:

- all tested `nmims-2-*` routes return `404` instead of a permanent redirect;
- both obsolete fee-article routes return `404` instead of a permanent redirect;
- `http://nmimsonline.co/...` uses two redirects instead of one.

The static builder now generates the missing permanent redirects. That fix is present in the new local NMIMS export but is not live until the `build/` output is redeployed. The apex HTTP chain is domain-level Vercel configuration and cannot be collapsed by a path-only static export rule.

## Architecture and root cause

DegreeBaba is a static generator, not Next.js. Its relevant flow is:

`source.json -> transformer -> renderer -> compiler -> workspace HTML -> static builder -> build/`

Public URL generation is already centralized in:

- `backend/core/utils.py::build_public_route`
- `backend/core/utils.py::build_public_url`

The renderer uses those helpers for canonicals, Open Graph URLs, breadcrumbs, and structured data. The builder uses them for routes and sitemap entries.

The redirect failure occurred after that URL normalization step. `backend/workspace/builder.py` exported pages, `routes.json`, `sitemap.xml`, and `robots.txt`, but did not export any deployment redirect rules. Raw internal slugs such as `nmims-2-nmims-online-mba` were correctly normalized to clean public routes, while requests for the former raw routes simply reached Vercel as missing files and returned `404`.

## Changes implemented

### Platform

`backend/workspace/builder.py`

- Generates `build/vercel.json` on every website build.
- Sets `trailingSlash: false`, matching the shared URL policy.
- Automatically creates permanent redirects whenever a raw workspace page slug is normalized to a different public route.
- Reads optional historical redirects from workspace metadata instead of hardcoding university-specific paths into the platform.
- Emits deterministic, de-duplicated redirect rules.

Vercel documents that a redirect with `permanent: true` uses HTTP `308`: <https://vercel.com/docs/project-configuration/vercel-json#redirects>

### NMIMS workspace only

`backend/workspaces/nmims-2/metadata.json`

- Adds redirects from both obsolete 2025 fee article routes to `/blog/nmims-online-mba-fees`.
- Keeps `https://www.nmimsonline.co` as the primary domain.

The workspace directory is intentionally ignored by Git in this repository. The local workspace and generated deployment package contain this configuration; any separate workspace persistence/deployment process must preserve it.

## Ordered production verification

### 1. Redirects

| Input | Effective URL | Hops | Result |
|---|---|---:|---|
| `http://nmimsonline.co/specializations` | `https://www.nmimsonline.co/specializations` | 2 | **FAIL** — expected 1 |
| `http://www.nmimsonline.co/specializations` | `https://www.nmimsonline.co/specializations` | 1 | PASS |
| `https://nmimsonline.co/specializations` | `https://www.nmimsonline.co/specializations` | 1 | PASS |
| `https://nmimsonline.co/specializations/` | `https://www.nmimsonline.co/specializations` | 2 | PASS — allowed for this input |

The failing first chain is:

1. `http://nmimsonline.co/specializations` -> `https://nmimsonline.co/specializations`
2. `https://nmimsonline.co/specializations` -> `https://www.nmimsonline.co/specializations`

The Vercel project/domain configuration must redirect the apex domain directly to the canonical `https://www` host where possible.

### 2. Canonical tags

Live checks pass:

| Template | URL | Canonical matches | Canonical response |
|---|---|---|---|
| Homepage | `/` | `https://www.nmimsonline.co/` | `200`, 0 redirects |
| Listing | `/specializations` | exact absolute URL, no slash | `200`, 0 redirects |
| Programme | `/nmims-online-mba` | exact absolute URL, no slash | `200`, 0 redirects |
| Blog | `/blog/nmims-online-mba-fees` | exact absolute URL, no slash | `200`, 0 redirects |

Each page has exactly one canonical tag.

### 3. Sitemap

Live sitemap checks pass:

- Total URLs: **25**
- URLs beginning with `https://www.`: **25**
- Trailing-slash URLs: homepage only
- Sitemap URLs returning `200` with 0 redirects: **25/25**
- Legacy `nmims-2-*` or obsolete fee URLs present: **0**

### 4. Historical `nmims-2-*` routes

Current production result: **FAIL**.

All nine checklist routes tested return `404` with no redirect. The same issue applies to other raw `nmims-2-*` workspace slugs.

The rebuilt export now contains **20 permanent redirects**:

- 18 automatically derived workspace-prefix redirects;
- 2 NMIMS-specific fee-article redirects.

All 20 destinations exist in `routes.json`; no redirect source appears in `sitemap.xml`.

### 5. Google Search Console

**BLOCKED — authentication required.** The available browser session is signed out of Search Console.

After deployment, verify:

- sitemap status is `Success` and discovered pages are approximately 25;
- user-declared and Google-selected canonicals match for homepage, programme, specialization, and blog samples;
- the eight previously non-indexable pages are indexable;
- `Duplicate, Google chose different canonical` trends downward;
- `Alternate page with proper canonical tag` contains only intentional alternates.

### 6. Ahrefs

**BLOCKED — authentication required.** The available browser session is signed out of Ahrefs.

After deployment, crawl from `https://www.nmimsonline.co/` and confirm these issues fall to zero or near zero:

- canonical points to redirect;
- 3XX redirect in sitemap;
- page has links to redirect.

### 7. Structured data

Google's live Rich Results Test passed one page from every generated HTML template:

| Template | Sample | Result |
|---|---|---|
| University | `/` | 1 valid Breadcrumb item |
| Course | `/nmims-online-mba` | valid Breadcrumb + Course items |
| Specialization | `/nmims-online-mba-in-financial-management` | valid Breadcrumb + Course items |
| Blog | `/blog/nmims-online-mba-fees` | 1 valid Breadcrumb item |
| Program listing | `/programs` | 1 valid Breadcrumb item |
| Specialization listing | `/specializations` | 1 valid Breadcrumb item |
| Blog listing | `/blog` | 1 valid Breadcrumb item |

No test displayed an error or warning.

The full generated-site JSON-LD audit also parses successfully:

- `Organization`: 1 page
- `BreadcrumbList`: 25 pages
- `Course`: 18 course/specialization pages
- `FAQPage`: 21 pages with FAQ data

## Additional verification

### Robots

Live `robots.txt` passes:

```text
User-agent: *
Allow: /

Sitemap: https://www.nmimsonline.co/sitemap.xml
```

### Internal links

Across all 25 live sitemap pages:

- unique internal page targets: 25;
- targets returning `200`: 25;
- targets redirecting: 0;
- trailing-slash internal links: 0.

The new local build also contains no broken links, no links to redirect sources, and no missing local images.

### Metadata and headings

Across all 25 live and locally rebuilt pages:

- non-empty title: 25/25;
- one non-empty meta description: 25/25;
- canonical/`og:url` consistency: 25/25;
- complete Open Graph and Twitter image/title/description fields: 25/25;
- exactly one H1: 25/25;
- description length range: 140–160 characters.

Two listing titles are only 21 characters (`NMIMS Online Programs` and `NMIMS Specializations`). They are accurate and not a production blocker, but can be expanded later if search-query data supports a better title.

### Fee article consolidation

- One current fee article source exists: `/blog/nmims-online-mba-fees`.
- Internal homepage/listing links point to that clean URL.
- Neither obsolete fee URL appears in the sitemap.
- Both obsolete routes are included in the new permanent redirect manifest.

### Build regression

NMIMS was compiled and exported from current sources after the change:

```text
Compiler: 25 pages compiled, 0 failed
Builder:  25 pages compiled, 0 failed
Routes:   25
Images:   29
Redirects: 20 permanent, 0 missing destinations
```

A generic non-NMIMS workspace test confirms that ordinary slugs do not create false redirects; it receives an empty redirect list plus the shared trailing-slash policy.

### Performance

**BLOCKED — the required Chrome DevTools performance trace integration is not configured in this environment.** No Core Web Vitals or Lighthouse score is claimed. Configure the Chrome DevTools MCP/performance tooling, then run mobile and desktop traces for homepage, programme, specialization, and blog samples.

## Deployment and final recheck

Deploy the contents of:

`backend/workspaces/nmims-2/build/`

The deployment root must contain `vercel.json`; deploying a parent directory without setting `build/` as the Vercel project root will not apply the redirects.

Immediately after deployment:

1. Rerun the four redirect commands.
2. Confirm representative `nmims-2-*` routes return one `308` to clean destinations.
3. Confirm both obsolete fee routes return one `308` to `/blog/nmims-online-mba-fees`.
4. Re-run the sitemap `200 0` loop.
5. Fix/verify the apex HTTP domain redirect in Vercel.
6. Complete the authenticated Search Console and Ahrefs checks.

Production can be marked ready only after the deployed redirect checks pass and the apex HTTP chain is resolved or explicitly accepted.
