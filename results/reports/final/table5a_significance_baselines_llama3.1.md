| comparison                                                 | metric                  |   n |   ref |   other |   diff | test    |           p |      p_holm | significant (0.05)   |
|:-----------------------------------------------------------|:------------------------|----:|------:|--------:|-------:|:--------|------------:|------------:|:---------------------|
| Evidence-Aware Agent (C) vs ReAct agent (A)                | list_f1                 | 133 |  91.8 |    84.1 |    7.7 | perm    | 0           | 0           | yes                  |
| Evidence-Aware Agent (C) vs ReAct agent (A)                | claim_correct           | 106 | 100   |    60.4 |   39.6 | mcnemar | 4.54747e-13 | 1.54614e-11 | yes                  |
| Evidence-Aware Agent (C) vs ReAct agent (A)                | conflict_detect_correct | 275 |  98.5 |    82.2 |   16.4 | mcnemar | 7.05398e-11 | 2.04565e-09 | yes                  |
| Evidence-Aware Agent (C) vs ReAct agent (A)                | resolution_correct      |  50 |  82   |    48   |   34   | mcnemar | 1.52588e-05 | 0.000396729 | yes                  |
| Evidence-Aware Agent (C) vs ReAct agent (A)                | injected_adoption       |  22 |   0   |    18.2 |  -18.2 | perm    | 0.124       | 1           |                      |
| Evidence-Aware Agent (C) vs ReAct agent (A)                | stale_adoption          |  26 |   0   |     7.7 |   -7.7 | perm    | 0.4989      | 1           |                      |
| Evidence-Aware Agent (C) vs ReAct agent (A)                | abstain_correct         |  50 | 100   |    22   |   78   | mcnemar | 3.63798e-12 | 1.20053e-10 | yes                  |
| Evidence-Aware Agent (C) vs ReAct agent (A)                | uar                     | 131 |   0   |     8.2 |   -8.2 | perm    | 0           | 0           | yes                  |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | list_f1                 | 133 |  91.8 |    87.5 |    4.3 | perm    | 0.0356      | 0.534       |                      |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | claim_correct           | 106 | 100   |   100   |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | conflict_detect_correct | 275 |  98.5 |    98.2 |    0.4 | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | resolution_correct      |  50 |  82   |    84   |   -2   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | injected_adoption       |  22 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | stale_adoption          |  26 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | abstain_correct         |  50 | 100   |   100   |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | uar                     | 122 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Naive RAG                      | list_f1                 | 133 |  91.8 |    72.8 |   19   | perm    | 0           | 0           | yes                  |
| Evidence-Aware Agent (C) vs Naive RAG                      | claim_correct           | 106 | 100   |    14.2 |   85.8 | mcnemar | 8.07794e-28 | 3.31195e-26 | yes                  |
| Evidence-Aware Agent (C) vs Naive RAG                      | conflict_detect_correct | 275 |  98.5 |    81.8 |   16.7 | mcnemar | 3.80297e-11 | 1.21695e-09 | yes                  |
| Evidence-Aware Agent (C) vs Naive RAG                      | resolution_correct      |  50 |  82   |    48   |   34   | mcnemar | 0.0023157   | 0.0486297   | yes                  |
| Evidence-Aware Agent (C) vs Naive RAG                      | injected_adoption       |  22 |   0   |    31.8 |  -31.8 | perm    | 0.0146      | 0.2628      |                      |
| Evidence-Aware Agent (C) vs Naive RAG                      | stale_adoption          |  26 |   0   |    15.4 |  -15.4 | perm    | 0.126       | 1           |                      |
| Evidence-Aware Agent (C) vs Naive RAG                      | abstain_correct         |  50 | 100   |     4   |   96   | mcnemar | 7.10543e-15 | 2.55795e-13 | yes                  |
| Evidence-Aware Agent (C) vs Naive RAG                      | uar                     | 126 |   0   |    19.3 |  -19.3 | perm    | 0           | 0           | yes                  |
| Evidence-Aware Agent (C) vs KG-RAG                         | list_f1                 | 133 |  91.8 |    84.9 |    6.9 | perm    | 0.006       | 0.114       |                      |
| Evidence-Aware Agent (C) vs KG-RAG                         | claim_correct           | 106 | 100   |    22.6 |   77.4 | mcnemar | 4.1359e-25  | 1.65436e-23 | yes                  |
| Evidence-Aware Agent (C) vs KG-RAG                         | conflict_detect_correct | 275 |  98.5 |    82.5 |   16   | mcnemar | 1.30653e-10 | 3.65828e-09 | yes                  |
| Evidence-Aware Agent (C) vs KG-RAG                         | resolution_correct      |  50 |  82   |    48   |   34   | mcnemar | 0.00151372  | 0.0333018   | yes                  |
| Evidence-Aware Agent (C) vs KG-RAG                         | injected_adoption       |  22 |   0   |    18.2 |  -18.2 | perm    | 0.122       | 1           |                      |
| Evidence-Aware Agent (C) vs KG-RAG                         | stale_adoption          |  26 |   0   |    15.4 |  -15.4 | perm    | 0.1237      | 1           |                      |
| Evidence-Aware Agent (C) vs KG-RAG                         | abstain_correct         |  50 | 100   |     2   |   98   | mcnemar | 3.55271e-15 | 1.3145e-13  | yes                  |
| Evidence-Aware Agent (C) vs KG-RAG                         | uar                     | 129 |   0   |     8.6 |   -8.6 | perm    | 0.0001      | 0.0025      | yes                  |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | list_f1                 | 133 |  91.8 |    81.9 |    9.8 | perm    | 0.0001      | 0.0025      | yes                  |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | claim_correct           | 106 | 100   |    49.1 |   50.9 | mcnemar | 1.11022e-16 | 4.21885e-15 | yes                  |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | conflict_detect_correct | 275 |  98.5 |    81.8 |   16.7 | mcnemar | 3.80297e-11 | 1.21695e-09 | yes                  |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | resolution_correct      |  50 |  82   |    56   |   26   | mcnemar | 0.00442505  | 0.088501    |                      |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | injected_adoption       |  22 |   0   |    31.8 |  -31.8 | perm    | 0.0146      | 0.2628      |                      |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | stale_adoption          |  26 |   0   |    11.5 |  -11.5 | perm    | 0.2548      | 1           |                      |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | abstain_correct         |  50 | 100   |    56   |   44   | mcnemar | 4.76837e-07 | 1.28746e-05 | yes                  |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | uar                     | 127 |   0   |    10.2 |  -10.2 | perm    | 0           | 0           | yes                  |
| Evidence-Aware Agent (C) vs CRAG                           | list_f1                 | 133 |  91.8 |    59.5 |   32.3 | perm    | 0           | 0           | yes                  |
| Evidence-Aware Agent (C) vs CRAG                           | claim_correct           | 106 | 100   |    33   |   67   | mcnemar | 8.47033e-22 | 3.30343e-20 | yes                  |
| Evidence-Aware Agent (C) vs CRAG                           | conflict_detect_correct | 275 |  98.5 |    81.8 |   16.7 | mcnemar | 3.80297e-11 | 1.21695e-09 | yes                  |
| Evidence-Aware Agent (C) vs CRAG                           | resolution_correct      |  50 |  82   |    50   |   32   | mcnemar | 0.000144958 | 0.00333405  | yes                  |
| Evidence-Aware Agent (C) vs CRAG                           | injected_adoption       |  22 |   0   |    18.2 |  -18.2 | perm    | 0.125       | 1           |                      |
| Evidence-Aware Agent (C) vs CRAG                           | stale_adoption          |  26 |   0   |    23.1 |  -23.1 | perm    | 0.0319      | 0.5104      |                      |
| Evidence-Aware Agent (C) vs CRAG                           | abstain_correct         |  50 | 100   |     6   |   94   | mcnemar | 1.42109e-14 | 4.9738e-13  | yes                  |
| Evidence-Aware Agent (C) vs CRAG                           | uar                     | 126 |   0   |    33.9 |  -33.9 | perm    | 0           | 0           | yes                  |