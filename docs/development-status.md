# Development Status

## Current status

- **SPEC 001 — Foundation & Feasibility:** verified locally; dataset availability
  re-checked 2026-10-21
- **SPEC 002 — Volume Data Pipeline:** implemented and tested locally (25 tests,
  real-data smoke run on 5 cases); Kaggle CPU run pending
  (`notebooks/01_prepare_data.ipynb`)
- **SPEC 003 — Training:** not started (notebook not written yet)
- **SPEC 004 — Evaluation:** implemented and tested locally (official evaluator
  wrapper, secondary metrics, bootstrap CIs, validation-only post-processing);
  real-data smoke run on 5 cases; Kaggle GPU run pending
  (`notebooks/03_evaluate.ipynb`, needs the SPEC 003 model)
- **SPEC 005 — Case analysis (E-005):** implemented and tested locally; runs in the
  same notebook
- **API/frontend/deployment:** not started

## Completed foundation decisions

- project task: renal 3D semantic segmentation
- modality: contrast-enhanced CT
- primary dataset: KiTS23 v0.1.4
- classes: background, kidney, tumor, cyst
- independence unit: anonymized case ID
- split policy: subject/case-level, fixed seed 42, 70/15/15; stratified by cohort
  proxy, tumor-size bin and cyst presence (D-010, D-012)
- primary evaluation: per-case macro Dice and surface Dice across KiTS HECs,
  official evaluator
- model strategy: official nnU-Net v2 only, fold 0, 100 epochs (D-012)
- local/Kaggle division of work
- reproducibility and Git hygiene policy
- full dataset staged on Kaggle only, from pinned and checksummed URLs (D-011)
- foundation approach review completed: `reports/foundation/approach_review.md`
  (its four decisions approved in lean form as D-012)
- scope cut to one nnU-Net v2 run (fold 0, 100 epochs, about 15 GPU-hours) (D-012)

## Explicitly not started

- full-dataset run on Kaggle (SPEC 002 notebook ready)
- model implementation
- training
- deployment

## Operational note

The local Git repository is initialized on `main`, but no remote URL is configured.
The final remote synchronization requirement cannot be completed until the intended
remote URL is supplied and Git credentials/tooling are available.
