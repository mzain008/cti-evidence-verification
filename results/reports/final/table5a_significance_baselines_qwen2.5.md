| comparison                                                 | metric                  |   n |   ref |   other |   diff | test    |           p |      p_holm | significant (0.05)   |
|:-----------------------------------------------------------|:------------------------|----:|------:|--------:|-------:|:--------|------------:|------------:|:---------------------|
| Evidence-Aware Agent (C) vs ReAct agent (A)                | list_f1                 | 133 |  89.3 |    83.5 |    5.8 | perm    | 0.0005      | 0.014       | yes                  |
| Evidence-Aware Agent (C) vs ReAct agent (A)                | claim_correct           | 106 | 100   |    77.4 |   22.6 | mcnemar | 1.19209e-07 | 4.29153e-06 | yes                  |
| Evidence-Aware Agent (C) vs ReAct agent (A)                | conflict_detect_correct | 275 |  96.7 |    80.7 |   16   | mcnemar | 5.20569e-09 | 2.18639e-07 | yes                  |
| Evidence-Aware Agent (C) vs ReAct agent (A)                | resolution_correct      |  50 |  96   |    76   |   20   | mcnemar | 0.00634766  | 0.158691    |                      |
| Evidence-Aware Agent (C) vs ReAct agent (A)                | injected_adoption       |  22 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs ReAct agent (A)                | stale_adoption          |  26 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs ReAct agent (A)                | abstain_correct         |  50 | 100   |    44   |   56   | mcnemar | 7.45058e-09 | 3.05474e-07 | yes                  |
| Evidence-Aware Agent (C) vs ReAct agent (A)                | uar                     | 124 |   0   |     1.8 |   -1.8 | perm    | 0.1225      | 1           |                      |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | list_f1                 | 133 |  89.3 |    87.7 |    1.6 | perm    | 0.215       | 1           |                      |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | claim_correct           | 106 | 100   |   100   |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | conflict_detect_correct | 275 |  96.7 |    97.8 |   -1.1 | mcnemar | 0.453125    | 1           |                      |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | resolution_correct      |  50 |  96   |    96   |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | injected_adoption       |  22 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | stale_adoption          |  26 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | abstain_correct         |  50 | 100   |   100   |    0   | mcnemar | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | uar                     | 125 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Naive RAG                      | list_f1                 | 133 |  89.3 |    83.6 |    5.7 | perm    | 0.0046      | 0.1242      |                      |
| Evidence-Aware Agent (C) vs Naive RAG                      | claim_correct           | 106 | 100   |    81.1 |   18.9 | mcnemar | 1.90735e-06 | 6.10352e-05 | yes                  |
| Evidence-Aware Agent (C) vs Naive RAG                      | conflict_detect_correct | 275 |  96.7 |    77.5 |   19.3 | mcnemar | 1.32804e-11 | 5.71056e-10 | yes                  |
| Evidence-Aware Agent (C) vs Naive RAG                      | resolution_correct      |  50 |  96   |    80   |   16   | mcnemar | 0.0214844   | 0.494141    |                      |
| Evidence-Aware Agent (C) vs Naive RAG                      | injected_adoption       |  22 |   0   |     4.5 |   -4.5 | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Naive RAG                      | stale_adoption          |  26 |   0   |     7.7 |   -7.7 | perm    | 0.5031      | 1           |                      |
| Evidence-Aware Agent (C) vs Naive RAG                      | abstain_correct         |  50 | 100   |    56   |   44   | mcnemar | 4.76837e-07 | 1.62125e-05 | yes                  |
| Evidence-Aware Agent (C) vs Naive RAG                      | uar                     | 125 |   0   |     5   |   -5   | perm    | 0.0047      | 0.1242      |                      |
| Evidence-Aware Agent (C) vs KG-RAG                         | list_f1                 | 133 |  89.3 |    85.7 |    3.6 | perm    | 0.0235      | 0.517       |                      |
| Evidence-Aware Agent (C) vs KG-RAG                         | claim_correct           | 106 | 100   |    77.4 |   22.6 | mcnemar | 1.19209e-07 | 4.29153e-06 | yes                  |
| Evidence-Aware Agent (C) vs KG-RAG                         | conflict_detect_correct | 275 |  96.7 |    81.5 |   15.3 | mcnemar | 7.45521e-09 | 3.05474e-07 | yes                  |
| Evidence-Aware Agent (C) vs KG-RAG                         | resolution_correct      |  50 |  96   |    76   |   20   | mcnemar | 0.00634766  | 0.158691    |                      |
| Evidence-Aware Agent (C) vs KG-RAG                         | injected_adoption       |  22 |   0   |     4.5 |   -4.5 | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs KG-RAG                         | stale_adoption          |  26 |   0   |     3.8 |   -3.8 | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs KG-RAG                         | abstain_correct         |  50 | 100   |    48   |   52   | mcnemar | 2.98023e-08 | 1.10269e-06 | yes                  |
| Evidence-Aware Agent (C) vs KG-RAG                         | uar                     | 125 |   0   |     2.4 |   -2.4 | perm    | 0.0669      | 1           |                      |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | list_f1                 | 133 |  89.3 |    74.1 |   15.2 | perm    | 0           | 0           | yes                  |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | claim_correct           | 106 | 100   |    63.2 |   36.8 | mcnemar | 3.63798e-12 | 1.60071e-10 | yes                  |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | conflict_detect_correct | 275 |  96.7 |    80.7 |   16   | mcnemar | 1.05072e-08 | 4.09782e-07 | yes                  |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | resolution_correct      |  50 |  96   |    64   |   32   | mcnemar | 3.05176e-05 | 0.000915527 | yes                  |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | injected_adoption       |  22 |   0   |     4.5 |   -4.5 | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | stale_adoption          |  26 |   0   |     0   |    0   | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | abstain_correct         |  50 | 100   |    74   |   26   | mcnemar | 0.000244141 | 0.00708008  | yes                  |
| Evidence-Aware Agent (C) vs Multi-hop RAG                  | uar                     | 106 |   0   |     1.3 |   -1.3 | perm    | 0.4973      | 1           |                      |
| Evidence-Aware Agent (C) vs CRAG                           | list_f1                 | 133 |  89.3 |    61.8 |   27.5 | perm    | 0           | 0           | yes                  |
| Evidence-Aware Agent (C) vs CRAG                           | claim_correct           | 106 | 100   |    55.7 |   44.3 | mcnemar | 1.42109e-14 | 6.39488e-13 | yes                  |
| Evidence-Aware Agent (C) vs CRAG                           | conflict_detect_correct | 275 |  96.7 |    81.5 |   15.3 | mcnemar | 1.57026e-08 | 5.96699e-07 | yes                  |
| Evidence-Aware Agent (C) vs CRAG                           | resolution_correct      |  50 |  96   |    58   |   38   | mcnemar | 2.09808e-05 | 0.000650406 | yes                  |
| Evidence-Aware Agent (C) vs CRAG                           | injected_adoption       |  22 |   0   |     9.1 |   -9.1 | perm    | 0.4982      | 1           |                      |
| Evidence-Aware Agent (C) vs CRAG                           | stale_adoption          |  26 |   0   |     3.8 |   -3.8 | perm    | 1           | 1           |                      |
| Evidence-Aware Agent (C) vs CRAG                           | abstain_correct         |  50 | 100   |    58   |   42   | mcnemar | 9.53674e-07 | 3.14713e-05 | yes                  |
| Evidence-Aware Agent (C) vs CRAG                           | uar                     | 116 |   0   |    24.3 |  -24.3 | perm    | 0           | 0           | yes                  |