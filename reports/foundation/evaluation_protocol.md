# Foundation Evaluation Protocol

## Split

Use a fixed seed `42` to create a 70/15/15 train/validation/internal-test split
from the 489 labeled KiTS23 training cases. Grouping key is the anonymized case
identifier. Exact counts are generated and recorded after the manifest is built.

No slice-level, patch-level, or adjacent-volume random split is permitted.

## Primary metric

Macro-average of per-case Dice across:

- `kidney_and_mass`: labels `(1, 2, 3)`
- `mass`: labels `(2, 3)`
- `tumor`: label `(2,)`

These are the official KiTS hierarchical evaluation regions.

## Secondary metrics

- official surface Dice for each hierarchical region;
- Dice and IoU for kidney, tumor, and cyst separately;
- precision and recall/sensitivity;
- specificity where meaningful;
- HD95 in millimetres;
- volume error;
- per-case distribution and worst-case analysis.

## Empty-mask rules

- empty reference and empty prediction: Dice/IoU = 1;
- empty reference and non-empty prediction: Dice/IoU = 0;
- non-empty reference and empty prediction: Dice/IoU = 0;
- both non-empty: standard metric.

Boundary metrics are separately marked undefined or worst-case when a boundary
does not exist. Denominators are always reported.

## Qualitative evidence

Every final report includes orthogonal overlays, 3D views, successful cases,
