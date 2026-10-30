# Project status

Last updated: 2026-10-30.

## Where the project is

| Spec | Stage | State |
|---|---|---|
| 001 | Foundation | Done. The GitHub remote is still missing (SPEC 012) |
| 002 | Data pipeline | Done. 414 of 414 train and validation cases preprocessed on Kaggle |
| 003 | Training | Done. 100 epochs, all 73 validation cases scored |
| 004 | Evaluation | Code ready and tested. Kaggle run started 2026-10-30 |
| 005 | Case analysis | Code ready and tested. Runs in the same notebook as 004 |
| 006 | Inference | Merged into 007, then replaced by phase 5 |
| 007 | Report and reproducibility | Code ready. Report fills in after 004 |
| 008–012 | Public demo | Drafted, see [phase 5](../specs/phase-05/README.md) |

## Training result

Source: `reports/training/spec003_session1_run_record.json` and
`spec003_session2_run_record.json`.

- 100 epochs took about 5.9 hours on a T4, at about 209 s per epoch. Final validation of all 73
  cases finished in session 2, 12.88 GPU hours in total.
- Validation, scored with the official evaluator:

| Predictions | Kidney + masses | Masses | Tumor | Mean Dice |
|---|---|---|---|---|
| Raw model output | 0.855 | 0.544 | 0.514 | 0.638 |
| After post-processing (D-021) | 0.937 | 0.694 | 0.650 | 0.760 |

- The raw score is low because the model marks false regions far from the kidneys. Pseudo Dice
  (0.874 at the end) hid this. It was still rising at epoch 100, so longer training should help.
- The post-processing row was measured once in a separate script and chosen on these same cases, so it may
  run slightly high. `kits23-evaluate` re-scores it with the final code.

## What comes next

1. `kits23-evaluate` predicts the 73 test cases, about 7–8 hours on the GPU.
2. `scripts/report/build_report.py` writes the real results.
3. Phase 5 starts with SPEC 008.

## What the owner needs to do

See [deployment.md](deployment.md#what-only-the-owner-can-do). The Hugging Face account is the
urgent one, because live upload can't start until the account is 30 days old.

## Decisions in force

- Task: 3D semantic segmentation of kidney, tumor and cyst in contrast-enhanced CT.
- Data: KiTS23 v0.1.4, 489 labeled cases. Split at case level, 343/73/73, seed 42, stratified by
  cohort proxy, tumor size and cyst presence (D-010, D-012).
- Model: official nnU-Net v2 2.8.1, `3d_fullres`, fold 0, 100 epochs (D-012, D-016).
- Primary result: per-case Dice and surface Dice over the KiTS regions, official evaluator,
  bootstrap 95% CIs (D-014).
- Product: a public research demo at $0 (D-018, D-019).

All decisions are in [decisions.md](decisions.md).
