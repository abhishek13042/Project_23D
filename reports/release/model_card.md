# Model card — nnU-Net v2, KiTS23, fold 0

**Status:** Evaluated once on the 73 internal test cases. Mean Dice is 0.722 (95% CI
0.665–0.777) and mean surface Dice is 0.596 (0.550–0.641). Full numbers are in
[`reports/evaluation/results.md`](../evaluation/results.md).

> Research demo, not for clinical use.

## What it is

- **Task:** 3D semantic segmentation of contrast-enhanced abdominal CT.
- **Outputs:** voxel labels 0 background, 1 kidney, 2 tumor, 3 cyst. The model is trained on the KiTS regions: kidney + masses, masses, tumor.
- **Method:** the official nnU-Net v2 (2.8.1), `3d_fullres`, `nnUNetTrainer_100epochs_kaggle` (the standard 100-epoch recipe, saving checkpoints more often, D-016). One fold only (fold 0), with post-processing chosen on validation that keeps the two largest foreground regions (D-012, D-021).
- **Data:** KiTS23 v0.1.4, 489 labeled cases, split at case level into 343 train, 73 validation and 73 locked test cases (seed 42). Two oversized whole-body scans were left out of training, so 341 cases were trained on (D-017). The split is stratified by cohort proxy, tumor size and cyst presence.

## Intended use

This is a portfolio and research project, built to learn and to show a correctly measured 3D medical segmentation workflow. **It is not a medical device.**

- It must not be used for diagnosis, treatment planning or any decision about a patient.
- It has no regulatory clearance and no clinical validation.

## How it was evaluated

The model was run once on the 73 internal test cases. The co-primary metrics are the official KiTS23 Dice and surface Dice, averaged over the three regions per case and then over cases, each with a bootstrap 95% CI.

The report also includes:

- secondary metrics: IoU, precision, recall, HD95 and volume error;
- an analysis by tumor size, cyst presence and cohort (SPEC 005).

## Known limitations

- **Short training:** one fold and 100 epochs instead of nnU-Net's 5 folds × 1000 epochs, so expect lower scores than the published nnU-Net KiTS23 results.
- **False regions:** the raw model marks false regions away from the kidneys in most scans. Post-processing keeps the two largest regions (D-021), which fails when a false region is bigger than a real kidney. On the test set it made 7 of 73 cases slightly worse, and case_00540 scored 0 on every region.
- **Small tumors:** the small-tumor group has a tumor Dice of 0.324, against 0.835 for large tumors.
- **Cysts:** cysts are effectively not separated from tumors. Median cyst Dice is 0.000 across the 37 test cases that have cysts.
- **Internal test set:** the test set comes from the public KiTS23 training cases. It is not the hidden challenge test set and not an external hospital, so the results can't be compared directly with the leaderboard.
- **Small groups:** 73 test cases, so the sub-group results (for example small tumors) are uncertain. They are descriptive only.
- **No contrast-phase data:** the contrast phase per case is unknown (D-010), so phase effects can't be measured.
- **Dataset biases:** biases in patient population, scanners and annotation are inherited from KiTS23.
- **License:** data CC BY-NC-SA 4.0. The model weights are derived from that data, so non-commercial use only.

## Inference settings

Measured on six validation cases on a Kaggle T4 GPU (`inference_benchmark.json`). The test set was
not used. Peak memory was the same for all three: 4.5 GB of GPU memory and 12.7 GB of RAM.

| Setting | Mean time per scan | Slowest scan | Mean Dice | Mean surface Dice |
|---|---|---|---|---|
| Full: test-time augmentation, tile step 0.5 | 442 s | 608 s | 0.566 | 0.434 |
| No test-time augmentation, tile step 0.5 | 133 s | 222 s | 0.566 | 0.427 |
| No test-time augmentation, tile step 0.75 (**live demo**) | 103 s | 182 s | 0.644 | 0.472 |

The full setting matches the evaluation: Dice of at least 0.9995 against the saved validation
predictions. The published scores and the run-it-yourself notebook use it.

The live demo uses the last setting because it is about four times faster. Its higher Dice is not an
improvement. It comes almost entirely from one scan, case_00002, which went from 0.267 to 0.788, and
six cases can't support more than "no loss was measured". The demo setting was not scored on the
73 test cases.

## How to use it

Install `nnunetv2==2.8.1`, then copy `project23d_trainer.py` into nnU-Net's
`training/nnUNetTrainer/variants/` folder. The checkpoint names that class, so nnU-Net can't load
the model without it. Keep the two largest connected foreground regions of the output
(26-connected), as described in `postprocessing.json`. The published scores depend on that step.

`checksums.json` holds the SHA-256 of every file in this package.

## Credits and license

- **Data:** KiTS23 (<https://github.com/neheller/kits23>), CC BY-NC-SA 4.0.
- **Method:** nnU-Net (Isensee et al., *Nature Methods* 2021; <https://github.com/MIC-DKFZ/nnUNet>), Apache 2.0.
- **These weights:** CC BY-NC-SA 4.0, because they are derived from KiTS23. Non-commercial use only, shared under the same terms.

See also [`docs/limitations.md`](../../docs/limitations.md).
