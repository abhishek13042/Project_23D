# Architecture

The project has two halves: a research pipeline that runs on Kaggle and produces the
model and its measured results, and a public product built on top of them. Only the
first half exists today. The second is specified in
[phase 5](../specs/phase-05/README.md).

## Research pipeline

The pipeline is organized around one volumetric data contract and one reproducible
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

## Where each stage runs

| Stage | Runs on | Code | Output |
|---|---|---|---|
| Staging | Kaggle CPU | `scripts/data/stage_kits23.py` | Verified KiTS23 files |
| Prepare | Kaggle CPU | `scripts/data/prepare_kits23.py` | Split, nnU-Net plans, shard plan |
| Preprocess | Kaggle CPU, 4 notebooks | `scripts/data/preprocess_shard.py` | About 50 GB of training data |
| Train | Kaggle GPU | `scripts/training/train.py` | Weights and validation predictions |
| Evaluate | Kaggle GPU | `scripts/eval/` | Scores and case analysis |
| Report | Laptop | `scripts/report/build_report.py` | `reports/evaluation/results.md` |

## Product (planned)

```text
             pages                 ┌──────────────────────────┐
  Browser ◄───────────────────────►│ Vercel: Next.js          │
  NiiVue viewer                    │ pages + small API        │
     │  ▲                          └───────────┬──────────────┘
     │  │ sample cases                         │ run statistics
     │  │                                      ▼
     │  └─ Hugging Face dataset        Neon Postgres
     │
     │  scan upload and result (direct, not through Vercel)
     ▼
  Hugging Face ZeroGPU Space: Gradio + nnU-Net ◄── Hugging Face model repo (weights)
```

Three rules shape this design:

- **Scans skip the website server.** The browser talks directly to the Space, so large files
  never pass through Vercel functions.
- **The demo works with no backend.** The gallery is plain files, so it stays up if the GPU quota
  runs out or the Space goes down.
- **The database never holds images.** It stores only run statistics, with no IP addresses.

Why these services: [deployment.md](deployment.md) and D-019.
