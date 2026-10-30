# SPEC 005 — Case Analysis (E-005)

- **Status:** DONE — see reports/evaluation/results.md (2026-10-31)
- **Phase:** 3 — Evaluation
- **Project:** Project_23D — Renal CT 3D Segmentation
- **Date:** 2026-10-24
- **Depends on:** SPEC 002 (`case_features.csv`), SPEC 004 (`per_case.csv`), D-012

## 1. Purpose

Under D-012 there is one model, so this spec has no training ablations. It answers
the question *where does the model fail?* using only the test-set results and the
case features. It needs no GPU.

## 2. Analyses

| Factor | Groups | Why |
|---|---|---|
| `size_bin` | none, small, medium, large (SPEC 002 tertiles) | Small tumors are the known hard case |
| `has_cyst` | yes / no | Cysts are the easiest label to confuse with tumors |
| `cohort` | kits21 / kits23_new | A proxy for the change in data source (D-010) |
| foreground-volume quartile | Q1–Q4 of kidney + tumor + cyst ml | Checks whether patient or kidney size matters |

For each group the analysis reports n, the mean and median, and a bootstrap 95% CI for:

- mean Dice;
- mean surface Dice;
- each HEC Dice.

It also reports:

- the Spearman correlation between tumor volume and tumor Dice on tumor cases, with a bootstrap CI;
- false positives: cases without a tumor where some tumor was predicted;
- the 10 worst cases with their features;
- figures:
  - a box plot of tumor Dice by size bin;
  - a box plot of mean Dice by cohort;
  - axial, coronal and sagittal overlays of the best, median and worst cases.

## 3. Rules

- Descriptive only. The groups are small, so no p-values or significance claims are made (docs/evaluation.md).
- Groups and factors are fixed here, before the test results exist.
- HEC Dice uses the official evaluator's values when they are present.

## 4. Code

| File | Role |
|---|---|
| `src/project3d/eval/analysis.py` | Join, group tables, Spearman CI, worst cases, Markdown |
| `src/project3d/eval/figures.py` | Overlays (CT window -160 to 240 HU) and box plots |
| `scripts/eval/case_analysis.py` | CLI: writes `analysis.json`, `analysis.md`, `figures/` |

## 5. Requirements

- `S005-REQ-001`: Every test case in `per_case.csv` is matched to its SPEC 002 features. A missing feature row stops the run.
- `S005-REQ-002`: Group tables list n for every group. CIs are computed only for groups of 10 or more cases.
- `S005-REQ-003`: The best, median and worst examples are chosen by a fixed rule: mean Dice, ties broken by case ID.
- `S005-REQ-004`: Overlays show the reference and the prediction on the same slices, through the largest mass (or kidney) cross-section.

## 6. Tests and verification

- `tests/eval/test_analysis.py`:
  - end-to-end on fake cases (tables, group order, 5 figures, Markdown);
  - quartiles and example choice;
  - Spearman and its CI.
- Real-data smoke run (2026-10-24, 5 cases):
  - all 5 figures written;
  - overlay orientation checked by eye (the spine is at the bottom of the axial view).

## 7. Acceptance criteria

- `analysis.md` and the figures are produced by the Kaggle run, and copied to `reports/error-analysis/`.
- The write-up states the group sizes next to every number.
