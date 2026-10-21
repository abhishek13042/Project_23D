# Experiment Foundation

No experiments are run in SPEC 001. This document defines the future structure.

## Required experiment record

Every run records:

- experiment ID
- hypothesis
- baseline
- variable changed
- dataset version and fingerprint
- split manifest and fingerprint
- model and checkpoint
- configuration and config hash
- random seed
- code version
- environment and hardware
- metrics
- artifacts
- interpretation
- conclusion

## Scope under D-012

Because of the compute limit (D-012), only two items run:

- **R-001 — Reference run:** official nnU-Net v2, fold 0, 100 epochs, scored on the
  locked test set. This replaces E-001; no hand-built baseline is trained.
- **E-005 — Performance by case characteristics:** a no-GPU analysis of the R-001
  test predictions.

E-001 to E-004 below are kept as future work and are not run in this project.

## Initial research questions

### E-001 — Baseline versus strong reference

**Hypothesis:** A self-configuring nnU-Net-style pipeline improves or stabilizes
case-level segmentation performance compared with a compact hand-configured 3D
U-Net under the same split.

### E-002 — Preprocessing sensitivity

**Hypothesis:** The chosen CT intensity policy and target-spacing policy materially
affect small-tumor and boundary performance.

### E-003 — Patch/context strategy

**Hypothesis:** The selected patch size and overlap provide a better memory-quality
tradeoff than the initial alternative without damaging whole-volume reconstruction.

### E-004 — Postprocessing impact

**Hypothesis:** Connected-component or hierarchy-aware postprocessing changes
false-positive behavior without masking genuine model failures.

### E-005 — Performance by case characteristics

**Hypothesis:** Performance changes systematically with tumor size, cyst presence,
cohort (cases 0-299 vs 400-588, a phase proxy; see D-010), and case-level
foreground volume.

Experiments that do not answer a decision-relevant question will not be run.
