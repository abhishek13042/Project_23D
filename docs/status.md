# Project status

Last updated: 2026-10-30.

## Where the project is

| Spec | Stage | State |
|---|---|---|
| 001 | Foundation | Done. The GitHub remote is still missing (SPEC 012) |
| 002 | Data pipeline | Done. 414 of 414 train and validation cases preprocessed on Kaggle |
| 003 | Training | 100 epochs done. Final validation finishing in session 2 |
| 004 | Evaluation | Code ready and tested. Kaggle run pending |
| 005 | Case analysis | Code ready and tested. Runs in the same notebook as 004 |
| 006 | Inference | Merged into 007, then replaced by phase 5 |
| 007 | Report and reproducibility | Code ready. Report fills in after 004 |
| 008–012 | Public demo | Drafted, see [phase 5](../specs/phase-05/README.md) |

## Training so far

Source: `reports/training/spec003_session1_run_record.json`.

- Session 1 trained all 100 epochs in about 5.9 hours on a T4, at about 209 s per epoch.
- Its final validation finished 57 of 73 cases before the session limit, at about 5.6 minutes
  per case. That was slower than planned.
- The last pseudo Dice was 0.955 / 0.847 / 0.819 for the three regions, mean 0.874. **This is not
  a result.** It is a noisy training-time number and it runs optimistic. The previous epoch was
  0.93 / 0.78 / 0.78.
- Session 2 (`kits23-train-2`) resumes the remaining validation cases.

## What comes next

1. Session 2 finishes, then the record is copied to `reports/training/`.
2. `kits23-evaluate` predicts the 73 test cases, about 7–8 hours on the GPU.
3. `scripts/report/build_report.py` writes the real results.
4. Phase 5 starts with SPEC 008.

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
