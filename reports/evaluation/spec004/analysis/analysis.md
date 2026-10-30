# E-005 — Performance by case characteristics (n = 73)

Descriptive only; groups are small and no significance test is made.

## size_bin

| group | n | mean Dice | 95% CI | tumor Dice | 95% CI | mean surface Dice |
|---|---|---|---|---|---|---|
| small | 25 | 0.515 | 0.416 to 0.612 | 0.324 | 0.209 to 0.446 | 0.469 |
| medium | 24 | 0.796 | 0.725 to 0.857 | 0.705 | 0.608 to 0.793 | 0.680 |
| large | 24 | 0.863 | 0.808 to 0.906 | 0.835 | 0.778 to 0.881 | 0.646 |

## has_cyst

| group | n | mean Dice | 95% CI | tumor Dice | 95% CI | mean surface Dice |
|---|---|---|---|---|---|---|
| False | 36 | 0.735 | 0.656 to 0.807 | 0.642 | 0.538 to 0.739 | 0.598 |
| True | 37 | 0.709 | 0.625 to 0.787 | 0.593 | 0.488 to 0.695 | 0.595 |

## cohort

| group | n | mean Dice | 95% CI | tumor Dice | 95% CI | mean surface Dice |
|---|---|---|---|---|---|---|
| kits21 | 44 | 0.752 | 0.679 to 0.819 | 0.667 | 0.574 to 0.750 | 0.635 |
| kits23_new | 29 | 0.675 | 0.585 to 0.759 | 0.542 | 0.420 to 0.660 | 0.538 |

## fg_volume_quartile

| group | n | mean Dice | 95% CI | tumor Dice | 95% CI | mean surface Dice |
|---|---|---|---|---|---|---|
| Q1 | 19 | 0.664 | 0.529 to 0.788 | 0.545 | 0.378 to 0.704 | 0.569 |
| Q2 | 18 | 0.658 | 0.534 to 0.774 | 0.546 | 0.395 to 0.693 | 0.574 |
| Q3 | 18 | 0.752 | 0.660 to 0.833 | 0.644 | 0.511 to 0.761 | 0.636 |
| Q4 | 18 | 0.816 | 0.732 to 0.888 | 0.738 | 0.606 to 0.849 | 0.609 |

## Tumor volume vs tumor Dice (tumor cases)

Spearman rho = 0.698, 95% CI 0.561 to 0.796, n = 73.

## Cases without tumor

0 of 0 predicted some tumor (false positive).

## Worst cases by mean Dice

| case | mean Dice | tumor Dice | size bin | cyst | cohort |
|---|---|---|---|---|---|
| case_00540 | 0.000 | 0.000 | small | True | kits23_new |
| case_00031 | 0.129 | 0.016 | small | False | kits21 |
| case_00227 | 0.131 | 0.000 | small | True | kits21 |
| case_00214 | 0.215 | 0.059 | small | True | kits21 |
| case_00016 | 0.292 | 0.210 | medium | False | kits21 |
| case_00165 | 0.306 | 0.025 | small | True | kits21 |
| case_00014 | 0.313 | 0.000 | small | False | kits21 |
| case_00509 | 0.330 | 0.000 | small | True | kits23_new |
| case_00561 | 0.335 | 0.046 | small | False | kits23_new |
| case_00502 | 0.336 | 0.000 | small | True | kits23_new |
