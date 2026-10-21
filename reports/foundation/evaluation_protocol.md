# Foundation Evaluation Protocol

## Split

Use a fixed seed `42` to create a 70/15/15 train/validation/internal-test split
from the 489 labeled KiTS23 training cases. Grouping key is the anonymized case
identifier. Exact counts are generated and recorded after the manifest is built. The split is
stratified by cohort (cases 0-299 vs 400-588), tumor-size bin and cyst presence;
train and validation form fold 0 of a custom nnU-Net split (D-012).

No slice-level, patch-level, or adjacent-volume random split is permitted.

## Primary metrics

Two co-primary results (D-012), both from the official `kits23_compute_metrics`
evaluator: macro-average of per-case Dice and of per-case surface Dice (tolerances
1.0331, 1.1329, 1.1498 mm), across:

- `kidney_and_mass`: labels `(1, 2, 3)`
- `mass`: labels `(2, 3)`
- `tumor`: label `(2,)`

These are the official KiTS hierarchical evaluation regions.

## Secondary metrics

- Dice and IoU for kidney, tumor, and cyst separately;
- precision and recall/sensitivity;
- specificity where meaningful;
- HD95 in millimetres, where both masks are non-empty;
- volume error;
- per-case distribution and worst-case analysis.

## Empty-mask rules

These follow the official KiTS23 evaluator and apply to Dice, IoU and surface Dice:

- empty reference and empty prediction: 1;
- empty reference and non-empty prediction: 0;
- non-empty reference and empty prediction: 0;
- both non-empty: standard metric.

HD95 is undefined when either mask is empty. Denominators are always reported.

## Qualitative evidence

Every final report includes orthogonal overlays, 3D views, successful cases,
median cases, worst cases, and explicit false-positive and false-negative
examples.

