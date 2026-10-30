# SPEC 003 — Training

- **Status:** IMPLEMENTED LOCALLY — KAGGLE RUN PENDING (needs the SPEC 002 output)
- **Phase:** 2 — Model
- **Project:** Project_23D — Renal CT 3D Segmentation
- **Date:** 2026-10-24
- **Depends on:** SPEC 002 (`Dataset220_KiTS2023`, preprocessed, locked fold 0), D-012, D-013, D-016

## 1. Purpose

Train one official nnU-Net v2 model (3d_fullres, fold 0, 100 epochs) on Kaggle's
free GPU. The run must survive the 12-hour session limit and record what it did.

## 2. Scope

In scope:

- a 5-epoch pilot that checks the pipeline and measures the time per epoch;
- the 100-epoch run, split over resumable Kaggle sessions;
- nnU-Net's own fold-0 validation (its predictions feed SPEC 004 post-processing);
- a run record per session and a session log that travels with the checkpoints.

Out of scope: other folds, other architectures and ensembles (D-012), and
test-set inference (SPEC 004).

## 3. Design choices

| Choice | Decision | Why |
|---|---|---|
| Trainer | `nnUNetTrainer_100epochs_kaggle`: nnU-Net's `nnUNetTrainer_100epochs` with `save_every = 5` | Same training recipe. A stopped session loses at most 5 epochs, not 50 (D-016). |
| Sessions | `train.py` stops nnU-Net before the session's budget runs out (11.25 h minus setup). The next session attaches that output and runs `nnUNetv2_train --c` | Kaggle ends a GPU session after 12 h. Resuming is nnU-Net's own mechanism. |
| Final validation | If `checkpoint_final.pth` exists but `validation/summary.json` doesn't, run `--val`. Half-written predictions are deleted, and the trainer skips cases already predicted | A session can end during validation, after training finished (it took about 5.6 min per case on the T4, so session 1 stopped at 57 of 73). nnU-Net's `--val` would redo all of them. |
| GPU | T4 | Recent PyTorch builds dropped P100 (sm_60) support. |
| Data loading | Preprocessed data copied to `/tmp`; `nnUNet_n_proc_DA=4` | Local disk is faster; the Kaggle GPU machine has 4 CPUs. |
| `torch.compile` | Off (`nnUNet_compile=f`) | Its compile time recurs each session and can fail on T4. |
| Pilot | nnU-Net's own `nnUNetTrainer_5epochs`, 1.5 h budget | Finds problems before the long run. Its seconds per epoch sets the number of sessions. |

## 4. Inputs and outputs

Inputs (Kaggle): the `kits23-prepare-data` output
(`nnUNet_preprocessed/Dataset220_KiTS2023`). From session 2 on, also the previous
training session's output.

Outputs, in `/kaggle/working/`:

- `nnUNet_results/Dataset220_KiTS2023/<trainer>__nnUNetPlans__3d_fullres/`:
  - `plans.json`, `dataset.json`;
  - `fold_0/` with checkpoints, `training_log_*.txt`, `progress.png`, and
    `validation/` at the end;
  - `project23d_sessions.json`: one row per session.
- `spec003/run_record.json`: trainer, GPU, sessions, total hours, epochs done,
  state, mean epoch time, last pseudo Dice, fold-0 validation Dice.

## 5. Code

| File | Role |
|---|---|
| `src/project3d/training/nnunet_trainer.py` | The trainer class; copied into nnU-Net's `variants/` folder on Kaggle |
| `scripts/training/train.py` | Finds inputs, restores the previous session, runs within budget, writes records |
| `scripts/training/build_train_notebook.py` | Generates `notebooks/02_train_pilot.ipynb` and `notebooks/02_train.ipynb` |
| `tests/training/test_train.py` | Input discovery, state machine, log parsing, budget stop, record, trainer settings |

## 6. Acceptance

- [x] Local tests pass (`pytest`).
- [ ] Pilot: 5 epochs finish, validation runs, epoch time is recorded.
- [ ] Full run: `state = done`, 100 epochs, `fold_0/validation/summary.json` present.
- [ ] Run record copied to `reports/training/spec003_run_record.json`.
