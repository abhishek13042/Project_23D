# Limitations

- KiTS23 is a challenge dataset, not a prospective clinical validation cohort.
- The project uses public non-commercial data under CC BY-NC-SA 4.0.
- Official challenge test labels are not available for ordinary local evaluation.
- Internal test performance is therefore not an independent external validation result.
- Case IDs are the available independence key; wider patient-level provenance cannot
  be inferred beyond the dataset documentation.
- KiTS23 includes corticomedullary and nephrogenic cases; acquisition phase must be
  recorded and analyzed rather than ignored.
- Annotation quality and review process are inherited from the dataset.
- Tumors and cysts are small and class-imbalanced relative to background and kidney.
- CT intensity values and spatial spacing vary by acquisition.
- A strong segmentation metric does not establish diagnostic or treatment utility.
- Any later use of KiTS19/KiTS21 or AMOS22 must address overlap, label semantics,
  and licensing separately.
- A Kaggle GPU run may not be bitwise identical to another GPU run even with fixed
  seeds; reproducibility is defined through recorded configuration and metric
  tolerance, not identical weights.
