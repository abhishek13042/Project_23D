# Evaluation Protocol

## Evaluation population

The 489 labeled KiTS23 training cases are split once at the case level:

- 70% training
- 15% validation
- 15% internal test

The split uses a fixed seed of `42`, groups by anonymized case ID, and stratifies
by cohort (cases 0-299 vs 400-588, a documented phase proxy; per-case phase is
unavailable, D-010), tumor-size bin, and cyst presence (D-012). Exact case
counts are generated from the verified manifest in SPEC 002, not guessed here.

The official 110-case KiTS23 challenge test allocation is not used for local
metrics because its ground-truth masks are not part of the ordinary public release.

Under D-012, the training and validation cases form fold 0 of a custom nnU-Net
`splits_final.json`. The internal test cases are never given to nnU-Net during
training or post-processing selection.

## Primary metrics

There are two co-primary results, matching the official KiTS23 ranking (D-012):

- the **macro-average of per-case Dice**, and
- the **macro-average of per-case surface Dice**, using the official tolerances
  (1.0331, 1.1329 and 1.1498 mm).

Both are computed with the official `kits23_compute_metrics` evaluator over the
three KiTS hierarchical evaluation classes:

1. kidney and masses: labels 1, 2, 3
2. mass: labels 2, 3
3. tumor: label 2

Per-case averaging prevents large volumes or easy cases from dominating the result.

## Secondary metrics

Report separately:

- Dice per hierarchical class
- class-level Dice for kidney, tumor, and cyst
- class-level IoU/Jaccard
- precision
- recall/sensitivity
- specificity where the case/class denominator is meaningful
- HD95 in millimetres, only where both masks are non-empty
- absolute and relative volume error where meaningful
- per-case distributions: median, interquartile range, 10th percentile, and worst cases

No single aggregate number may replace per-class and per-case reporting.

## Empty-mask policy

For a specific binary evaluation region:

This is the official KiTS23 evaluator's rule. It applies to Dice, IoU and surface
Dice alike.

| Ground truth | Prediction | Score | Interpretation |
|---|---|---|---|
| empty | empty | 1.0 | Correct absence |
| non-empty | empty | 0.0 | Complete miss |
| empty | non-empty | 0.0 | False positive |
| non-empty | non-empty | normal formula | Standard overlap |

HD95 has no meaningful value when either mask is empty. It is reported as undefined
for those cases, and the number of such cases is listed with it.
The report includes denominators for every metric.

## Threshold and output policy

The multiclass prediction is the argmax class map unless an experiment explicitly
defines a calibrated probability threshold. Postprocessing is not tuned on the
test split: the rule was chosen on the fold-0 validation cases only (D-021).

## Qualitative analysis

For validation and test cases, save:

- axial, coronal, and sagittal overlays
- 3D surface or volume views for representative cases
- best, median, and worst cases per target class
- false-positive and false-negative examples
- small-lesion and boundary-failure examples

## Statistical reporting

Report per-case distributions and bootstrap 95% confidence intervals for primary
aggregate metrics when the number of cases permits. No statistical significance
claim is made without a predeclared comparison and appropriate paired analysis.
