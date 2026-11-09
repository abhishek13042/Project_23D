# apps/web: the demo website

A Next.js site that shows the test-set results, a gallery of sample cases in a 3D viewer, and a
page for running the model on your own scan. It is a research demo, not a medical tool.

## Run it locally

```bash
cd apps/web
npm install
npm run dev
```

All settings are optional; copy `.env.example` to `.env.local` to set them. Without them the site
still runs and says what is missing.

| Command | What it does |
|---|---|
| `npm run data` | Turn the files in `reports/` into `src/data/results.json` (runs before dev, build and test) |
| `npm run dev` | Start the site at http://localhost:3000 |
| `npm test` | Run the Vitest tests |
| `npm run typecheck` | Check the TypeScript types |
| `npm run build` | Make the production build |

## Layout

| Path | What it holds |
|---|---|
| `src/app/` | One folder per page (`/`, `/results`, `/gallery`, `/case/[id]`, `/try`, `/about`) and the API routes in `api/` |
| `src/components/` | The page parts: the score map, the CT viewer, the upload form, the page header and navigation |
| `src/lib/` | Logic shared by pages and API routes: results data, input checks, API handlers, the Space client |
| `src/db/` | The database schema (Postgres on Neon) and its client |
| `scripts/generate-data.mjs` | Builds the site's data from the report files; a missing report stops the build |

Every number on the site comes from `reports/`, never typed in by hand. Deployment is described in
[docs/deployment.md](../../docs/deployment.md) and [docs/operations.md](../../docs/operations.md).
