# systems/editor.md — React Admin Frontend

## Purpose

A 4-step wizard that guides the operator through the full pipeline: select a workspace,
upload a DOCX, review and edit the extracted fields, upload images, preview the compiled
page, then download or compile.

---

## Responsibilities

1. Workspace management (select, create, delete)
2. DOCX upload or raw JSON paste → trigger ingestion via backend API
3. Review and edit all extracted ACF fields
4. Upload images (hero, certificate) — converted to Base64, sent to backend
5. Live preview in iframe via `POST /preview-html`
6. Download standalone HTML or trigger workspace compile + build

---

## Tech Stack

- React 19 + Vite
- Vanilla CSS (`frontend/src/styles.css` — 33 KB)
- Axios for API calls (`frontend/src/api.js`)
- No state management library — `useState` + `session` object in `App.jsx`

---

## Screen Structure

```
App.jsx (session state, step routing)
  │
  ├── Screen0Workspace.jsx    Step 1: Select or create workspace
  ├── Screen1Upload.jsx       Step 2: Upload DOCX or paste JSON
  ├── Screen2Review.jsx       Step 3: Review/edit fields, upload images
  └── Screen3Preview.jsx      Step 4: Preview iframe + compile/build/download
```

### Session Object (`App.jsx`)

```javascript
{
  workspace: { slug, name, is_new },  // selected workspace
  slug: '',                            // page slug
  page_type: '',                       // course / specialization / etc.
  university_slug: '',
  parent_slug: '',
  acf_data: {},                        // extracted + edited ACF field dict
  raw_acf_data: {},                    // original from parser (before edits)
  images: {},                          // { hero_image_url: '/assets/images/...', ... }
  context: null,                       // transformer context dict
  htmlContent: null,                   // preview HTML string
  htmlBlob: null,
  validation_warnings: [],
  table_warnings: [],
}
```

---

## Key Components

### `Screen0Workspace.jsx` (~50 KB)
- Lists all workspaces via `GET /list-workspaces`
- Allows creating new workspaces
- Allows deleting workspaces (with confirmation)
- Shows existing pages in a selected workspace for editing

### `Screen1Upload.jsx` (~15 KB)
- File input for `.docx` upload → `POST /parse-docx`
- Raw JSON paste input → `POST /ingest-acf`
- Sets `session.acf_data`, `page_type`, `slug`, `university_slug`

### `Screen2Review.jsx` (~36 KB)
- Renders all fields from `FIELD_SCHEMA` per page type
- `FieldHealthPanel.jsx` shows required/optional field completeness
- `AddFieldModal.jsx` allows adding missing optional fields
- Parent course selector for specializations (with heuristic pre-fill)
- Image upload slots — encodes to Base64 → `POST /save-page-image`
- Validates before proceeding to Screen 3

### `Screen3Preview.jsx` (~27 KB)
- Posts full `acf_data + images` to `POST /preview-html` → renders in `<iframe>`
- Download standalone HTML button
- "Compile Workspace" button → `POST /compile-workspace`
- "Build Website" button → `POST /build-website`
- Download ZIP button → `GET /download-build`

---

## Field Schema (`fieldSchema.js`)

Defines which fields each page type requires. Used by `Screen2Review.jsx` and
`FieldHealthPanel.jsx` to compute completeness and show impact warnings.

```javascript
export const FIELD_SCHEMA = {
  course: [
    { key: 'program_name', label: 'Program Name', required: true, section: 'Hero', impact: '...' },
    ...
  ],
  specialization: [...],
  university: [...],
  blog: [...],
}
```

---

## API Integration (`api.js`)

All API calls go through `frontend/src/api.js`. Key endpoints used:

| Endpoint | Method | Used In |
|---|---|---|
| `/list-workspaces` | GET | Screen0 |
| `/parse-docx` | POST (multipart) | Screen1 |
| `/ingest-acf` | POST | Screen1 |
| `/preview-html` | POST | Screen3 |
| `/preview-file` | GET | Screen3 iframe src |
| `/save-page` | POST | Screen2 save |
| `/compile-workspace` | POST | Screen3 |
| `/build-website` | POST | Screen3 |
| `/download-build` | GET | Screen3 |
| `/delete-workspace` | DELETE | Screen0 |
| `/delete-page` | DELETE | Screen0 |

---

## Known Limitations

- No loading spinners on form inputs in `Screen2Review` — listed in ROADMAP as pending
- Preview iframe reload can be slow for large templates (full render on each change)
- No real-time build status tracking — the compile/build buttons are fire-and-wait
- Image uploads are Base64 over JSON — not multipart; large images may cause API timeouts
