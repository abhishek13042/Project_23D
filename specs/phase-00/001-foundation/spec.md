# SPEC 001 — Foundation & Feasibility

- **Status:** VERIFIED LOCALLY — REMOTE SYNC PENDING
- **Phase:** 0 — Foundation
- **Project:** Project_23D — Renal CT 3D Segmentation
- **Date:** 2026-10-08 (documentation repaired and dataset availability re-checked 2026-10-21)

## 1. Purpose

Lock the project definition, primary dataset, volumetric data contract, leakage
policy, evaluation protocol, research basis, compute strategy, and reproducibility
requirements before implementation begins.

## 2. Scope

This specification covers foundation decisions for semantic segmentation of kidney,
renal tumor, and renal cyst regions in contrast-enhanced CT volumes.

It does not implement data ingestion, preprocessing code, model code, training,
evaluation code, APIs, frontend, or deployment.

## 3. Project definition

### 3.1 Task

Input: one contrast-enhanced preoperative CT volume from a KiTS23 case.
Output: one mutually exclusive voxel label volume.

### 3.2 Modality

Contrast-enhanced computed tomography. KiTS23 includes corticomedullary and
nephrogenic phases; phase metadata must be retained and reported.

### 3.3 Target labels

```text
0 background
1 kidney
2 tumor
3 cyst
```

This is multiclass semantic segmentation, not multilabel segmentation.

### 3.4 Unit of independence

The anonymized KiTS case identifier `case_XXXXX` is the unit of independence. All
slices, patches, masks, predictions, and derived files from one case remain in one
partition.

### 3.5 Evaluation population

The labeled KiTS23 training allocation contains 489 cases. These are split into
train, validation, and internal test partitions at the case level. The official
110-case challenge test allocation is not used for local metric claims because
ground-truth labels are not ordinarily included in the public release.

### 3.6 Intended use

Research benchmarking and automated volumetric delineation. The project is not a
diagnostic, treatment-planning, or clinically validated system.

## 4. Dataset decision

KiTS23 official dataset version `0.1.4` is primary.

Official sources:

- <https://kits-challenge.org/kits23/>
- <https://github.com/neheller/kits23>
- <https://huggingface.co/datasets/neheller/KiTS-Challenge-Imaging>
- KiTS21 challenge paper, cited by the official KiTS23 repository:
  <https://arxiv.org/abs/2307.01984>

The official sources report 599 cases, with 489 training cases and 110 test cases.
The data license is CC BY-NC-SA 4.0. The official repository code is MIT. The
project is non-commercial and will include attribution and license notices.

Alternatives considered: KiTS19, AMOS22, MSD Task 03 Liver, and BTCV. They are
documented in `docs/datasets.md`; none is selected as primary.

## 5. Data contract

### 5.1 Volume contract

Each volume record must include:

- `case_id: str`
- `image_path: path to NIfTI .nii.gz`
- `source_shape: tuple[int, int, int]`
- `source_spacing_mm: tuple[float, float, float]`
- `source_affine: 4x4 matrix`
- `source_orientation`
- `source_dtype`
- `intensity_scaling_metadata`
- `acquisition_phase: corticomedullary | nephrogenic | unknown`
- `dataset_version`
- `file_sha256`

CT intensities are read using the file’s physical-value scaling metadata. The raw
dtype and scaling are preserved in the manifest. Intensity clipping/windowing is a
preprocessing decision made in SPEC 002 from measured intensity distributions, not
a property of the source data.

### 5.2 Mask contract

Each mask record must include:

- same `case_id` as the volume;
- same source shape;
- matching affine/geometry within the declared tolerance;
- integer labels in `{0, 1, 2, 3}`;
- `mask_path` to NIfTI `.nii.gz`;
- mask file hash;
- voxel counts per label.

Mask transforms use nearest-neighbor interpolation. Image transforms use a declared
continuous interpolation method.

### 5.3 Canonical model space

The loader will expose a canonical orientation and tensor order for model input,
while preserving source geometry for export. The exact target spacing and patch
size are intentionally selected after the verified data manifest in SPEC 002; the
method and metadata requirements are locked here.

### 5.4 Missing/corrupt data

- missing image or mask: reject the case and report it;
- unreadable NIfTI/header: quarantine and report it;
- shape or affine mismatch: reject before training;
- unknown label value: reject and report;
- duplicate `case_id`: fail the manifest gate;
- empty mask: retain only if the official case is valid and record the fact;
- missing phase metadata: keep as unknown and report, never guess silently. The
  official `kits23.json` has no phase field (verified 2026-10-21, D-010).

## 6. Split and leakage policy

- Use one fixed seed: `42`.
- Split labeled cases 70% train, 15% validation, and 15% internal test.
- Group all derived samples by `case_id`.
- Never split slices, patches, augmented copies, or adjacent studies independently.
- Use file hashes and case IDs to detect duplicate or repeated cases.
- Do not merge KiTS19/KiTS21 cases into the primary KiTS23 dataset.
- Stratify where feasible by acquisition phase and presence of tumor/cyst labels.
  Phase is not available in the official metadata, so phase stratification is
  currently infeasible (D-010).
- Freeze and hash the generated split manifest before training.
- If a future external dataset is used, it receives a separate evaluation role and
  is never merged into the internal test result.

## 7. Evaluation protocol

### Primary

Per-case macro Dice across official KiTS hierarchical evaluation classes:

- `kidney_and_mass = {1, 2, 3}`
- `mass = {2, 3}`
- `tumor = {2}`

### Secondary

- official surface Dice for the three HECs;
- per-class Dice and IoU for kidney, tumor, and cyst;
- precision and recall/sensitivity;
- specificity where meaningful;
- HD95 in millimetres;
- volume error;
- per-case distributions and worst-case analysis.

### Empty masks

Both empty → perfect overlap score. Exactly one empty → zero overlap score. Both
non-empty → standard formula. Boundary metrics include explicit undefined/empty
handling and denominators.

## 8. Research basis

The project uses:

- U-Net for the encoder-decoder and skip-connection baseline concept;
- 3D U-Net for volumetric operations and patch/memory reasoning;
- V-Net for volumetric Dice-aware loss reasoning;
- nnU-Net for the strong self-configuring reference;
- KiTS19/KiTS21/KiTS23 papers for renal labels, challenge design, and HEC metrics;
- Swin UNETR as a reviewed modern method, not an initial implementation target.

Full research notes are in `docs/research.md` and
`reports/foundation/research_review.md`.

## 9. Compute and reproducibility

### Local responsibilities

- data/metadata inspection after SPEC 002 begins;
- loader and geometry validation;
- visualization;
- unit/integration tests;
- model initialization;
- forward, loss, backward, checkpoint, and inference smoke tests;
- tiny end-to-end tests.

### Kaggle responsibilities

- baseline training;
- strong-reference training;
- controlled experiments and ablations;
- final model selection;
- full evaluation and benchmark runs.

Plan for a variable 16-GB-class GPU environment. Patch-based 3D training is the
default feasibility strategy because CT volume shapes and GPU memory are variable.
Batch size is a configuration value and may be one for full-resolution patches.
AMP/fp16 is allowed on CUDA after numerical smoke tests; the policy must record
whether AMP was enabled and any metric tolerance.

Every run records dataset/split fingerprints, code version, config hash, seed,
environment, GPU, runtime, checkpoint hash, metrics, and artifacts. Fixed seeds do
not guarantee bitwise-identical CUDA weights; reproducibility is defined by the
recorded protocol and acceptable metric tolerance.

## 10. Future experiment structure

No experiments run in SPEC 001. Future experiments require:

- hypothesis;
- baseline;
- single principal variable;
- dataset/split;
- configuration;
- metrics;
- result;
- interpretation;
- conclusion.

Initial research questions are recorded in `docs/experiments.md`.

## 11. Requirements

- `S001-REQ-001`: The segmentation task, modality, classes, and intended use are defined.
- `S001-REQ-002`: The primary dataset and access/license conditions are verified.
- `S001-REQ-003`: Volume, mask, geometry, intensity, and identity contracts are defined.
- `S001-REQ-004`: Case-level splitting and leakage prevention are mandatory.
- `S001-REQ-005`: Primary and secondary metrics, including empty-mask behavior, are defined.
- `S001-REQ-006`: Research references justify the baseline and strong-reference choices.
- `S001-REQ-007`: Local/Kaggle compute responsibilities are separated.
- `S001-REQ-008`: Reproducibility and future experiment fields are mandatory.
- `S001-REQ-009`: Limitations and unsupported clinical claims are documented.

## 12. Tests and verification

Foundation verification is documentation and source audit only:

- official source URLs are recorded;
- dataset counts and labels are traceable to official sources;
- no unsupported dataset statistic is used;
- required data-contract fields exist;
- split policy prohibits slice-level leakage;
- metric edge cases are written;
- compute and experiment fields are complete;
- no code or data pipeline is started.

## 13. Acceptance criteria

- project/task clearly defined;
- KiTS23 verified and selected;
- access and usage terms recorded;
- labels/classes verified;
- data contract defined;
- case-level split defined;
- leakage controls defined;
- metrics defined;
- research basis documented;
- local/Kaggle strategy defined;
- reproducibility defined;
- future experiment structure defined;
- limitations documented;
- no invented results or unsupported claims;
- no content blocker prevents SPEC 002.

## 14. Evidence

- `docs/project-overview.md`
- `docs/architecture.md`
- `docs/datasets.md`
- `docs/research.md`
- `docs/evaluation.md`
- `docs/experiments.md`
- `docs/limitations.md`
- `docs/development-status.md`
- `docs/decisions.md`
- foundation reports under `reports/foundation/`

## 15. Non-goals

- dataset download or ingestion;
- preprocessing implementation;
- model implementation;
- training;
- API/frontend/deployment;
- clinical validation;
- external data mixing.

## 16. Quality-gate result

Content gate: **PASS**.
Local Git gate: **PASS after local commit**.
Remote synchronization: **PENDING** because no intended remote URL or GitHub CLI is
available in the environment.
