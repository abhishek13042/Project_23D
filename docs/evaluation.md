# Evaluation Protocol

## Evaluation population

The 489 labeled KiTS23 training cases are split once at the case level:

- 70% training
- 15% validation
- 15% internal test

The split uses a fixed seed of `42`, groups by anonymized case ID, and stratifies
where feasible by acquisition phase and presence of tumor/cyst labels. Exact case
counts are generated from the verified manifest in SPEC 002, not guessed here.

The official 110-case KiTS23 challenge test allocation is not used for local
metrics because its ground-truth masks are not part of the ordinary public release.

## Primary metric

The primary result is the **macro-average of per-case Dice across the three KiTS
hierarchical evaluation classes**:

1. kidney and masses: labels 1, 2, 3
2. mass: labels 2, 3
3. tumor: label 2

Per-case averaging prevents large volumes or easy cases from dominating the result.

## Secondary metrics

Report separately:

- Dice per hierarchical class
- official KiTS surface Dice per hierarchical class using the official tolerance values
- class-level Dice for kidney, tumor, and cyst
- class-level IoU/Jaccard
- precision
- recall/sensitivity
- specificity where the case/class denominator is meaningful
- HD95 in millimetres for non-empty foreground surfaces
- absolute and relative volume error where meaningful
- per-case distributions: median, interquartile range, 10th percentile, and worst cases

No single aggregate number may replace per-class and per-case reporting.

## Empty-mask policy

For a specific binary evaluation region:

| Ground truth | Prediction | Dice/IoU convention | Interpretation |
|---|---|---|---|
| empty | empty | 1.0 | Correct absence |
| non-empty | empty | 0.0 | Complete miss |
| empty | non-empty | 0.0 | False positive |
| non-empty | non-empty | normal formula | Standard overlap |

Boundary metrics are reported as undefined/omitted for cases where both masks are
empty, and as a worst-case failure or zero score where exactly one mask is empty.
The report includes denominators for every metric.

## Threshold and output policy

The multiclass prediction is the argmax class map unless an experiment explicitly
defines a calibrated probability threshold. Postprocessing is not tuned on the
test split.

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
