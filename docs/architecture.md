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
3D U-Net baseline / nnU-Net reference
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

The first comparison is deliberately small:

1. compact 3D U-Net baseline;
2. nnU-Net-style/reference configuration using its documented self-configuration
   principles or official nnU-Net implementation if adopted after the smoke test.

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
