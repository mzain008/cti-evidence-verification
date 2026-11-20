| comparison                                                | metric                  |   n |   ref |   other |   diff | test    |           p |      p_holm | significant (0.05)   |
|:----------------------------------------------------------|:------------------------|----:|------:|--------:|-------:|:--------|------------:|------------:|:---------------------|
| Evidence-Aware Agent (C) vs - verification                | list_f1                 | 133 |  91.8 |    90.7 |    1   | perm    | 0.0657      | 1           |                      |
| Evidence-Aware Agent (C) vs - verification                | claim_correct           | 106 | 100   |    60.4 |   39.6 | mcnemar | 4.54747e-13 | 1.77351e-11 | yes                  |
| Evidence-Aware Agent (C) vs - verification                | conflict_detect_correct | 275 |  98.5 |    98.5 |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - verification                | resolution_correct      |  50 |  82   |    66   |   16   | mcnemar | 0.0078125   | 0.242188    |                      |
| Evidence-Aware Agent (C) vs - verification                | injected_adoption       |  22 |   0   |     9.1 |   -9.1 | perm    | 0.5051      | 1           |                      |
| Evidence-Aware Agent (C) vs - verification                | stale_adoption          |  26 |   0   |     3.8 |   -3.8 | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - verification                | abstain_correct         |  50 | 100   |    22   |   78   | mcnemar | 3.63798e-12 | 1.38243e-10 | yes                  |
| Evidence-Aware Agent (C) vs - verification                | uar                     | 131 |   0   |     1.9 |   -1.9 | perm    | 0.065       | 1           |                      |
| Evidence-Aware Agent (C) vs - graph verification          | list_f1                 | 133 |  91.8 |    80.1 |   11.7 | perm    | 0           | 0           | yes                  |
| Evidence-Aware Agent (C) vs - graph verification          | claim_correct           | 106 | 100   |    94.3 |    5.7 | mcnemar | 0.03125     | 0.875       |                      |
| Evidence-Aware Agent (C) vs - graph verification          | conflict_detect_correct | 275 |  98.5 |    98.2 |    0.4 | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - graph verification          | resolution_correct      |  50 |  82   |    66   |   16   | mcnemar | 0.0214844   | 0.644531    |                      |
| Evidence-Aware Agent (C) vs - graph verification          | injected_adoption       |  22 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - graph verification          | stale_adoption          |  26 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - graph verification          | abstain_correct         |  50 | 100   |    78   |   22   | mcnemar | 0.000976562 | 0.0332031   | yes                  |
| Evidence-Aware Agent (C) vs - graph verification          | uar                     | 123 |   0   |     0.8 |   -0.8 | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | list_f1                 | 133 |  91.8 |    87.3 |    4.4 | perm    | 0.0257      | 0.7453      |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | claim_correct           | 106 | 100   |   100   |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | conflict_detect_correct | 275 |  98.5 |    98.5 |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | resolution_correct      |  50 |  82   |    84   |   -2   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | injected_adoption       |  22 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | stale_adoption          |  26 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | abstain_correct         |  50 | 100   |   100   |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - temporal verification       | uar                     | 125 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - authority verification      | list_f1                 | 133 |  91.8 |    91.6 |    0.2 | perm    | 0.8486      | 1           |                      |
| Evidence-Aware Agent (C) vs - authority verification      | claim_correct           | 106 | 100   |    86.8 |   13.2 | mcnemar | 0.00012207  | 0.00427246  | yes                  |
| Evidence-Aware Agent (C) vs - authority verification      | conflict_detect_correct | 275 |  98.5 |    97.5 |    1.1 | mcnemar | 0.25        | 1           |                      |
| Evidence-Aware Agent (C) vs - authority verification      | resolution_correct      |  50 |  82   |    38   |   44   | mcnemar | 1.04904e-05 | 0.000377655 | yes                  |
| Evidence-Aware Agent (C) vs - authority verification      | injected_adoption       |  22 |   0   |    40.9 |  -40.9 | perm    | 0.004       | 0.128       |                      |
| Evidence-Aware Agent (C) vs - authority verification      | stale_adoption          |  26 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - authority verification      | abstain_correct         |  50 | 100   |   100   |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - authority verification      | uar                     | 131 |   0   |     2.8 |   -2.8 | perm    | 0.003       | 0.099       |                      |
| Evidence-Aware Agent (C) vs - explicit conflict detection | list_f1                 | 133 |  91.8 |    90   |    1.8 | perm    | 0.106       | 1           |                      |
| Evidence-Aware Agent (C) vs - explicit conflict detection | claim_correct           | 106 | 100   |   100   |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - explicit conflict detection | conflict_detect_correct | 275 |  98.5 |    82.2 |   16.4 | mcnemar | 7.05398e-11 | 2.60997e-09 | yes                  |
| Evidence-Aware Agent (C) vs - explicit conflict detection | resolution_correct      |  50 |  82   |    70   |   12   | mcnemar | 0.03125     | 0.875       |                      |
| Evidence-Aware Agent (C) vs - explicit conflict detection | injected_adoption       |  22 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - explicit conflict detection | stale_adoption          |  26 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - explicit conflict detection | abstain_correct         |  50 | 100   |   100   |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs - explicit conflict detection | uar                     | 130 |   0   |     0   |    0   | perm    | 1           | 1           |                      |