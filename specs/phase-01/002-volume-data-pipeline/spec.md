# SPEC 002 — Volume Data Pipeline

- **Status:** IMPLEMENTED LOCALLY — KAGGLE RUN PENDING
- **Phase:** 1 — Data
- **Project:** Project_23D — Renal CT 3D Segmentation
- **Date:** 2026-10-22
- **Depends on:** SPEC 001 (locked), D-009, D-010, D-012

## 1. Purpose

Turn the 489 labeled KiTS23 v0.1.4 cases into a verified, split, nnU-Net-ready
dataset, once, on a Kaggle CPU session, so that SPEC 003 can spend all of its GPU
time on training.

## 2. Scope

In scope:

- check every file against the pinned manifest (`data/sources/kits23_v0.1.4_files.tsv`);
- check that each image and its mask have the same geometry;
- measure per-case label features used for stratification;
- make the locked 70/15/15 split and fingerprint it;
- write the nnU-Net v2 raw dataset (`Dataset220_KiTS2023`) and a one-fold
  `splits_final.json`;
- run nnU-Net's fingerprint and planning for `3d_fullres` on Kaggle CPU;
- preprocess the train+val cases in four Kaggle CPU shard notebooks, whose outputs
  SPEC 003 attaches (D-017).

Out of scope: training, inference, metrics (SPEC 003–004).

## 3. Design choices

| Choice | Decision | Why |
|---|---|---|
| Preprocessing | nnU-Net's own fingerprint, plan and preprocess | D-012: official nnU-Net only. Its spacing, intensity and patch choices are the reference; reimplementing them adds risk and no value. |
| Version | `nnunetv2==2.8.1` | Pinned so the plans are reproducible; it provides `nnUNetTrainer_100epochs`. |
| Labels | Region-based, as in nnU-Net's official KiTS23 conversion (`Dataset220_KiTS2023.py`): `kidney=[1,2,3]`, `masses=[2,3]`, `tumor=2`, `regions_class_order=[1,3,2]` | The regions are the official KiTS HECs, so training optimizes what is evaluated. |
| Image reader | `NibabelIOWithReorient` | Same as the official conversion. |
| Test cases | Not in `imagesTr`. Images go to `imagesTs`, labels stay out of the nnU-Net folder | Test labels can't influence the dataset fingerprint or plans. |
| Validation | Fold 0 of a custom `splits_final.json` (train/val from our split) | Keeps our split; nnU-Net's 5-fold default is not used. |
| Files | Symlinks into `/kaggle/input` | No extra disk for about 30 GB of NIfTI. |
| Where | Kaggle CPU notebook (Accelerator None) | Uses no GPU quota (D-012). |

## 4. Split (locked)

- Seed `42`; fractions 70/15/15, giving 343/73/73 for 489 cases.
- Strata: `cohort | size_bin | cyst`.
  - cohort: `kits21` (case ≤ 299) or `kits23_new`. This is a proxy, not a phase label (D-010).
  - size_bin: `none`, or tertiles of tumor volume (ml) among tumor cases. The cut points are recorded.
  - cyst: whether label 3 is present.
- Allocation: largest-remainder per stratum. Test is filled first, then validation, then train. Within a stratum the order is a seeded shuffle of the sorted case IDs.
- `split.json` records the manifest hash, seed, fractions, strata, cut points, per-role summary, roles and the SHA-256 fingerprint of the roles.

## 5. Inputs and outputs

Inputs:

- the KiTS23 images and segmentations as two private Kaggle datasets (D-011);
- the manifest TSV.

Outputs, in `/kaggle/working/spec002/`:

- `verify_report.csv`;
- `case_features.csv`;
- `split.json`;
- `splits_final.json`;
- `run_record.json`.

Output in `/kaggle/working/nnUNet_preprocessed/Dataset220_KiTS2023/`: the plans, the fingerprint, `splits_final.json` (fold 0 without the excluded training cases), `shard_plan.json` and `gt_segmentations/`.

Each shard notebook `kits23-preprocess-k` saves its cases in
`nnUNet_preprocessed/Dataset220_KiTS2023/nnUNetPlans_3d_fullres/` and its record in
`spec002/shard_k.json` (cases done, failed cases, size, hours).

## 6. Code

| File | Role |
|---|---|
| `src/project3d/data/manifest.py` | Find files and check their size and SHA-256 against the manifest |
| `src/project3d/data/features.py` | Label volumes, presence flags, cohort, size bins, image/mask geometry check |
| `src/project3d/data/split.py` | Stratified split, fingerprint, nnU-Net fold file |
| `src/project3d/data/nnunet_export.py` | Raw dataset folder, `dataset.json`, leak check |
| `scripts/data/prepare_kits23.py` | CLI running steps 1–4; stops on any failed check |
| `src/project3d/data/preprocess_plan.py` | Resampled case sizes, excluded cases, shard plan (D-017) |
| `scripts/data/preprocess_shard.py` | Preprocesses one shard, one process per case, with retry and resume |
| `scripts/data/build_kaggle_notebook.py` | Generates the prepare notebook from the files above |
| `scripts/data/build_preprocess_notebook.py` | Generates the four shard notebooks |
| `notebooks/01_prepare_data.ipynb`, `notebooks/01b_preprocess_{1..4}.ipynb` | Kaggle notebooks (generated; don't edit by hand) |

## 7. Requirements

- `S002-REQ-001`: Every image and mask matches the manifest size and SHA-256. Missing, mismatched, duplicate or unexpected files stop the run.
- `S002-REQ-002`: Files un-gzipped by the platform are reported as `DECOMPRESSED_UNVERIFIED` and a warning is shown.
- `S002-REQ-003`: An image/mask shape or affine mismatch stops the run (SPEC 001 §5.4).
- `S002-REQ-004`: Unknown label values stop the run.
- `S002-REQ-005`: The split is case-level, deterministic for a given seed and input, and stratified as in §4.
- `S002-REQ-006`: The split is fingerprinted and saved before any nnU-Net step.
- `S002-REQ-007`: No test case appears in `imagesTr`, `labelsTr` or `splits_final.json`. This is checked automatically after export.
- `S002-REQ-008`: `dataset.json` follows the official nnU-Net KiTS23 region-based format.
- `S002-REQ-009`: The notebook runs exactly the tested code, and a test fails if it is stale.
- `S002-REQ-010`: `run_record.json` records versions, CPU count, split fingerprint, timings, the excluded cases, shard sizes, patch size and spacing. Each shard writes its own record.
- `S002-REQ-011`: Only training cases can be excluded (resampled size above 350 M voxels, D-017); validation and test cases never are.

## 8. Tests and verification

Local (`pytest`, 25 tests):

- manifest status for each failure type;
- volumes computed from physical spacing;
- unknown labels;
- tertile bins;
- geometry mismatch;
- split exact counts (343/73/73 on 489 synthetic cases);
- determinism;
- per-stratum balance (within ±1);
- end-to-end CLI on fake cases;
- stop on a corrupt file, a missing case and a geometry mismatch;
- leak check;
- notebook freshness.

Real-data smoke run (2026-10-22), on the 5 smallest real cases with `--subset`:

- all 10 files verified OK;
- features correct (for example, case_00061: 29×512×512, 5.0 mm slices, tumor 111.6 ml);
- split 3/1/1;
- raw folder layout and `dataset.json` as specified;
- `nnUNetv2_plan_and_preprocess --verify_dataset_integrity` (nnunetv2 2.8.1, CPU torch)
  accepted the folder and wrote compressed `.b2nd` arrays for the 4 train/val cases.
  The plans themselves are not representative (only 4 thick-slice cases).

Kaggle: the full run, checked against §10.

## 9. Risks

| Risk | Handling |
|---|---|
| The preprocessed data (about 50 GB) is larger than Kaggle's 20 GB saved-output limit | Four shard notebooks of about 13 GB each (D-017). |
| Out of RAM on whole-body scans (happened in the first run, on `case_00223`) | Those training cases are excluded; every case runs in its own process, 2 at a time; a crashed case is retried alone. |
| Kaggle's preinstalled torch is incompatible with nnU-Net 2.8.1 (it excludes torch 2.9.x) | pip resolves it during install. The versions are printed and recorded. |
| Dataset folder layout on Kaggle is unknown | Files are found recursively, and the images and segmentation folders are auto-detected by file size. |
| Kaggle un-gzips files | `DECOMPRESSED_UNVERIFIED` status (REQ-002). |

## 10. Acceptance criteria

- The Kaggle run finishes. Verify shows 978 OK and nothing failing.
- The split totals are 343/73/73, and the fingerprint is recorded in `run_record.json`.
- `nnUNetv2_plan_and_preprocess --verify_dataset_integrity` passes.
- `run_record.json` has been returned and is stored in `reports/spec002/`.
- All four shard notebooks finish with no failed case, and the training notebook finds every fold-0 case.
- All local tests pass.

## 11. How to run on Kaggle

1. Push `notebooks/01_prepare_data.ipynb` as `kits23-prepare-data` with the outputs of `kits23-stage-1..3` attached.
   Settings: Accelerator **None**, Internet **On**, private. It takes about 2 hours.
2. Push `notebooks/01b_preprocess_{1..4}.ipynb` as `kits23-preprocess-1..4`, each with
   `kits23-stage-1..3` and `kits23-prepare-data` attached. They can run at the same time; about 2 hours each.
3. Copy the printed records back into the project (`reports/data/`).

## 12. Non-goals

- Custom preprocessing, resampling or intensity windowing (nnU-Net decides these).
- The `2d` and `3d_lowres` configurations (`3d_lowres` only as the fallback above).
- Using the official 110-case challenge test set.
- Phase labels (not in the official metadata, D-010).
