# Decision Log

## D-001 — Use KiTS23 as the primary dataset

- **Date:** 2026-10-08
- **Decision:** Use KiTS23 v0.1.4 for the primary renal segmentation project.
- **Reason:** It matches the renal 3D task, provides voxel labels and an official
  evaluator, has 489 labeled training cases, and is publicly accessible with clear
  non-commercial licensing terms.

## D-002 — Define the task as multiclass semantic segmentation

- **Decision:** Predict mutually exclusive labels 0 background, 1 kidney, 2 tumor,
  3 cyst.
- **Reason:** This matches the official KiTS23 label ontology.

## D-003 — Treat the case ID as the unit of independence

- **Decision:** Split by `case_XXXXX`; never split slices or patches.
- **Reason:** A 3D scan and all derived samples must remain in one partition.

## D-004 — Create an internal test set from labeled cases

- **Decision:** Use a reproducible 70/15/15 train/validation/internal-test split of
  the 489 labeled cases.
- **Reason:** Official challenge test labels are not ordinarily available for local
  scoring, so local model selection and reporting need a locked, case-disjoint
  holdout drawn from the labeled cases.

## D-005 — Use KiTS hierarchical evaluation classes

- **Decision:** Primary evaluation includes kidney-and-masses, mass, and tumor HECs.
- **Reason:** The official evaluator recognizes nested renal structures and avoids
  penalizing tumor/cyst confusion as a complete miss of the renal mass.

## D-006 — Keep the model comparison small

- **Decision:** Compare a compact 3D U-Net baseline with an nnU-Net-style reference.
- **Reason:** This provides a meaningful baseline/reference comparison without an
  unplanned architecture zoo.
- **Status:** Superseded by D-012 (official nnU-Net v2 only; baseline is future work).

## D-007 — Use the same code path locally and on Kaggle

- **Decision:** Local mode is for smoke testing and Kaggle mode is for serious
  training, experiments, and full evaluation; both use the same code path.
- **Reason:** This prevents environment-specific implementations and reduces wasted
  GPU time on errors that a local smoke test would have caught.

## D-008 — Do not commit data, checkpoints, or secrets

- **Decision:** Use `.gitignore` rules for raw/derived data, model weights, generated
  outputs, and local secrets.
- **Reason:** Dataset licensing, repository size, and secret safety.

## D-009 — No remote push without an intended remote URL

- **Decision:** Do not fabricate or guess a GitHub remote.
- **Reason:** The repository has no configured remote and the intended destination
  has not been supplied; guessing one could publish the project to the wrong place.

## D-010 — Treat contrast phase as unknown unless a verified source exists

- **Date:** 2026-10-21
- **Decision:** Record `acquisition_phase` as `unknown` for every case unless a
  verified per-case source is found. Stratify the split by tumor and cyst presence
  only.
- **Reason:** The 2026-10-21 availability check found that the official
  `dataset/kits23.json` metadata (489 records) has no contrast-phase field. The
  challenge homepage states that cases are corticomedullary or nephrogenic but does
  not give a per-case mapping. SPEC 001 forbids guessing the phase.
- **Status:** Stratification extended by D-012 (cohort proxy and tumor-size bin added).

## D-011 — Acquire the full dataset on Kaggle, not locally

- **Date:** 2026-10-21
- **Decision:** The 42.3 GB KiTS23 release is imported straight into private Kaggle
  datasets from the Hugging Face mirror, pinned to commit
  `65f1f295873a326230153c7e1de0c7dba10f0b29`. Every file is verified against
  `data/sources/kits23_v0.1.4_files.tsv` (size and SHA-256). The local machine
  holds only a small smoke-test subset of about five cases.
- **Reason:** The local device lacks room for the full release. The mirror
  segmentations are byte-identical to the official GitHub ground truth (verified on
  sampled cases), so a single source with published checksums covers images and
  labels. Kaggle's Remote Files import uses no local bandwidth. Plan details and
  the fallback are in `reports/foundation/approach_review.md` §3.

## D-012 — Lean compute-limited scope (one week, about 15 GPU-hours)

- **Date:** 2026-10-21
- **Decision:** The project is cut to one well-measured model:
  - Reference model: official nnU-Net v2 only (not "nnU-Net-style"). No hand-built
    baseline, ensemble, cascade or second architecture.
  - Training: fold 0 of nnU-Net's 5-fold split only, with `nnUNetTrainer_100epochs`
    on `3d_fullres`. If a timed pilot (about 5 epochs) shows 100 epochs will not fit
    in about 14 GPU-hours, fall back to `3d_lowres` or 50 epochs and record it.
  - Preprocessing runs in a CPU-only Kaggle notebook (no GPU quota) and is saved as a
    dataset. A labeled subset of about 250 cases may be used if storage is tight.
  - Split: locked 15% test set, stratified by cohort proxy (cases 0-299 vs 400-588),
    tumor-size bin and cyst presence. Phase stays `unknown` (D-010).
  - Metrics: Dice and surface Dice over the three KiTS regions, computed with the
    official KiTS23 evaluator and its empty-mask rule, with bootstrap 95% CIs.
  - The training schedule, configuration and case count are stated in every result.
- **Reason:** The owner has limited compute and four projects to finish this month.
  Full nnU-Net (1000 epochs x 5 folds) would use several weeks of Kaggle GPU quota.
  The cuts remove GPU cost but keep the parts that make the result trustworthy: a
  locked test set, the official evaluator and confidence intervals. This approves
  the four questions in `reports/foundation/approach_review.md` §10 in lean form.

## D-013 — nnU-Net raw dataset format for SPEC 002

- **Date:** 2026-10-22
- **Decision:** Pin `nnunetv2==2.8.1`. Write `Dataset220_KiTS2023` in the format of
  nnU-Net's official KiTS23 conversion: region-based labels (`kidney=[1,2,3]`,
  `masses=[2,3]`, `tumor=2`, `regions_class_order=[1,3,2]`) with
  `NibabelIOWithReorient`. Only train and validation cases go into `imagesTr`;
  locked test images go to `imagesTs` with no labels. Fold 0 of a custom
  `splits_final.json` holds our train/validation split. Files are symlinked on Kaggle.
- **Reason:** The regions are the official KiTS evaluation classes, so training
  optimizes what is scored. Keeping test cases out of `imagesTr` stops them from
  influencing nnU-Net's fingerprint and plans. The pin makes the plans repeatable.

## D-014 — Evaluation details for SPEC 004–005

- **Date:** 2026-10-24
- **Decision:**
  - Post-processing: nnU-Net's own `determine_postprocessing` on the fold-0
    validation predictions, applied unchanged to test. Post-processed predictions
    are the primary result; raw predictions are reported next to them.
  - HD95: the larger of the two directed 95th-percentile surface distances, in mm,
    using the voxel spacing; undefined (NaN, counted) when either mask is empty.
  - Geometry: our shape/affine check runs before the official evaluator, and our
    Dice must match the official Dice within 1e-3, or the run stops.
  - CIs: case bootstrap, 10 000 resamples, seed 42, only with at least 10 cases.
  - Case analysis (SPEC 005) is descriptive, with groups fixed before test results.
- **Reason:** These choices are fixed in writing before the test set is scored, so
  the one test evaluation cannot be steered. HD95 definitions differ between
  libraries; the symmetric max form is the common one (MONAI, KiTS literature).

## D-015 — Stage KiTS23 with three download notebooks

- **Date:** 2026-10-24
- **Decision:** Plan B of D-011. Three private CPU notebooks
  (`notebooks/00_stage_data_{1,2,3}.ipynb`, from `scripts/data/stage_kits23.py`)
  download contiguous image shards of about 14 GB each from the pinned URLs; shard 1
  also holds all 489 segmentations. Every file is checked for size and SHA-256 while
  it downloads. Later notebooks take the three notebook outputs as inputs, and
  `detect_roots` links the image folders into one.
- **Reason:** Everything runs through the Kaggle CLI, with no web-UI import and no
  local download. Kaggle saves about 20 GB of output per notebook, and the images
  are 42 GB.

## D-016 — Train in resumable Kaggle sessions

- **Date:** 2026-10-24
- **Decision:**
  - Train with `nnUNetTrainer_100epochs_kaggle`. It is identical to nnU-Net's
    `nnUNetTrainer_100epochs`, except it saves `checkpoint_latest.pth` every 5 epochs
    instead of every 50.
  - Each Kaggle session trains for at most 11.25 h, then stops. The next session
    attaches the previous output and resumes with `--c`.
  - GPU: T4. `torch.compile` off; 4 data-augmentation workers.
  - Run a 5-epoch pilot (`nnUNetTrainer_5epochs`) first.
- **Reason:** 100 epochs of 3d_fullres take longer than Kaggle's 12-hour session.
  With 50-epoch checkpoints, a stopped session could throw away hours of GPU time,
  and the weekly quota is only 30 h. The training recipe itself is unchanged.
  Recent PyTorch no longer supports the P100.

## D-017 — Preprocess in four shard notebooks; leave out two oversized training scans

- **Date:** 2026-10-25
- **Decision:**
  - `kits23-prepare-data` (notebook 01) verifies, splits and runs nnU-Net's
    fingerprint and planning only (`--no_pp`). It saves the plans, our
    `splits_final.json`, the reference labels (`gt_segmentations`) and a shard plan.
  - Four CPU notebooks `kits23-preprocess-1..4` (`notebooks/01b_preprocess_*.ipynb`,
    from `scripts/data/preprocess_shard.py`) each preprocess about a quarter of the
    train+val cases, split by resampled voxel count. Each case runs in its own
    process, 2 at a time, and a case that crashes is retried alone.
  - Training cases larger than 350 million voxels after resampling to the 3d_fullres
    spacing are left out of training and removed from fold 0 of `splits_final.json`.
    With KiTS23 this drops two whole-body scans (expected: `case_00223`, about 556 M,
    and `case_00412`, about 429 M; the median case is about 100 M). The run record
    lists the exact cases.
  - The training notebook links the prepare output and the four shard outputs into
    one preprocessed folder (`train.py`, `assemble_preprocessed`).
- **What does not change:** the locked 343/73/73 split and its fingerprint, the
  validation and test cases (no validation or test case is ever excluded), the nnU-Net
  plans and the training recipe.
- **Reason:** The first full run failed twice. nnU-Net's preprocessing worker died on
  `case_00223` (Kaggle's 34 GB of RAM ran out, with 2 workers and then with 1). Also,
  the measured size of the preprocessed data, about 1.1 bytes per voxel, puts the
  whole dataset at about 50 GB, while one notebook saves only about 20 GB.
  Leaving 2 of 343 training cases out costs far less than any change of
  configuration (for example 3d_lowres) would.
