# SPEC 007 — Report and Reproducibility (includes SPEC 006)

- **Status:** DONE — see reports/evaluation/results.md (2026-10-31)
- **Phase:** 4 — Release
- **Project:** Project_23D — Renal CT 3D Segmentation
- **Date:** 2026-10-24
- **Depends on:** SPEC 002–005, D-012, D-014

## 1. Purpose

Turn the saved run records into one honest results report. Anyone should be able
to rerun the work from the written steps alone. Under D-012, SPEC 006 (inference
and productization) is merged into this spec. Inference is the SPEC 004 notebook.
This spec covers no app, API or demo; D-018 moved those to [phase 5](../../phase-05/README.md).

## 2. Deliverables

| File | Content |
|---|---|
| `scripts/report/build_report.py` | Builds `reports/evaluation/results.md` from the run records only |
| `reports/evaluation/results.md` | Setup, headline result with CIs, per-region table, integrity checks, link to the case analysis (generated) |
| `docs/reproduce.md` | Step-by-step Kaggle and local instructions, and what counts as a reproduction |
| `reports/release/model_card.md` | What the model is, intended use, how it was evaluated, limitations |

## 3. Requirements

- `S007-REQ-001`: Every number in the report is read from a saved record. Missing records appear as *pending*, never as estimates.
- `S007-REQ-002`: The headline gives n, the mean and the 95% CI for both co-primary metrics, for both post-processed and raw predictions.
- `S007-REQ-003`: Results made without the official evaluator are labeled "Not valid".
- `S007-REQ-004`: The report compares the split fingerprints of SPEC 002 and SPEC 004, and flags a mismatch.
- `S007-REQ-005`: The report says the internal test split is not comparable to the KiTS23 leaderboard.
- `S007-REQ-006`: The model card says the model is not for clinical use, and states the data license.
- `S007-REQ-007`: `docs/reproduce.md` lists every notebook, its inputs and settings, and what to copy back.

## 4. Tests

`tests/report/test_build_report.py`:

- with no records, everything is *pending* and no numbers appear;
- with full fake records, the numbers match `summary.json`, the fingerprint matches and the analysis link is correct;
- a fingerprint mismatch and an invalid primary result are both flagged.

## 5. Acceptance criteria

- After the Kaggle runs, `build_report.py` reports 0 pending items, except training details if SPEC 003 has no record.
- The integrity checks pass.
- A reader can follow `docs/reproduce.md` without asking questions.

## 6. Non-goals

- A web demo, API or model hosting. These are in [phase 5](../../phase-05/README.md) (D-018).
- Publishing the weights, which SPEC 008 does. The data license is non-commercial and share-alike, so any release must say so.
