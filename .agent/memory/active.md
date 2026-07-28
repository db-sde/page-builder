# memory/active.md — Current Work

Last updated: 2026-07-27

---

## What Is Being Worked On?

**Template regression restoration complete (2026-07-27).** The original V2 presentation from
`3970dc3e56348abf0fb5f82cd39de0ea19c802e1` is again the structural baseline for University,
Course, and Specialization pages. Phase 3 data guards and fabricated-content removal remain.
No CSS, parser, transformer, renderer, schema, compiler, builder, or editor code changed.

The schema-driven content pipeline — Phase 3 complete (2026-07-24) — remains the
editing workflow described in [systems/schema-pipeline.md](../systems/schema-pipeline.md):

```
Upload DOCX -> parse -> detect page type -> load blueprint -> auto-populate
  -> Editing State -> operator fills only manual fields + images -> preview -> publish
```

Four layers: **Field Definitions** (schema) -> **Page Requirements** (templates) ->
**Page Blueprint** (build contract) -> **Editing State** (what is left to do).

Phase 3 also removed every fabricated fallback from the renderer, transformers and templates
(REG-010) and the workspace-slug email leak (REG-011). Preview and production share one
renderer; the only difference is placeholder indicators.

---

## Why?

So the editor opens on an almost-complete page and the operator only completes what the
system genuinely cannot know — while the output stays 100% data-driven.

---

## Current boundary

- Ownership `core/field_definitions.py`; template requirements `core/page_requirements.py`;
  build contract `core/page_blueprint.py`; editor payload `core/editing_state.py`
- Parser JSON unchanged; unused schema fields preserved, reported, never warned about
- `field_state` / `page_state` / `editing_state` are API/editor metadata, not `source.json`
- Auto-population fills only explicitly declared defaults (currently `mode`) — never content
- Compiler, builder, workspace layout, routing, SEO, publishing and storage format unchanged

## Known impact to watch

University pages are shorter where sections had no real data: `features`, `recruiters`,
`banks`, `financing` come only from `university_knowledge.json` `shared_lists`, empty in both
current workspaces. `facts` and `accreditations` are parsed and populated but `university.html`
still does not render them — a pre-existing template gap; adding sections is product work.

---

## What Remains?

**Product decisions (blocked on a human, not on code):**
1. Should `university.html` render the already-parsed `facts` and `accreditations`?
   The data exists and the transformer builds it; the template has no such sections.
   Phase 3 deliberately did not add sections automatically.
2. Should section titles come from the `*_heading` schema fields instead of hardcoded text?
3. Populate `university_knowledge.json` `shared_lists` (features / recruiters / banks /
   financing) for each workspace, or accept those university sections staying hidden.

**Follow-ups:**
4. Drive the editor's field list and image slots from `GET /page-blueprint` so
   `frontend/src/fieldSchema.js` stops duplicating the backend schema.
5. Expose repeaters (highlights, faqs, reviews, job_profiles, fee_plans) in the editor —
   they are still not editable anywhere.
6. Parameterise GA via `metadata.json["ga_id"]` (still hardcoded to `nmims-2` in `builder.py`).

**Pre-existing TODOs / ROADMAP:**
7. Responsive CSS refinement (768–1024px)
8. Contact app polish (loading states, validation UX)
9. Redis caching TODO in `engine.py`; AI gap-fill TODO in `base.py`
10. Tests — parser, extractor, adapter, compiler still lack focused unit tests

---

## Maintenance Note

> After every coding session, update this file with:
> - What was changed
> - What was left incomplete
> - What the next step is
>
> Move completed items to `memory/history.md`.
