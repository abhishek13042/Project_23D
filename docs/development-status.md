# Development Status

## Current status

**SPEC 001 — Foundation & Feasibility:** verified locally
**SPEC 002 — Volume Data Pipeline:** not started
**Model training:** not started
**API/frontend/deployment:** not started

## Completed foundation decisions

- project task: renal 3D semantic segmentation
- modality: contrast-enhanced CT
- primary dataset: KiTS23 v0.1.4
- classes: background, kidney, tumor, cyst
- independence unit: anonymized case ID
- split policy: subject/case-level, fixed seed 42
- primary evaluation: per-case macro Dice across KiTS HECs
- model strategy: compact 3D U-Net baseline and nnU-Net-style strong reference
- local/Kaggle division of work
- reproducibility and Git hygiene policy

## Explicitly not started

- dataset download
- raw data ingestion
- manifest generation
- preprocessing implementation
- model implementation
- training
- evaluation code
- deployment

## Operational note

The local Git repository is initialized on `main`, but no remote URL is configured.
The final remote synchronization requirement cannot be completed until the intended
remote URL is supplied and Git credentials/tooling are available.
