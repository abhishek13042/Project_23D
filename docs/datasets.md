# Dataset Research and Decision

## Primary decision

**Selected:** KiTS23, official repository version `0.1.4`.

### Official source and access

- Challenge homepage: <https://kits23.kits-challenge.org/> (the older
  <https://kits-challenge.org/kits23/> address serves the same page)
- Official repository: <https://github.com/neheller/kits23>
- Public imaging mirror used by the official downloader:
  <https://huggingface.co/datasets/neheller/KiTS-Challenge-Imaging>
- Paper cited by the official repository: the **KiTS21** challenge report,
  <https://arxiv.org/abs/2307.01984>. The repository does not link a separate
  KiTS23 overview paper.

The official repository documents installation and the `kits23_download_data`
command. The repository states that imaging is fetched from the public Hugging
Face dataset and segmentations are maintained in the official repository. No
application or research-registration workflow is required for ordinary academic
use according to the official README; the data license remains non-commercial.

### Verified dataset facts

| Field | Verified value |
|---|---|
| Modality | Contrast-enhanced preoperative CT |
| Cohort | KiTS23 renal malignancy cohort |
| Cases | 599 total; 489 training; 110 challenge test |
| Labels | Kidney, tumor, cyst, plus background |
| Label codes | 0 background, 1 kidney, 2 tumor, 3 cyst |
| Storage | 3D NIfTI files using `.nii.gz`; official ground-truth filename is `segmentation.nii.gz` |
| Metadata | Shape, spacing, direction/orientation, and affine/geometry are read from each volume header; `dataset/kits23.json` holds per-case clinical fields but **no contrast-phase field** |
| Subject key | Anonymized `case_XXXXX` identifier |
| Test labels | Not included in the ordinary public training release |
| License | CC BY-NC-SA 4.0 for data; official repository code is MIT |
| Access | Public repository plus public Hugging Face imaging mirror |
| Approval | No separate application required for ordinary non-commercial research use per official README |
| Research use | Official MICCAI challenge, benchmark code, challenge reports, and nnU-Net-related research |

The official site describes the 489/110 allocation and the target classes. The
official evaluation code defines the KiTS hierarchical regions and reads NIfTI
segmentation files. Per-case spacing will be measured from headers during SPEC 002;
no single dataset-wide spacing value is invented here.

### Dataset organization

The official repository organizes cases as `case_XXXXX`. Imaging is downloaded
from the public imaging mirror; segmentation files are published through the
official KiTS23 repository. The exact archive/file inventory will be verified by
the SPEC 002 acquisition and manifest task without changing this foundation
decision.

### Leakage policy for KiTS23

The KiTS23 page records overlap with earlier KiTS19, KiTS21, and KNIGHT case
allocations. The project therefore:

- uses KiTS23 case identifiers as the grouping key;
- does not merge historical KiTS releases into the primary dataset;
- does not split slices or patches across partitions;
- fingerprints case IDs and file hashes;
- reports any duplicate case identifier before data use.

## Availability check — 2026-10-21

Every official source was queried live. All of them responded, and nothing is gated.

| Item | Result |
|---|---|
| KiTS23 homepage | Reachable (HTTP 200); still reports 599 cases, 489 training and 110 test |
| Official repository `neheller/kits23` | Reachable, not archived, MIT license, `setup.py` version `0.1.4`, last push 2026-05-13 |
| Download entrypoint | `kits23_download_data`. It fetches `images/case_XXXXX.nii.gz` from the Hugging Face mirror into `dataset/case_XXXXX/imaging.nii.gz` |
| Hugging Face mirror | Public, **not gated**, license `cc-by-nc-sa-4.0`, last modified 2026-05-13 |
| Imaging files | 489 files under `images/`, 42.12 GB total |
| Segmentation files | 489 `segmentation.nii.gz` in the official repository, plus 489 files (0.14 GB) under `segmentations/` on the mirror |
| Extra mirror content | `interpolated/` has 300 files (52.58 GB). The official downloader does not use it, and neither will this project |
| Case IDs | 489 unique IDs from `case_00000` to `case_00588`. The numbering is not contiguous; the gaps are cases outside the public training release |
| Per-case annotations | `instances/` holds individual annotator masks. `segmentation.nii.gz` is the official reference |
| Label aggregation | The official order is kidney, then cyst, then tumor, so tumor overwrites cyst and kidney where they overlap |
| HEC surface-Dice tolerances | kidney_and_mass 1.0331 mm, mass 1.1329 mm, tumor 1.1498 mm (`kits23/configuration/labels.py`) |
| Contrast phase | Not present in `kits23.json`; see decision D-010 |

**Storage implication:** a full download of imaging and labels needs about
42.3 GB before any preprocessed copies. Under D-011 the full release lives only on
Kaggle as private datasets imported from pinned mirror URLs. Kaggle allows 200 GB
per dataset and 200 GB of private datasets in total. Notebooks save at most 20 GB of
output to `/kaggle/working`, so preprocessed data may need sharding. The machine-
readable source list (978 files, sizes, SHA-256, pinned URLs) is
`data/sources/kits23_v0.1.4_files.tsv`.

The mirror's `segmentations/` files are byte-identical to the official GitHub
`segmentation.nii.gz` files (SHA-256 compared on `case_00000`, `case_00123`,
`case_00450`, `case_00588`).

## Alternatives considered

| Dataset | Access and usage | Subjects/volumes and labels | Main limitation | Decision |
|---|---|---|---|---|
| **KiTS19** | Public KiTS challenge family; non-commercial data terms | Official paper reports 300 kidney-tumor patients; 210 public training cases; CT semantic segmentations | Smaller and overlaps with KiTS23 case history | Rejected as primary; useful historical reference only |
| **AMOS22** | Open Zenodo record `10.5281/zenodo.7155725` (re-verified open on 2026-10-21); CC BY 4.0; 24.2 GB archive; challenge page historically used registration for competition access | 500 CT and 100 MRI scans; voxel-level labels for 15 abdominal organs | Broad multi-organ/multi-modality scope is unnecessary for the focused renal project; archive is much larger | Rejected as primary; possible external generalization source later |
| **MSD Task 03 — Liver** | Public; the MSD site states CC BY-SA 4.0 and the `Task03_Liver.tar` mirror responded with a 28.9 GB archive on 2026-10-21 | 3D liver/tumor segmentation task; exact source-level count and metadata were not used without current manifest verification | Wrong anatomy for a renal project and weaker direct fit | Screened out |
| **BTCV / Beyond the Cranial Vault** | Synapse-based access and account workflow | Multi-organ abdominal CT benchmark | Access friction and broader task than required | Screened out |

## Selection rationale

KiTS23 is the strongest fit because it aligns with the renal 3D scope, provides
machine-readable masks and a clear class ontology, has hundreds of labeled cases,
has an official evaluator, and is publicly accessible without waiting for a
dataset application. Its non-commercial license is compatible with a portfolio
research project but must be preserved in all project documentation.
