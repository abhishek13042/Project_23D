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

### E-005 — Error-slice behavior

**Hypothesis:** Performance changes systematically with tumor size, cyst presence,
acquisition phase, and case-level foreground volume.

Experiments that do not answer a decision-relevant question will not be run.
