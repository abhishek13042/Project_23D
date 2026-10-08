# Project Overview

## Status

SPEC 001 — Foundation & Feasibility is verified locally. No data pipeline,
training, API, frontend, or deployment implementation has started.

## Problem definition

The project performs **3D semantic segmentation of kidneys, renal tumors, and renal
cysts in contrast-enhanced CT volumes**.

Given one preoperative contrast-enhanced CT volume, the system produces a voxel
label for:

```text
0 = background
1 = kidney
2 = tumor
3 = cyst
```

This is a **multiclass semantic segmentation** task. Tumor and cyst are mutually
exclusive semantic labels in the stored mask; hierarchical evaluation regions are
derived for comparison with the KiTS protocol.

## Intended use

This is a research and engineering prototype for automated volumetric delineation
and quantitative segmentation evaluation. It may support research into renal
anatomy/tumor morphometry and model benchmarking.

It is not a diagnostic system, treatment-planning system, or clinically validated
decision tool. No clinical claim will be made from segmentation metrics alone.

## Primary dataset

KiTS23, official dataset version `0.1.4`, is the primary dataset. The official
challenge reports 599 cases: 489 training cases and 110 test cases. The local
project uses the labeled training allocation to create a reproducible internal
train/validation/test split. Official challenge test labels are not used for local
model selection because they are not publicly available through the normal data
release.

## Evaluation population

The unit of independence is the anonymized KiTS case identifier. A case is treated
as one subject/study unit. No slice, patch, or adjacent-volume split is allowed.

The internal evaluation population is a locked, subject-disjoint holdout created
from the 489 labeled training cases. The official 110-case challenge test set is
kept outside local metric claims unless official ground truth becomes legitimately
available.

## System boundary

```text
KiTS23 NIfTI CT + segmentation
→ subject-level split
→ spatial/intensity preprocessing
→ 3D segmentation model
→ whole-volume or patch-based inference
→ NIfTI mask with source geometry
→ overlap, boundary, per-case, and failure analysis
```

## Non-goals

- diagnosis or malignancy classification
- treatment recommendation
- clinical deployment
- prediction of patient outcomes
- radiomics or nephrometry claims without a separate validated contract
- mixing KiTS19/KiTS21 cases into the KiTS23 primary evaluation
- random slice-level splitting
