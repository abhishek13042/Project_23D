# SPEC 001 — Learnings

## 1. Why case-level splitting matters

A 3D CT case creates many correlated slices and patches. A random slice split can
put nearly identical anatomy from one patient into both training and test data,

## 2. Why KiTS hierarchical evaluation classes matter

Kidney, tumor, and cyst have a nested relationship. A system can delineate the

## 3. Why spacing belongs in the contract

Voxel counts are not physical distances. Two boundaries with the same voxel error

## 4. Why nnU-Net is a reference rather than an automatic answer

nnU-Net demonstrates that preprocessing and training configuration are part of the

## 5. Why public test data is not automatically usable

The official KiTS23 test allocation has 110 cases, but the public workflow does not
provide their ground-truth masks for ordinary local scoring. The project must use a
locked internal test split for local evidence and must not imply official-test
performance.

## 6. Questions deferred to SPEC 002

- exact source file inventory after download;
- observed shape and spacing distributions;
- target model spacing;
- patch size and overlap;
- number of empty masks or unusual label cases;
- exact stratification feasibility.

These are data-pipeline measurements, not reasons to invent foundation facts.
