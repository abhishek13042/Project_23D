# Foundation Approach Review

**Date:** 2026-10-21
**Scope:** Every foundation document, checked against the published literature, the
official KiTS23 code, and current Kaggle limits. This review proposes changes. It
does not lock them; decisions are only made in `docs/decisions.md`.

## 1. Verdict

The foundation is sound in its fundamentals: the task, labels, case-level split,
hierarchical evaluation, and baseline/reference framing all match how the field
works on KiTS. The literature supports the core choice of a U-Net family model inside
the nnU-Net framework over transformers.

The main gaps are practical rather than conceptual:

1. **Compute budget is not quantified.** nnU-Net training cost on a Kaggle GPU is
   close to the whole weekly quota per fold (section 4).
2. **Data staging on Kaggle was undefined.** It is now resolved by D-011 (section 3).
3. **One validation split is weaker than the field's 5-fold practice**, and the
   internal test set is small (section 5).
4. **"nnU-Net-style" is ambiguous.** Use the official nnU-Net v2, not a
   reimplementation (section 6).
5. **Boundary-metric conventions differ from the official evaluator** (section 7).

## 2. Literature basis

| Source | Finding that matters here |
|---|---|
| Isensee et al., nnU-Net, *Nature Methods* 2021 | Preprocessing, spacing, patch size, and training schedule are part of the method. For CT, intensities are clipped to the 0.5–99.5 percentiles of foreground voxels, then z-scored with foreground statistics. |
| Isensee et al., *nnU-Net Revisited*, MICCAI 2024 ([arXiv 2404.09556](https://arxiv.org/abs/2404.09556)) | On KiTS23 (5-fold CV, n=489, hierarchical regions), Dice is 86.04 for the original nnU-Net, 86.79 for ResEnc M, 88.17 for ResEnc L, and 88.67 for ResEnc XL. SwinUNETR-type models score far lower. KiTS has the highest inter-method spread of six datasets, so it separates methods well. The paper recommends 5-fold cross-validation and a separate test pool. |
| Same paper, Table 1 (A100 40 GB) | Original nnU-Net: 7.7 GB VRAM, about 9 GPU-hours. ResEnc M: 9.1 GB, about 12 h. ResEnc L: 22.7 GB, about 35 h. |
| Heller et al., KiTS21 report ([arXiv 2307.01984](https://arxiv.org/abs/2307.01984)) | This is the source of the hierarchical evaluation classes and surface Dice. Its title confirms that KiTS21 cases are corticomedullary-phase. |
| Myronenko et al., KiTS23 winner ([arXiv 2310.04110](https://arxiv.org/abs/2310.04110)) | Auto3DSeg with SegResNet and DiNTS: 15-model ensemble, region-based sigmoid outputs, kidney ROI crop, 0.78 mm spacing, 8×A40 GPUs. 5-fold CV Dice was about 0.889, but the hidden test set gave 0.835 Dice and 0.723 surface Dice. |
| Uhm et al., KiTS23 2nd place ([arXiv 2312.05528](https://arxiv.org/abs/2312.05528)) | nnU-Net-style 3D U-Net. A low-resolution + full-resolution cascade and post-processing raised validation tumor Dice from about 0.80 to 0.826. Region-based training alone did not help. Test result: 0.820 Dice and 0.712 surface Dice. |
| Domain-shift study ([arXiv 2309.02001](https://arxiv.org/abs/2309.02001)) | Adding external data (KiPA22) needed HU harmonization. Cyst was the weakest class, with many false positives and cyst/tumor confusion. |
| Maier-Hein et al., *Metrics Reloaded*, *Nature Methods* 2024 | For segmentation, pair an overlap metric (Dice) with a boundary metric (normalized surface Dice), and report per-case distributions. This supports the current metric plan. |

Two lessons apply directly:

- **Expect a gap between cross-validation and an unseen test set.** The top teams
  dropped about 0.05–0.07 Dice from CV to the hidden test set. The internal test set
  here is drawn from the same distribution as training, so it will be *optimistic*.
  `docs/limitations.md` already says this, and the final report should say it again.
- **Tumor and cyst drive the ranking.** Kidney-and-mass Dice saturates (about 0.95–0.98).
  The meaningful differences are in the mass and tumor regions and in the cyst class.

## 3. Data acquisition: Kaggle only (resolved, D-011)

The local machine does not need the 42 GB download.

- Verified on 2026-10-21: the Hugging Face mirror holds **both** the 489 images and
  the 489 official segmentations. Mirror segmentations are byte-identical to
  `dataset/case_XXXXX/segmentation.nii.gz` in the official GitHub repository
  (SHA-256 matched on 4 sampled cases). The mirror API also publishes a SHA-256
  checksum for every file.
- `data/sources/kits23_v0.1.4_files.tsv` lists all 978 files with size, SHA-256, and
  a URL **pinned to mirror commit `65f1f295873a326230153c7e1de0c7dba10f0b29`**, so a
  later change to the mirror cannot silently change the data.
- Kaggle's documented limits are 200 GB per dataset and 200 GB of private
  datasets. Its **Remote Files** connector downloads files directly from the source server
  into Kaggle's storage, so no local bandwidth is used.

**Plan A, Remote Files import.** Create a private Kaggle dataset by pasting
`kits23_v0.1.4_segmentation_urls.txt` (0.14 GB). Then create a second private dataset
from `kits23_v0.1.4_image_urls.txt` (42.1 GB). Whether the connector accepts 489 URLs
in one go is unverified. If it does not, split the list into several datasets of
about 100 cases each.

**Plan B, notebook shards.** If the connector fails, run a Kaggle notebook with
internet on that downloads about 160 cases per run into `/kaggle/working` (20 GB
saved-output limit per notebook). Save each run's output as a dataset and attach all
shards. The checksum manifest verifies every file in either plan.

**Local smoke data:** download only the 5 smallest cases (11–15 MB each, about 70 MB
total; for example `case_00546` and `case_00061`). That is enough for loader,
geometry, and forward/backward tests.

**Licensing:** CC BY-NC-SA 4.0 permits non-commercial redistribution with attribution
under the same license. Keep the Kaggle datasets **private**. If one is ever made
public, set the license to CC BY-NC-SA 4.0 and credit the KiTS23 organizers.

## 4. Compute budget: the biggest open risk

Kaggle documents 12-hour GPU sessions, 1× P100 (16 GB) or 2× T4, 4 CPU cores,
29 GB RAM, and 20 GB of saved output. The weekly GPU quota is not documented. Users
commonly report about 30 hours, and the real figure appears on your Kaggle account
settings page.

Rough estimate: the original nnU-Net needs about 9 h on an A100. A P100 has no tensor
cores and is typically several times slower than an A100 for this workload, so one
full 1000-epoch fold is plausibly **30–50 GPU-hours**. That is one or more weeks of
quota for a single fold. This is an estimate, and it must be measured with a
timed short run before planning.

Proposed policy for SPEC 003:

- Use nnU-Net v2's shipped shorter schedules (`nnUNetTrainer_250epochs`, or 100 for
  ablations) and state the schedule in every result. Revisited-paper numbers come from
  1000 epochs and are not directly comparable.
- Train on 1 fold with checkpoint/resume across 12-hour sessions; nnU-Net resumes
  natively with `--c`.
- Prefer **T4 for AMP**, because T4 has tensor cores and P100 does not, so fp16 speeds
  up P100 much less. Benchmark both once.
- Data loading is CPU-bound with only 4 cores. Preprocess once into nnU-Net's format
  and store it as a Kaggle dataset rather than decompressing `.nii.gz` every session.
  The preprocessed full-resolution data may exceed 20 GB, so plan to shard it (as in
  Plan B) or crop to the kidney region.
- ResEnc M (9.1 GB) fits a 16 GB GPU. ResEnc L (22.7 GB) does not fit one Kaggle GPU,
  so the attainable reference is the original nnU-Net or ResEnc M.

## 5. Split and validation design

**Current:** one 70/15/15 split (about 342/73/74 cases), stratified by phase and
tumor/cyst presence.

**Issues:**

- Phase stratification is impossible as written (D-010). However, a documented proxy
  exists: KiTS21 cases `case_00000`–`case_00299` are corticomedullary per the KiTS21
  paper title and the KiTS23 homepage ("previously all cases were in late arterial").
  Cases `case_00400`–`case_00588` (189 cases) are the new, mixed-phase cohort.
  **Stratifying by cohort (≤299 vs ≥400)** keeps the new-phase cases balanced
  across partitions without guessing any individual case's phase.
- `kits23.json` offers further stratifiers: `malignant` (439 true, 43 false, 7 null)
  and `radiographic_size` (median 4.0; 252 of 482 at 4 or below). Size directly
  affects tumor Dice. Do **not** use clinical fields as model inputs.
- A single validation split of about 73 cases gives noisy model selection, and
  nnU-Net Revisited specifically recommends 5-fold CV. Full 5-fold CV is not
  affordable on Kaggle (section 4).

**Proposal:** keep the locked internal test set (15%, about 74 cases), stratified by
cohort, size bin, and cyst presence. Use nnU-Net's own 5-fold split on the remaining
cases, but **train fold 0 only** for routine work. Run more folds only for the
final model if quota allows. Reporting test results with bootstrap 95% CIs is
already planned and essential with n ≈ 74. A tumor-Dice CI will likely be several
points wide, so small differences between models are not claims.

## 6. Model strategy

| Current wording | Assessment | Proposal |
|---|---|---|
| "compact 3D U-Net baseline" | Good. It shows what the auto-configuration buys. | Use the same preprocessed data and patch sampler, so only the model and training configuration differ (Revisited R1, which says to isolate the variable). |
| "nnU-Net-style reference … or official nnU-Net if adopted" | Ambiguous. A reimplementation risks a weak reference, which Revisited identifies as the field's main failure mode. | **Use official nnU-Net v2** (`3d_fullres`, optionally ResEnc M). Record the plans file and its hash. |
| V-Net, Swin UNETR deferred | Supported. Transformers underperform on KiTS23 in Revisited. | Keep deferred. |

Ideas the evidence supports, each as one future experiment under the existing rules:

- **Region-based training** on the three hierarchical regions, as used by the winner
  and supported natively by nnU-Net v2. Evidence is mixed: the 2nd-place team saw no
  gain.
- **Low-resolution + full-resolution cascade or fusion.** This was the 2nd-place team's
  main gain for tumors, but it costs extra compute.
- **Post-processing** (small-component removal, tumor/cyst rim correction). This is
  existing E-004. Tune it on validation only.

## 7. Evaluation

What is right: case-level macro Dice over the official hierarchical classes,
per-class reporting, denominators, and qualitative failure analysis.

Changes to consider:

1. **Make surface Dice co-primary.** The official KiTS23 ranking averages Dice *and*
   surface Dice. Reporting Dice alone as primary is not KiTS-comparable.
2. **Use the official evaluator** (`kits23_compute_metrics`, version 0.1.4) for the
   headline numbers instead of re-implementing them. Use custom code only for the
   secondary metrics.
3. **Align the empty-mask rule.** The official `metrics.py` sets surface Dice = 1 when
   both masks are empty and 0 when exactly one is empty. `docs/evaluation.md`
   currently says boundary metrics are "undefined/omitted" when both are empty.
   Use the official rule for surface Dice and keep the undefined rule only for HD95,
   where a distance genuinely does not exist.
4. Report the **cyst class** prominently. Prior work shows it is the weakest and most
   confused class.
5. State the expected range so results are interpretable. Published 5-fold CV for the
   original nnU-Net on KiTS23 is about 0.86 Dice. A short-schedule Kaggle run should
   be expected to land below that.

## 8. Experiment plan (E-001 to E-005)

- E-001 (baseline vs reference) is the right first experiment.
- E-005 is titled "Error-slice behavior" but describes case-level stratified analysis.
  Rename it "Performance by case characteristics". It is an *analysis*, not an
  experiment with one changed variable.
- With one seed per configuration and n ≈ 74 test cases, differences need paired
  per-case comparison (for example, a paired bootstrap of per-case Dice). Write this
  rule into the experiment template.
- Add one budget field to every run: GPU type, GPU-hours, epochs, and schedule name.

## 9. Documentation consistency issues found

| Location | Issue | Status |
|---|---|---|
| 11 files | About 20 sentences cut off mid-line | Fixed 2026-10-21 |
| datasets, spec, research review | arXiv 2307.01984 mislabelled as the KiTS23 paper | Fixed |
| spec §6, evaluation.md | Phase stratification is infeasible | Fixed (D-010, D-012) |
| evaluation.md | Empty-mask rule for boundary metrics differs from the official one | Fixed (D-012) |
| project-overview / architecture | "nnU-Net-style" is ambiguous | Fixed (D-012) |
| experiments.md | E-005 title does not match its content | Fixed (D-012) |
| spec §9 | No compute budget figures | Fixed (D-012) |

## 10. Decisions needed from the project owner

1. Adopt **official nnU-Net v2** as the reference (instead of "nnU-Net-style")?
2. Make **surface Dice co-primary** and adopt the official empty-mask convention?
3. Adopt **cohort + size + cyst stratification** with **nnU-Net 5-fold splits,
   fold 0 by default**, for the non-test cases?
4. Accept a **shortened training schedule** (for example 250 epochs), with the
   schedule recorded in every result?

**Resolved 2026-10-21 (D-012):** all four were approved in a lean, compute-limited
form: official nnU-Net v2 only, Dice plus surface Dice via the official evaluator,
stratified locked test set with fold 0 only, and `nnUNetTrainer_100epochs`
(`3d_lowres` fallback). See `docs/decisions.md` D-012.
