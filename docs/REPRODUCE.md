# How to reproduce the results

Everything heavy runs on Kaggle. A laptop is only used for code, tests and the
final report. Total cost: about 15 Kaggle GPU-hours plus a few CPU-hours (D-012).

## 0. Local setup (any machine, no GPU)

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m pytest -q
```

All tests must pass. The notebooks are generated from the tested code:

```bash
.venv/Scripts/python scripts/data/build_kaggle_notebook.py
.venv/Scripts/python scripts/eval/build_eval_notebook.py
```

A test fails if a notebook is out of date, so the notebooks you upload always run the tested code.

## 1. Data on Kaggle (once)

Stage KiTS23 v0.1.4 as two private Kaggle datasets, images and segmentations, from the pinned URLs (D-011, `reports/foundation/approach_review.md` §3).
The manifest `data/sources/kits23_v0.1.4_files.tsv` holds the size and SHA-256 of all 978 files.

## 2. SPEC 002 — prepare (Kaggle CPU, about 1–4 h, no GPU quota)

| | |
|---|---|
| Notebook | `notebooks/01_prepare_data.ipynb` |
| Inputs | the two KiTS23 datasets |
| Settings | Accelerator None, Internet On |
| Save output as | private dataset `kits23-nnunet-preprocessed` |
| Copy back | `spec002/run_record.json` → `reports/data/spec002_run_record.json` |

The run checks:

- every file against the manifest;
- the geometry of each image and mask;
- the locked split, 343/73/73, seed 42;
- nnU-Net's own dataset integrity check.

## 3. SPEC 003 — train (Kaggle GPU, about 14 h)

Not written yet. When it exists:

| | |
|---|---|
| Configuration | nnU-Net v2 2.8.1, `nnUNetTrainer_100epochs`, `3d_fullres`, fold 0 |
| Input | `kits23-nnunet-preprocessed` |
| Save output as | a private dataset holding `.../fold_0/checkpoint_final.pth` and `fold_0/validation/` |
| Copy back | its run record → `reports/training/spec003_run_record.json` |

## 4. SPEC 004 + 005 — evaluate (Kaggle GPU, about 1–3 h)

| | |
|---|---|
| Notebook | `notebooks/03_evaluate.ipynb` |
| Inputs | both KiTS23 datasets, `kits23-nnunet-preprocessed`, the training output |
| Settings | GPU T4 x1, Internet On |

What it does:

1. predicts the 73 test cases;
2. chooses post-processing on validation only;
3. scores raw and post-processed predictions with the official KiTS23 evaluator;
4. writes the case analysis and figures.

Copy back the `spec004/` output folder **without** `pred_raw/` and `pred_pp/` to `reports/evaluation/spec004/`. NIfTI files are git-ignored anyway.

The folder should contain:

- `run_record.json`;
- `postprocessing.pkl`;
- `eval_pp/` and `eval_raw/` (each with `per_case.csv` and `summary.json`);
- `analysis/` (`analysis.md`, `analysis.json` and `figures/`).

## 5. Report (local)

```bash
.venv/Scripts/python scripts/report/build_report.py
```

This writes `reports/evaluation/results.md` using only the copied records. Anything missing is shown as *pending*.

Check section 4 of that report:

- the split fingerprint must say **match**;
- the Dice cross-check must be at most 1e-3.

## What "reproduced" means here

GPU training is not bit-for-bit deterministic, so a rerun gives slightly different weights. Two things count as a reproduction:

- the same split fingerprint;
- co-primary metrics inside the reported 95% CIs.

Identical numbers are not required (`docs/limitations.md`).
