# Project_23D — Renal CT 3D Segmentation

Research-grade 3D semantic segmentation of kidneys, renal tumors, and renal
cysts from contrast-enhanced CT volumes using the KiTS23 dataset.

## Status

SPEC 001 — Foundation & Feasibility is complete locally. SPEC 002 — Volume Data
Pipeline is implemented and tested locally; its Kaggle CPU run
(`notebooks/01_prepare_data.ipynb`, then `notebooks/01b_preprocess_{1..4}.ipynb`, D-017) is pending. SPEC 003 (training) is implemented
(`notebooks/02_train*.ipynb`); its Kaggle GPU run is pending. SPEC 004 (evaluation) and SPEC 005 (case analysis) are implemented and tested
locally; they run on Kaggle in `notebooks/03_evaluate.ipynb` once a model exists. SPEC 007
(report and reproducibility, with SPEC 006 merged in) is implemented: see
[`docs/REPRODUCE.md`](docs/REPRODUCE.md) and
[`reports/evaluation/results.md`](reports/evaluation/results.md) (pending until the runs finish).

The development process is spec-driven:

```text
PROJECT → PHASE → SPEC → TASK → IMPLEMENTATION → TEST → VERIFICATION → EVIDENCE → QUALITY GATE
```

See [`docs/project-overview.md`](docs/project-overview.md) for the locked project
definition and [`specs/phase-00/001-foundation/spec.md`](specs/phase-00/001-foundation/spec.md)
for the complete foundation contract.

The original project brief was not present in the empty project folder. The
foundation therefore records the current project definition from the kickoff
requirements and verifies the KiTS23 primary dataset against its official sources.
