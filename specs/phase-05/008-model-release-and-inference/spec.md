# SPEC 008 — Model Release and Inference Package

- **Status:** DRAFT
- **Phase:** 5 — Public demo
- **Depends on:** SPEC 003, SPEC 004, D-014, D-018

## 1. Purpose

Make the trained model usable outside the Kaggle notebooks: publish the weights, and provide one
tested predictor that the gallery and the live service both call.

## 2. Deliverables

| File | Content |
|---|---|
| `src/project3d/inference/predictor.py` | Load the model, predict one volume, return labels and region volumes |
| `scripts/inference/predict.py` | Command line: NIfTI in, segmentation and JSON summary out |
| `scripts/release/export_model.py` | Package the checkpoint, plans, `dataset.json` and `postprocessing.pkl` |
| Hugging Face model repo | The packaged model and its model card |
| `reports/release/inference_benchmark.json` | Speed and quality of each inference setting |
| `reports/release/model_card.md` | Updated with results and the settings the demo uses |

## 3. Requirements

- `S008-REQ-001`: The predictor applies the same post-processing as the evaluated model.
- `S008-REQ-002`: The output keeps the input's shape, spacing and affine.
- `S008-REQ-003`: The output includes each region's volume in mL, calculated from the voxel spacing.
- `S008-REQ-004`: Test-time augmentation and tile step are options. The defaults match the evaluation.
- `S008-REQ-005`: Input is rejected with a clear error if it isn't 3D, or has invalid spacing, or is too large.
- `S008-REQ-006`: The model repo states CC BY-NC-SA 4.0, credits KiTS23 and nnU-Net, and says "not for clinical use".
- `S008-REQ-007`: The packaged files are checksummed, and the checksum is recorded in the repository.

## 4. Speed and quality measurement

The demo probably can't afford the full evaluation setting, so the trade-off must be measured.

- Compare at least: full setting; no test-time augmentation; no test-time augmentation with a
  larger tile step.
- Measure Dice and surface Dice on **validation cases only**, on a Kaggle GPU. The test set is
  not touched (D-014).
- Record time per case and the peak memory on GPU and on CPU.
- The demo states which setting it uses and that setting's validation score.

## 5. Tests

- Geometry round trip with a fake model.
- Volume calculation against a mask of known size.
- Rejection of each kind of invalid input.
- The default options match the evaluated setting.

## 6. Acceptance criteria

- [ ] A clean Kaggle notebook downloads the model repo and predicts a validation case.
- [ ] With default settings, that case's result matches the SPEC 003 validation prediction: Dice of at least 0.99 between the two.
- [ ] `inference_benchmark.json` covers all three settings.
- [ ] The model card is updated.

## 7. Non-goals

- Training a smaller or faster model.
- ONNX export.
- Any tuning on the test set.
