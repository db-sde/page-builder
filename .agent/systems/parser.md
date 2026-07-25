# systems/parser.md — Ingestion & Parsing Subsystem

## Purpose

Convert raw Microsoft Word (`.docx`) files into structured, typed block lists,
then extract those blocks into ACF (Advanced Custom Fields) JSON dictionaries
that match the target page schema.

---

## Responsibilities

1. Read `.docx` files and yield typed content blocks
2. Detect headings, paragraphs, bold text, list items, and tables
3. Map document sections to canonical ACF field names via fuzzy heading matching
4. Process tables: detect merged title rows, recover from bad headers, normalise column counts
5. Merge output from the external microservice (`MICRO_APP_URL`) with local parser output
6. Adapt and normalise field names across different DOCX conventions

---

## Inputs

- A `.docx` file (binary) — either from the Review UI (via `/parse-docx` endpoint) or
  from the CLI (`ingestion/ingest.py`)
- Optional `meta` dict — seed values for `program_name`, `spec_name`, `university_name`

---

## Outputs

- `parse_docx()` → `list[dict]` — typed blocks:
  ```python
  [
    {"type": "h1", "text": "MBA Finance"},
    {"type": "paragraph", "text": "About the program..."},
    {"type": "table", "table_title": "Fee Structure", "headers": [...], "rows": [[...]]},
    {"type": "list_item", "text": "• 2 years duration"},
    ...
  ]
  ```
- `extract_acf(blocks, page_type, meta)` → `dict` — ACF field dict:
  ```python
  {
    "program_name": "MBA Finance",
    "hero_description": "About the program...",
    "fee_plans": [...],
    "syllabus_content": "<table>...</table>",
    ...
  }
  ```
- `merge_micro_and_local(micro, local)` → `dict` — micro wins, local fills gaps
- `adapt_schema(payload, page_type)` → `dict` — normalised field names
- `build_field_state(page_type, values, derived_values)` → `dict` — post-parser ownership
  and completeness metadata; this runs after the Micro/local merge and metadata extraction,
  not inside the parser

---

## Dependencies

- `python-docx` — DOCX reading
- `difflib.get_close_matches` — fuzzy heading matching in `extractor.py`
- `ingestion/extractor.py` uses `HEADING_ANCHORS` dict to map section headings to canonical keys

---

## Important Files

| File | Role |
|---|---|
| `backend/ingestion/parser.py` | DOCX → raw blocks |
| `backend/ingestion/extractor.py` | Blocks → ACF JSON (fuzzy heading anchors) |
| `backend/ingestion/adapter.py` | Schema adapter, micro+local merge |
| `backend/ingestion/ingest.py` | CLI entrypoint for standalone testing |
| `backend/core/field_definitions.py` | Canonical post-parser field ownership contract |

---

## HEADING_ANCHORS

`extractor.py` defines canonical section anchors per page type. Example (course):
```python
"course": {
  "about": ["about", "overview", "program overview", "about the program"],
  "fees": ["fees", "fee structure", "fees and financing", "pricing"],
  "syllabus": ["syllabus", "curriculum", "course structure"],
  ...
}
```

When the parser encounters a heading block, it fuzzy-matches the heading text against
these anchors to decide which section the following blocks belong to.

---

## Known Limitations

- **External microservice dependency:** Complex university/course DOCX files are parsed
  by `MICRO_APP_URL`. If this service is down, parsing falls back to local-only output
  (which may be incomplete for complex documents).
- **Table header detection is heuristic:** Works well for standard DOCX tables but can
  fail on heavily merged or custom-styled tables. Warnings are emitted but not errors.
- **No image extraction from DOCX:** Images embedded in DOCX are ignored. Images must
  be uploaded separately via the Review UI.
- **No footnote or endnote parsing:** These are silently dropped.

---

## Ownership Boundary After Parsing

The Micro App remains the parsing authority. Once its JSON has been adapted and merged,
the API determines page identity and calls `build_field_state()`. The returned metadata
describes `source`, `required`, `optional`, `manual`, `derived`, `missing`, and `value` for
each University/Course/Specialization field. It does not alter parser JSON and is not a
replacement for parsing or schema validation.
