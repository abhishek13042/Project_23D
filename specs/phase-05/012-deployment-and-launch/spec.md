# SPEC 012 — Deployment, CI and Launch

- **Status:** CODE DONE. Launch waits on the owner's accounts, see `docs/operations.md`
- **Phase:** 5 — Public demo
- **Depends on:** SPEC 011, D-009, D-019. SPEC 010 for live upload only

## 1. Purpose

Put the project on the public internet, keep it healthy for $0, and present it well.

## 2. Deliverables

| Item | Content |
|---|---|
| Public GitHub repository | The owner creates it empty and supplies the URL (D-009) |
| `.github/workflows/ci.yml` | pytest, ruff, notebook freshness, web build |
| Vercel project | Deploys `apps/web/` on every push to `main` |
| `.github/workflows/sync-space.yml` | Pushes `apps/space/` to the Space, once SPEC 010 is done |
| `.env.example` | Names of the required settings, with no values |
| `docs/operations.md` | What to check, what to do when a quota runs out |

## 3. Requirements

- `S012-REQ-001`: CI runs on every push and pull request, and does not need the dataset or a GPU.
- `S012-REQ-002`: Secrets live only in each service's secret settings.
- `S012-REQ-003`: A secret scan of the full git history passes before the repository goes public.
- `S012-REQ-004`: No data, weights or scans are in the git history.
- `S012-REQ-005`: A scheduled CI job checks that the site and the gallery files respond, using only allowed CI activity. Its failure is visible in GitHub.
- `S012-REQ-006`: The run statistics stay within Neon's free storage. A documented cleanup covers what happens near the limit.

## 4. Launch checklist

- [x] Results and model card are final and match `reports/` (checked 2026-11-04).
- [x] Limits in `docs/deployment.md` are rechecked and re-dated (2026-11-04, none changed).
- [x] The not-for-clinical-use notice shows on every page, in the site-wide bar under the menu.
- [x] KiTS23, nnU-Net and NiiVue are credited on the About page, with their licenses.
- [ ] README has the live link and a short demo GIF. (GIF done: `docs/media/demo.gif`, 180 KB, no CT images. The live link waits for deployment.)
- [ ] The site is opened from a phone and from a fresh browser with no accounts.
- [x] `/try` shows a useful message when live inference is unavailable. It points to the
  run-it-yourself notebook.

## 5. Acceptance criteria

- [ ] CI passes on `main`.
- [ ] A push to `main` deploys to the public URL.
- [ ] The public URL works for a visitor with no account.
- [ ] Total running cost is $0, and no card is on file with any service.

## 6. Non-goals

- A custom domain. The free `vercel.app` address is enough.
- Uptime guarantees.
