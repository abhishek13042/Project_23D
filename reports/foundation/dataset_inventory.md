# Dataset Inventory

## Primary: KiTS23

| Field | Finding | Source |
|---|---|---|
| Official source | KiTS23 challenge homepage and official repository | <https://kits-challenge.org/kits23/>; <https://github.com/neheller/kits23> |
| Version | `0.1.4` | Official repository README |
| Access | `kits23_download_data`; imaging from public Hugging Face mirror; labels from official repository | Official repository README |
| Approval | No ordinary research application described; non-commercial use applies | Official repository README |
| License | CC BY-NC-SA 4.0 data; MIT code | Official repository README and dataset card |
| Subjects/volumes | 599 cases: 489 training, 110 test | Official challenge homepage |
| Modality | Contrast-enhanced preoperative CT | Official challenge homepage |
| Labels | Background, kidney, tumor, cyst | Official challenge homepage and `labels.py` |
| Format | NIfTI `.nii.gz`; official evaluator uses `segmentation.nii.gz` | Official repository/evaluator |
| Subject IDs | Anonymized `case_XXXXX` | Official repository organization |
| Metadata | Per-case geometry/spacing from NIfTI header; acquisition phase documented where available | Official challenge description; exact values deferred to manifest |
| Official split | 489 training, 110 challenge test | Official challenge homepage |
| Local split | 70/15/15 case-level split of labeled training cases, seed 42 | Project decision D-004 |
| Leakage risk | Historical KiTS19/KiTS21/KNIGHT case overlap; adjacent slices/patches are dependent | Official KiTS23 homepage |
| Suitability | Direct fit for focused renal 3D multiclass segmentation | Foundation decision |

## Alternatives

### KiTS19

The KiTS19 paper reports 300 patient cases and 210 public training cases with
contrast-enhanced CT semantic segmentations. It is the historical predecessor of
KiTS23 and is useful for research context. It is not selected because it is smaller

### AMOS22

The official Grand Challenge page and Zenodo record report 500 CT scans, 100 MRI
scans, and voxel-level annotations for 15 abdominal organs. Zenodo marks the
record open under CC BY 4.0 and publishes a 24,234,336,519-byte archive. It is
not selected because its multi-organ/multi-modality scope is broader than the
focused renal problem and would add unnecessary data and ontology complexity.

### MSD Task 03 — Liver

The Medical Segmentation Decathlon paper and source site document 3D medical
segmentation tasks, including liver segmentation. It was screened out because the
target anatomy does not match the renal project and current task-specific access
and license details were not sufficiently verified in this audit.

### BTCV / Beyond the Cranial Vault

This is a recognized multi-organ abdominal CT benchmark, but its Synapse access
workflow adds unnecessary access friction and its task scope is broader than the
selected renal problem.

## Dataset decision

KiTS23 is selected. No data has been downloaded in SPEC 001.
