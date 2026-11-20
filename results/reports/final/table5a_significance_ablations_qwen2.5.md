| comparison                                                | metric                  |   n |   ref |   other |   diff | test    |           p |      p_holm | significant (0.05)   |
|:----------------------------------------------------------|:------------------------|----:|------:|--------:|-------:|:--------|------------:|------------:|:---------------------|
| Evidence-Aware Agent (C) vs - verification                | list_f1                 | 133 |  89.3 |    87.8 |    1.5 | perm    | 0.5068      | 1           |                      |
| Evidence-Aware Agent (C) vs - verification                | claim_correct           | 106 | 100   |    77.4 |   22.6 | mcnemar | 1.19209e-07 | 4.41074e-06 | yes                  |
| Evidence-Aware Agent (C) vs - verification                | conflict_detect_correct | 275 |  96.7 |    96.7 |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - verification                | resolution_correct      |  50 |  96   |    94   |    2   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - verification                | injected_adoption       |  22 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - verification                | stale_adoption          |  26 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - verification                | abstain_correct         |  50 | 100   |    44   |   56   | mcnemar | 7.45058e-09 | 2.83122e-07 | yes                  |
| Evidence-Aware Agent (C) vs - verification                | uar                     | 124 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - graph verification          | list_f1                 | 133 |  89.3 |    76.8 |   12.5 | perm    | 0           | 0           | yes                  |
| Evidence-Aware Agent (C) vs - graph verification          | claim_correct           | 106 | 100   |    87.7 |   12.3 | mcnemar | 0.000244141 | 0.00830078  | yes                  |
| Evidence-Aware Agent (C) vs - graph verification          | conflict_detect_correct | 275 |  96.7 |    97.5 |   -0.7 | mcnemar | 0.5         | 1           |                      |
| Evidence-Aware Agent (C) vs - graph verification          | resolution_correct      |  50 |  96   |    90   |    6   | mcnemar | 0.375       | 1           |                      |
| Evidence-Aware Agent (C) vs - graph verification          | injected_adoption       |  22 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - graph verification          | stale_adoption          |  26 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - graph verification          | abstain_correct         |  50 | 100   |    82   |   18   | mcnemar | 0.00390625  | 0.125       |                      |
| Evidence-Aware Agent (C) vs - graph verification          | uar                     | 126 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | list_f1                 | 133 |  89.3 |    83   |    6.3 | perm    | 0.0034      | 0.1122      |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | claim_correct           | 106 | 100   |   100   |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | conflict_detect_correct | 275 |  96.7 |    98.5 |   -1.8 | mcnemar | 0.0625      | 1           |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | resolution_correct      |  50 |  96   |    92   |    4   | mcnemar | 0.625       | 1           |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | injected_adoption       |  22 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | stale_adoption          |  26 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | abstain_correct         |  50 | 100   |   100   |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | uar                     | 120 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - authority verification      | list_f1                 | 133 |  89.3 |    90.6 |   -1.4 | perm    | 0.2913      | 1           |                      |
| Evidence-Aware Agent (C) vs - authority verification      | claim_correct           | 106 | 100   |    86.8 |   13.2 | mcnemar | 0.00012207  | 0.00439453  | yes                  |
| Evidence-Aware Agent (C) vs - authority verification      | conflict_detect_correct | 275 |  96.7 |    96.4 |    0.4 | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - authority verification      | resolution_correct      |  50 |  96   |    64   |   32   | mcnemar | 0.000144958 | 0.00507355  | yes                  |
| Evidence-Aware Agent (C) vs - authority verification      | injected_adoption       |  22 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - authority verification      | stale_adoption          |  26 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - authority verification      | abstain_correct         |  50 | 100   |   100   |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - authority verification      | uar                     | 126 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - explicit conflict detection | list_f1                 | 133 |  89.3 |    86.8 |    2.5 | perm    | 0.0052      | 0.1612      |                      |
| Evidence-Aware Agent (C) vs - explicit conflict detection | claim_correct           | 106 | 100   |   100   |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - explicit conflict detection | conflict_detect_correct | 275 |  96.7 |    80   |   16.7 | mcnemar | 3.80297e-11 | 1.48316e-09 | yes                  |
| Evidence-Aware Agent (C) vs - explicit conflict detection | resolution_correct      |  50 |  96   |    78   |   18   | mcnemar | 0.0117188   | 0.351562    |                      |
| Evidence-Aware Agent (C) vs - explicit conflict detection | injected_adoption       |  22 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - explicit conflict detection | stale_adoption          |  26 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - explicit conflict detection | abstain_correct         |  50 | 100   |   100   |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - explicit conflict detection | uar                     | 126 |   0   |     0   |    0   | perm    | 1           | 1           |                      |