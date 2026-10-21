# Architecture

## Foundation architecture

The project is organized around one volumetric data contract and one reproducible
experiment contract.

```text
KiTS23 official release
        ↓
Case manifest and integrity validation
        ↓
Subject-level train/validation/test split
        ↓
Canonical orientation and model-space preprocessing
        ↓
nnU-Net v2 (3d_fullres, fold 0)
        ↓
Patch or whole-volume inference
        ↓
Restored NIfTI segmentation with source geometry
        ↓
KiTS hierarchical metrics + per-class metrics
        ↓
Qualitative and failure analysis
```

## Frozen boundaries

- The input is a single contrast-enhanced CT volume per KiTS case.
- The output is a mutually exclusive semantic label volume.
- Source shape, spacing, orientation, and affine are retained in the manifest.
- Any resampling uses image interpolation for CT and nearest-neighbor
  interpolation for masks.
- Evaluation is case-level and performed in physical voxel spacing for boundary
  metrics.
- Predictions are mapped back to the source geometry before export.

## Model strategy

Because of the compute limit (D-012), one model is trained: the **official
nnU-Net v2** implementation, `3d_fullres` configuration, fold 0, 100 epochs
(`3d_lowres` fallback). No hand-built baseline is trained. nnU-Net handles
resampling, intensity normalization, patch size and export back to source geometry.

V-Net and transformer models are research references, not automatic additional
implementations. A third architecture requires a documented hypothesis.

## Data flow contracts

```text
CaseRecord
→ VolumeRecord + MaskRecord
→ ModelSample
→ PredictionRecord
→ CaseMetricRecord
→ EvaluationReport
```

No downstream implementation may silently change label semantics, geometry, or
subject identity.
