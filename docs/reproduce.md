# How to reproduce the results

Everything heavy runs on Kaggle. A laptop is only used for code, tests and the
final report. Total cost: about 23 Kaggle GPU-hours as measured, plus a few CPU-hours.

## 0. Local setup (any machine, no GPU)

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m pytest -q
```

All tests must pass. The notebooks are generated from the tested code:

```bash
.venv/Scripts/python scripts/notebooks/build_all.py
```

A test fails if a notebook is out of date, so the notebooks you upload always run the tested code.

## 1. Data on Kaggle (once)

Run the three private staging notebooks `notebooks/00_stage_data_{1,2,3}.ipynb` (Accelerator None, Internet On, about 15–30 min each, no GPU quota). Each downloads about 14 GB of KiTS23 v0.1.4 from the pinned HuggingFace URLs into its output and checks every file against the manifest `data/sources/kits23_v0.1.4_files.tsv` (size and SHA-256 of all 978 files). Shard 1 also holds all segmentations (D-015).

With the Kaggle CLI, each notebook is pushed from a folder holding it and a `kernel-metadata.json` (`"is_private": true`, `"enable_internet": true`, `"enable_gpu": false`):

```bash
kaggle kernels push -p <folder>
```

Later notebooks list `abhishekg14/kits23-stage-1`, `-2` and `-3` under `kernel_sources`. The pipeline links the three image folders into one.

## 2. SPEC 002 — prepare and preprocess (Kaggle CPU, no GPU quota)

| | |
|---|---|
| Notebooks | `notebooks/01_prepare_data.ipynb` (`kits23-prepare-data`, about 2 h), then `notebooks/01b_preprocess_{1..4}.ipynb` (`kits23-preprocess-1..4`, about 2 h each, in parallel) |
| Inputs | prepare: the outputs of `kits23-stage-1..3`; shards: the same plus `kits23-prepare-data` |
| Settings | Accelerator None, Internet On, private |
| Copy back | `spec002/run_record.json` → `reports/data/spec002_run_record.json`; `spec002/shard_{k}.json` → `reports/data/spec002_shard_{k}.json` |

The preprocessed data is about 50 GB, so it is split over four notebook outputs
(D-017). Two oversized whole-body training scans are left out of training; the run
record lists them.

The run checks:

- every file against the manifest;
- the geometry of each image and mask;
- the locked split, 343/73/73, seed 42;
- nnU-Net's own dataset integrity check.

## 3. SPEC 003 — train (Kaggle GPU, about 15 h over 2 sessions)

Measured on a T4: about 209 s per epoch (5.9 h for 100 epochs), then final validation at about 5.6 min per case (about 7 h for 73 cases).

| | |
|---|---|
| Notebooks | `notebooks/02_train_pilot.ipynb` (5 epochs), then `notebooks/02_train.ipynb` (100 epochs) |
| Configuration | nnU-Net v2 2.8.1, `nnUNetTrainer_100epochs_kaggle` (D-016), `3d_fullres`, fold 0 |
| Inputs | the `kits23-prepare-data` and `kits23-preprocess-1..4` outputs; from session 2 on, also the previous training session's output |
| Settings | Accelerator GPU T4 x1, Internet On |
| Copy back | `spec003/run_record.json` → `reports/training/spec003_session{n}_run_record.json` |

Push the 100-epoch notebook as `kits23-train-1`, `kits23-train-2`, and so on.
Each one prints `NOT FINISHED` (push the next session), `DONE` or `STOP`.
The SPEC 004 notebook takes the output of the session that printed `DONE`.

## 4. SPEC 004 + 005 — evaluate (Kaggle GPU, about 7–8 h)

| | |
|---|---|
| Notebook | `notebooks/03_evaluate.ipynb` |
| Inputs | `kits23-stage-1..3`, `kits23-prepare-data`, and only the last training session's output (exactly one `checkpoint_final.pth` must be attached) |
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
