# Project_23D: Kidney Tumor Segmentation in 3D CT

A 3D segmentation model that finds kidneys, renal tumors and cysts in contrast-enhanced
CT scans. It is built with [nnU-Net v2](https://github.com/MIC-DKFZ/nnUNet) on the
[KiTS23](https://github.com/neheller/kits23) dataset, and evaluated once on a locked test
set with the official KiTS23 evaluator.

**Research and portfolio project. Not a medical device. Not for clinical use.**

## Status

| Stage | State |
|---|---|
| Data: 489 cases staged, split 343/73/73, preprocessed on Kaggle | Done |
| Training: nnU-Net v2, `3d_fullres`, fold 0, 100 epochs | Trained; final validation finishing |
| Evaluation on the 73 test cases | Pending |
| Public demo: website, live inference, database | Planned ([phase 5 specs](specs/phase-05/README.md)) |

Results will appear in [reports/evaluation/results.md](reports/evaluation/results.md). That
file is generated from the run records, so it shows *pending* until the run has finished.
Detail is in [docs/status.md](docs/status.md).

## How it works

```text
KiTS23 CT scans
  → checks every file against its checksum
  → splits by case, seed 42, with 73 test cases locked away
  → nnU-Net v2 trains one 3D U-Net on Kaggle's free GPU
  → scored once with the official KiTS23 evaluator, with 95% confidence intervals
  → case analysis: which tumors it finds, and where it fails
```

## Repository layout

```text
src/project3d/      Library code: data, evaluation, training
scripts/            Command-line entry points, one folder per stage
  notebooks/        Generators for the Kaggle notebooks
notebooks/          Generated Kaggle notebooks (do not edit by hand)
tests/              Pytest suite, mirrors src/ and scripts/
data/sources/       Pinned file lists and checksums (the data itself is not in git)
reports/            Run records and generated results
docs/               Documentation, start at docs/README.md
specs/              What each stage must deliver, one spec per stage
```

## Quick start

No GPU or dataset is needed to run the tests.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m pytest -q
```

To run the full pipeline, follow [docs/reproduce.md](docs/reproduce.md). Everything heavy
runs on Kaggle's free tier.

## Documentation

- [docs/README.md](docs/README.md): index of all documents
- [docs/project-overview.md](docs/project-overview.md): the problem and the scope
- [docs/architecture.md](docs/architecture.md): how the system fits together
- [docs/evaluation.md](docs/evaluation.md): how results are measured
- [docs/decisions.md](docs/decisions.md): every major decision and why
- [docs/deployment.md](docs/deployment.md): how the demo runs for $0

## License

The source code is MIT ([LICENSE](LICENSE)). The KiTS23 data, and the weights and sample
cases derived from it, are CC BY-NC-SA 4.0: non-commercial use only, shared under the same
terms. See [NOTICE.md](NOTICE.md).
