# Project status

Last updated: 2026-11-01.

## Where the project is

| Spec | Stage | State |
|---|---|---|
| 001 | Foundation | Done. The GitHub remote is still missing (SPEC 012) |
| 002 | Data pipeline | Done. 414 of 414 train and validation cases preprocessed on Kaggle |
| 003 | Training | Done. 100 epochs, all 73 validation cases scored |
| 004 | Evaluation | Done. Test mean Dice 0.722 |
| 005 | Case analysis | Done. See `reports/evaluation/spec004/analysis/` |
| 006 | Inference | Merged into 007, then replaced by phase 5 |
| 007 | Report and reproducibility | Done. See `reports/evaluation/results.md` |
| 008 | Model release | Done. Benchmark recorded. The upload to Hugging Face waits on the owner |
| 009 | Demo gallery | Done. 10 cases built. The upload to Hugging Face waits on the owner |
| 010 | Inference service | Code done. ZeroGPU test blocked by the Hugging Face account's age |
| 011 | Website and database | Code done. Runs locally. Needs Vercel and Neon |
| 012 | Deployment and CI | Code done. Needs the GitHub repository, then [operations.md](operations.md) |

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
- The post-processing row was chosen on these same cases, so it runs slightly high.

## Test result

Scored once on the 73 test cases (`reports/evaluation/results.md`), 6.22 GPU hours.

| Predictions | Kidney + masses | Masses | Tumor | Mean Dice (95% CI) | Mean surface Dice |
|---|---|---|---|---|---|
| Raw model output | — | — | — | 0.652 (0.596–0.707) | 0.519 |
| After post-processing (primary) | 0.903 | 0.645 | 0.617 | 0.722 (0.665–0.777) | 0.596 |

- The median case scores 0.845. The mean is pulled down by small tumors (tumor Dice 0.324 in that
  group, 0.835 for large tumors) and by failed scans.
- Post-processing helped 52 cases and hurt 7. case_00540 scored 0 on every region.
- Cysts are effectively not separated: median cyst Dice is 0.000.

## What comes next

1. The owner follows the launch order in [operations.md](operations.md#first-launch).
2. Optional, after launch: train longer. This is a separate run, and it must be reported as one.

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
