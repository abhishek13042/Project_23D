# Decision Log

## D-001 — Use KiTS23 as the primary dataset

**Date:** 2026-10-08
**Decision:** Use KiTS23 v0.1.4 for the primary renal segmentation project.
**Reason:** It matches the renal 3D task, provides voxel labels and an official
evaluator, has 489 labeled training cases, and is publicly accessible with clear

## D-002 — Define the task as multiclass semantic segmentation

**Decision:** Predict mutually exclusive labels 0 background, 1 kidney, 2 tumor,
3 cyst.
**Reason:** This matches the official KiTS23 label ontology.

## D-003 — Treat the case ID as the unit of independence

**Decision:** Split by `case_XXXXX`; never split slices or patches.
**Reason:** A 3D scan and all derived samples must remain in one partition.

## D-004 — Create an internal test set from labeled cases

**Decision:** Use a reproducible 70/15/15 train/validation/internal-test split of
the 489 labeled cases.
**Reason:** Official challenge test labels are not ordinarily available for local

## D-005 — Use KiTS hierarchical evaluation classes

**Decision:** Primary evaluation includes kidney-and-masses, mass, and tumor HECs.
**Reason:** The official evaluator recognizes nested renal structures and avoids

## D-006 — Keep the model comparison small

**Decision:** Compare a compact 3D U-Net baseline with an nnU-Net-style reference.
**Reason:** This provides a meaningful baseline/reference comparison without an

## D-007 — Use the same code path locally and on Kaggle

**Decision:** Local mode is for smoke testing and Kaggle mode is for serious
**Reason:** This prevents environment-specific implementations and reduces wasted

## D-008 — Do not commit data, checkpoints, or secrets

**Decision:** Use `.gitignore` rules for raw/derived data, model weights, generated
**Reason:** Dataset licensing, repository size, and secret safety.

## D-009 — No remote push without an intended remote URL

**Decision:** Do not fabricate or guess a GitHub remote.
**Reason:** The repository has no configured remote and the intended destination
