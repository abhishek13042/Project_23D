# Specifications

Each stage of the project has a spec that says what must be delivered and how to prove it
works. Current progress is in [docs/status.md](../docs/status.md).

| Phase | Spec | Purpose | Status |
|---|---|---|---|
| 0 | [001 Foundation](phase-00/001-foundation/spec.md) | Lock the problem, data and evaluation rules | Done, remote pending |
| 1 | [002 Volume data pipeline](phase-01/002-volume-data-pipeline/spec.md) | Verify, split and preprocess the data | Done |
| 2 | [003 Training](phase-02/003-3d-segmentation-model/spec.md) | Train nnU-Net v2 on Kaggle | In progress |
| 3 | [004 Evaluation](phase-03/004-evaluation-and-error-analysis/spec.md) | One scored test run | Code ready, run pending |
| 3 | [005 Case analysis](phase-03/005-experiments-and-ablation/spec.md) | Where the model succeeds and fails | Code ready, run pending |
| 4 | [006 Inference](phase-04/006-inference-and-productization/spec.md) | Merged into 007 | Closed |
| 4 | [007 Report and reproducibility](phase-04/007-release-and-reproducibility/spec.md) | Honest results and rerun steps | Code ready |
| 5 | [008 Model release and inference](phase-05/008-model-release-and-inference/spec.md) | Publish weights, build the predictor | Draft |
| 5 | [009 Demo gallery](phase-05/009-demo-gallery/spec.md) | Pre-computed sample cases | Draft |
| 5 | [010 Inference service](phase-05/010-inference-service/spec.md) | Live inference on ZeroGPU | Draft |
| 5 | [011 Web app and database](phase-05/011-web-app-and-database/spec.md) | The public website | Draft |
| 5 | [012 Deployment and launch](phase-05/012-deployment-and-launch/spec.md) | CI, hosting and launch | Draft |
| 5 | [013 Frontend design](phase-05/013-frontend-design/spec.md) | The survey-sheet look for every page | Code done |

Under D-012 (compute limit), SPEC 002–004 cover one nnU-Net v2 run and its evaluation. SPEC 005
is reduced to a no-GPU case analysis. D-018 added phase 5.

Implementation of a spec starts only after its status moves from DRAFT to APPROVED.
