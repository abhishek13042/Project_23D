# SPEC 011 — Web App and Database

- **Status:** CODE DONE. Waiting on the Neon and Vercel accounts
- **Phase:** 5 — Public demo
- **Depends on:** SPEC 009, D-018, D-019. SPEC 010 for live upload only

## 1. Purpose

Build the public website: the first thing a recruiter or reader sees. It explains the project,
shows the results honestly, and lets visitors explore real 3D segmentations.

## 2. Pages

| Page | Content |
|---|---|
| `/` | What it does, a live 3D example, headline results |
| `/gallery` | All sample cases with scores and group |
| `/case/[id]` | 3D viewer: CT, prediction and ground truth, with toggles and region volumes |
| `/results` | Results with confidence intervals, what worked, what failed |
| `/about` | Method, model card, data credit, limitations |
| `/try` | Upload a scan, or the fallback link if live inference is unavailable |

## 3. Deliverables

| File | Content |
|---|---|
| `apps/web/` | Next.js app in TypeScript, with NiiVue |
| `apps/web/src/db/schema.ts` | Database schema |
| `apps/web/src/data/results.json` | Metrics generated from `reports/` at build time |

## 4. Database

Neon Postgres, reached only from Next.js route handlers.

```text
inference_run
  id, created_at, status, duration_seconds, voxel_count,
  kidney_ml, tumor_ml, cyst_ml, app_version

feedback
  id, created_at, run_id (optional), rating, comment
```

The `/try` page writes one `inference_run` after a run. Statistics are shown on `/results`.

## 5. Requirements

- `S011-REQ-001`: Gallery and results pages work with the database and the Space both down.
- `S011-REQ-002`: Scans never pass through a Vercel function. The browser calls the Space directly.
- `S011-REQ-003`: The database stores no images, file names or IP addresses.
- `S011-REQ-004`: Every page that shows a result says "Research demo, not for clinical use".
- `S011-REQ-005`: `/try` warns against uploading identifiable data, before any file is chosen.
- `S011-REQ-006`: Metrics come from generated data, never from values typed into components.
- `S011-REQ-007`: The worst cases are as easy to find as the best ones.
- `S011-REQ-008`: Pages work on a phone. The viewer shows a clear message if WebGL2 is missing.
- `S011-REQ-009`: Database write routes validate input and limit its size.
- `S011-REQ-010`: The site credits KiTS23 and nnU-Net, and states the license of the data and weights.

## 6. Tests

- Route handlers: valid input, invalid input and database failure.
- Build fails if generated results are missing.
- End-to-end: a gallery case opens and the viewer loads in a browser.

## 7. Acceptance criteria

- [x] `next build` passes.
- [x] All pages work on desktop and phone width.
- [x] A gallery case loads with the database disconnected.
- [x] Lighthouse performance on `/` is at least 80. It measured 92 locally, with accessibility 100.

## 8. Non-goals

- User accounts and saved history.
- Payments or ads, which the Vercel plan and data license both rule out.
