# SPEC 013: Frontend design

- **Status:** Done. The owner can still ask for changes to the direction
- **Phase:** 5
- **Depends on:** SPEC 011 (website), SPEC 004 (per-scan scores)

## 1. Goal

Give the public website one recognisable identity that shows the real test result in the first
viewport, keeps the failures easy to find, and stays honest about what the numbers mean.

The look and tokens are recorded in [DESIGN.md](../../../DESIGN.md). This spec says what must be
true, so it can be checked.

## 2. Idea

Segmentation is outlining, and a contour line is an outline. The site is a survey sheet of the 73
test scans. Each scan is a spot height whose height is its mean Dice. Failures stay on the map as
pits.

## 3. Pages

| Page | Mode | What it does |
|---|---|---|
| `/` | Experience | Score terrain, key and live reading, then scores, best and worst, one open scan |
| `/gallery` | Operate | Sheet index map above the groups of scans, worst group first |
| `/case/[id]` | Experience | Viewer first, then scores, volumes and a locator map |
| `/results` | Read | Tables with the scale bar, and where each number comes from |
| `/try` | Operate | Rules first, then the agreement, the drop zone and the result |
| `/about` | Read | Method, limits, privacy, credits |
| Header and footer | Shared | Sheet header with the disclaimer, and a title block with the credits |

## 4. The score terrain

- Horizontal axis: tumor volume in mL, log scale, from the expert's outline.
- Vertical axis: kidney volume in mL, log scale, from the expert's outline.
- Each of the 73 dots is a real scan. Height is its post-processed mean Dice.
- The surface is a Gaussian kernel average of those heights. It is drawn only inside the limit of
  survey, the area close enough to real scans.
- It is computed at build time from `reports/evaluation/spec004/eval_pp/per_case.csv`.
- It holds scores and volumes only: no patient pixels and no mask geometry.

## 5. Requirements

- **S013-REQ-001:** The first viewport of `/` shows the real test result, not an illustration.
- **S013-REQ-002:** Every height on the terrain comes from the generated data (S011-REQ-006).
- **S013-REQ-003:** The terrain says it is smoothed, and a table lists all 73 scans.
- **S013-REQ-004:** The lowest scans are labelled in the first viewport (S011-REQ-007).
- **S013-REQ-005:** State is shown by a mark as well as a color: best, worst, gallery and other.
- **S013-REQ-006:** The one 0 to 1 scale bar is used for every score ruler on the site.
- **S013-REQ-007:** Kidney, tumor and cyst keep the same colors in the viewer and every legend.
- **S013-REQ-008:** The disclaimer is on every page, and the viewer repeats it (S011-REQ-004).
- **S013-REQ-009:** On `/try` the warning comes before the agreement and the file field
  (S011-REQ-005).
- **S013-REQ-010:** All behaviour from SPEC 011 is unchanged: routes, API calls, viewer, upload.
- **S013-REQ-011:** Every page works at 390 px wide with no sideways page scroll.
- **S013-REQ-012:** Text meets WCAG AA contrast, and every control shows keyboard focus.
- **S013-REQ-013:** The contour animation runs once and is off under reduced motion.
- **S013-REQ-014:** No claim is added that is not already in the reports.

## 6. Out of scope

Backend, database, API, deployment, and new measurements. Nothing here changes a score.

## 7. Acceptance

- [x] The terrain renders from `results.json`, with 73 spots, at desktop and phone width. Review
  captures are in `.impeccable/review/`.
- [x] All six pages were looked at in a browser at desktop and 390 px. Two fixes came from this:
  a case label that covered another spot, and gallery links that wrapped on phones.
- [x] `impeccable detect` was run on each page and every finding was fixed or explained. The live
  scan timed out on four pages, so those were scanned as built HTML with the CSS inlined. What is
  left are false positives: padding on full-width bands (it sits on the inner frame), text color on
  SVG links, and the edge ticks of the map, which are kept on purpose.
- [x] `tsc`, `vitest` (29 tests) and `next build` pass. Python: 166 tests and ruff pass.
- [x] `DESIGN.md` and `.impeccable/design.json` describe the built site. Recorded as D-022.
