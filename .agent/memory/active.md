# memory/active.md — Current Work

Last updated: 2026-07-24

---

## What Is Being Worked On?

Based on the repository state (both `uv run main.py` and `npm run dev` are running),
the team is in an active development session. The specific feature being worked on
is **not determinable from the repository alone** at the time of this `.agent/` creation.

---

## Why?

Not enough evidence from the repository.

---

## What Remains?

From open TODOs in the codebase and ROADMAP.md:

1. **Responsive CSS refinement** — minor issues on intermediate screen widths (768–1024px)
2. **Contact app polish** — loading states, better validation UX
3. **Caching** — `render_resolved()` in `engine.py` has a `TODO` for Redis caching
4. **AI gap-fill** — `BaseTransformer` has a `TODO` for calling Groq on missing required fields
5. **Tests** — parser, extractor, adapter, compiler all lack unit tests

---

## Maintenance Note

> After every coding session, update this file with:
> - What was changed
> - What was left incomplete
> - What the next step is
>
> Move completed items to `memory/history.md`.
