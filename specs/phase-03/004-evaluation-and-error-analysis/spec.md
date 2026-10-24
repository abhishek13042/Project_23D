# SPEC 004 — Evaluation

- **Status:** IMPLEMENTED LOCALLY — KAGGLE RUN PENDING (needs the SPEC 003 model)
- **Phase:** 3 — Evaluation
- **Project:** Project_23D — Renal CT 3D Segmentation
- **Date:** 2026-10-24
- **Depends on:** SPEC 002 (split, features), SPEC 003 (fold-0 model), D-012, D-014

## 1. Purpose

Score the single trained nnU-Net v2 model (fold 0) once on the 73 locked test
cases, with the official KiTS23 evaluator and confidence intervals, so that the
headline number can be trusted and reproduced.

## 2. Scope

In scope:

- test-set inference with `nnUNetv2_predict_from_modelfolder` (Kaggle GPU);
- nnU-Net post-processing, chosen on the fold-0 validation predictions only;
- co-primary metrics (official Dice and surface Dice) with bootstrap 95% CIs;
- secondary metrics per region, per-case table and run record.

Out of scope: training (SPEC 003), the case analysis and figures (SPEC 005, run in
the same notebook), the official challenge test set, ensembles.

## 3. Design choices

| Choice | Decision | Why |
|---|---|---|
| Evaluator | `kits23.evaluation.metrics.compute_metrics_for_case`, installed from GitHub; version and commit recorded | D-012: the official evaluator and its empty-mask rule. |
| Geometry check | Our own shape and affine check before scoring; the run stops on a mismatch | The official function's own shape/spacing checks are ineffective (they compare objects that are never equal). |
| Config check | `check_config()` asserts the installed evaluator's HEC labels and surface-Dice tolerances match ours | A silent evaluator change would change the metric. |
| Cross-check | Our Dice vs official Dice, per case and HEC; stop if the difference is above 1e-3 | Catches orientation or loading bugs. |
| Post-processing | `nnUNetv2_determine_postprocessing` on fold-0 validation, applied to test | The protocol forbids tuning on test (docs/evaluation.md). If the validation folder is incomplete, post-processing is skipped and this is recorded. |
| Primary result | Post-processed predictions; raw predictions also scored | Transparency: shows what post-processing changed. |
| Per-case mean | Mean of the three HEC scores per case, then mean over cases | KiTS23 ranking convention; per-case averaging (docs/evaluation.md). |
| CI | Case bootstrap, 10 000 resamples, seed 42, percentile 95%; only with ≥ 10 cases | Enough resamples for stable bounds; no CI on tiny smoke sets. |
| HD95 | D-014 | — |

## 4. Inputs and outputs

Inputs (Kaggle): the two KiTS23 datasets, `kits23-nnunet-preprocessed`
(`spec002/split.json`, `case_features.csv`), and the training output that holds
`<trainer>/fold_0/checkpoint_final.pth`, `plans.json`, `dataset.json` and
`fold_0/validation/`.

Outputs, in `/kaggle/working/spec004/`:

- `pred_raw/`, `pred_pp/` — test label maps;
- `postprocessing.pkl` — what was chosen on validation;
- `eval_pp/`, `eval_raw/` — `per_case.csv`, `summary.json`;
- `analysis/` — SPEC 005;
- `run_record.json`.

## 5. Code

| File | Role |
|---|---|
| `src/project3d/eval/metrics.py` | Regions, Dice/IoU/precision/recall, HD95, volumes |
| `src/project3d/eval/stats.py` | Descriptive statistics and bootstrap CI |
| `src/project3d/eval/official.py` | Official evaluator wrapper, config check, version |
| `scripts/eval/evaluate.py` | CLI: scores a prediction folder against a split role |
| `scripts/eval/build_eval_notebook.py` | Generates the notebook |
| `notebooks/03_evaluate.ipynb` | Kaggle notebook (generated; don't edit by hand) |

## 6. Requirements

- `S004-REQ-001`: Only cases with role `test` in the locked `split.json` are scored; a missing prediction or a missing/duplicate reference stops the run.
- `S004-REQ-002`: A prediction whose shape or affine differs from its reference, or that has labels outside {0,1,2,3}, stops the run.
- `S004-REQ-003`: Co-primary metrics come from the official evaluator; without it the summary is marked `primary_valid: false`.
- `S004-REQ-004`: The installed evaluator's classes and tolerances are checked against ours before scoring.
- `S004-REQ-005`: Post-processing is chosen only on fold-0 validation predictions.
- `S004-REQ-006`: Bootstrap 95% CIs are reported for both co-primary metrics and per-HEC Dice.
- `S004-REQ-007`: Secondary metrics per region (three HECs plus kidney and cyst) with denominators: number of cases, number with empty reference, number undefined.
- `S004-REQ-008`: `summary.json` records the split fingerprint and evaluator version; `run_record.json` records versions, GPU, TTA setting, post-processing and timings.
- `S004-REQ-009`: The test set is evaluated once; no setting is changed after seeing test results.
- `S004-REQ-010`: The notebook runs exactly the tested code, and a test fails if it is stale.

## 7. Tests and verification

Local (`pytest`, `tests/eval/`):

- the empty-mask rule;
- the overlap formulas;
- HD95 for parallel planes with anisotropic spacing, and against a brute-force distance computation;
- the regions in the case metrics;
- bootstrap and descriptive statistics;
- end-to-end `evaluate.py` with a fake official evaluator;
- `--no-official` marks the primary result invalid;
- a config mismatch is caught;
- the run stops on a missing prediction and on a misaligned prediction;
- notebook freshness and embedded files.

Real-data smoke run (2026-10-24), on the 5 local real cases. The predictions were the references, with one case's tumor shifted by 5 voxels.

- Untouched cases: Dice 1.0, HD95 0.
- Shifted case: tumor Dice 0.919, tumor HD95 4.0 mm.
- Speed: about 2 s per 512×512 case on a laptop CPU with 3 processes.

The official evaluator was not run locally (its install is Kaggle-only).

## 8. Risks

| Risk | Handling |
|---|---|
| Test inference with test-time augmentation is slow on a T4 | `DISABLE_TTA` switch (about 8× faster); the setting is recorded. |
| The training output lacks `fold_0/validation` | Post-processing is skipped, pred_pp = pred_raw, `postprocessing_applied: false`. |
| The kits23 install changes packages | Versions printed and recorded; nnU-Net is pinned. |
| Orientation mismatch between the model output and the references | Geometry check plus the Dice cross-check stop the run. |

## 9. Acceptance criteria

- The notebook finishes, and evaluates 73 of 73 test cases.
- `primary_valid` is true, and the cross-check difference is at most 1e-3.
- Both co-primary means are reported with CIs, for raw and post-processed predictions.
- `run_record.json` is returned and stored in `reports/evaluation/`.
- All local tests pass.

## 10. How to run on Kaggle

1. Finish SPEC 003. Save its output (the `nnUNet_results` folder) as a private dataset.
2. Import `notebooks/03_evaluate.ipynb`, and add the four inputs in §4.
3. Set Accelerator to **GPU T4 x1** and Internet to **On**. Then click **Save Version → Save & Run All**.
4. Save the output as a private dataset. Copy the printed `run_record` back into the project.

## 11. Deviations from docs/evaluation.md (lean scope, D-012)

Specificity, relative volume error and 3D surface renderings are not produced.
Specificity is dominated by the background in CT, and the volume error is reported in absolute ml.
