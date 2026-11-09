# Development guide

## Setup

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
```

On Linux or macOS, use `.venv/bin/python`. nnU-Net and PyTorch are not needed locally: they
are installed in the Kaggle notebooks, and the tests use small fakes in their place.

## Everyday commands

```bash
.venv/Scripts/python -m pytest -q
.venv/Scripts/python -m ruff check apps src scripts tests
.venv/Scripts/python scripts/notebooks/build_all.py
.venv/Scripts/python scripts/ops/check_links.py
```

For the website, run these in `apps/web`:

```bash
npm test
npm run typecheck
npm run build
```

CI runs all of these on every push ([.github/workflows/ci.yml](../.github/workflows/ci.yml)), so
they must pass before a commit.

## Repository map

| Path | Holds |
|---|---|
| `src/project3d/data/` | Manifest checks, case features, split, nnU-Net export, shard planning |
| `src/project3d/eval/` | Metrics, confidence intervals, official evaluator wrapper, case analysis, figures |
| `src/project3d/inference/` | The predictor shared by the command line, the benchmark and the live demo |
| `src/project3d/training/` | The nnU-Net trainer variant that saves checkpoints every 5 epochs |
| `scripts/data/` | Stage the data, prepare it, preprocess one shard |
| `scripts/training/` | Train within one Kaggle session |
| `scripts/eval/` | Score predictions, analyse cases |
| `scripts/report/` | Build `reports/evaluation/results.md` |
| `scripts/release/`, `scripts/inference/` | Package the model, segment a scan, benchmark settings |
| `scripts/gallery/`, `scripts/space/` | Build the sample-case gallery and the Hugging Face Space folder |
| `scripts/ops/` | Site health check, git history scan, Markdown link check |
| `scripts/notebooks/` | Generate the Kaggle notebooks |
| `apps/space/` | The Gradio app that runs the model on Hugging Face Spaces |
| `apps/web/` | The Next.js demo website |
| `tests/` | Same layout as the code it tests |
| `data/sources/` | Pinned URLs and SHA-256 checksums of KiTS23 v0.1.4 |
| `data/raw/` | Local smoke-test cases, git-ignored |

The main folders each have a README with more detail.

## How the notebooks work

The notebooks are generated, so never edit them by hand. Each builder embeds source files from
`src/` and `scripts/` in `%%writefile` cells, which means Kaggle runs exactly the code the
tests cover.

To change something that runs on Kaggle:

1. Edit the file in `src/` or `scripts/`.
2. Run the tests.
3. Run `scripts/notebooks/build_all.py`.
4. Commit the code and the notebooks together.

`tests/notebooks/test_notebooks.py` fails if a notebook is stale.

## Conventions

- **Specs first.** Each stage has a spec in `specs/`, with numbered requirements and acceptance
  criteria.
- **Decisions are recorded.** A choice that changes scope, data or evaluation gets a `D-0xx`
  entry in [decisions.md](decisions.md).
- **Numbers come from records.** A result in a report must be read from a saved run record,
  never typed by hand. Missing records show as *pending*.
- **The test set is one-shot.** It is scored once. Tuning uses validation cases only (D-014).
- **Secrets and data stay out of git.** No tokens, no images, no weights (D-008).
