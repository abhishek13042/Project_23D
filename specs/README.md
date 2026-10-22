# Specification Index

Current status: **SPEC 001 verified locally; remote synchronization pending because
no intended remote URL is configured.** SPEC 002 is implemented and tested locally; its Kaggle CPU run is pending.

Specifications are organized by major engineering milestone rather than by every
small technical concept.

| Phase | Specification | Purpose |
|---|---|---|
| 0 | 001 Foundation | Lock problem, data, feasibility, and reproducibility contracts |
| 1 | 002 Volume Data Pipeline | Ingest, validate, preprocess, split, and package 3D volumes |
| 2 | 003 3D Segmentation Model | Baseline, main model, training, checkpointing, and inference contract |
| 3 | 004 Evaluation and Error Analysis | Metrics, visual analysis, failure modes, and generalization |
| 3 | 005 Experiments and Ablation | Hypothesis-driven comparisons and controlled improvements |
| 4 | 006 Inference and Productization | Reusable inference pipeline and appropriate demo/interface |
| 4 | 007 Release and Reproducibility | Packaging, documentation, artifacts, and final audit |

Under D-012 (compute limit, one week), SPEC 002-004 cover the single nnU-Net v2
run and its evaluation. SPEC 005 is reduced to the no-GPU case analysis (E-005);
SPEC 006-007 are reduced to a short reproducibility write-up.

No implementation begins until the relevant specification is approved and locked.
