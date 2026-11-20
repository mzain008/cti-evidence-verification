| model               | comparison                                                 | metric                  |   n |   ref |   other |   diff |           p |      p_holm |
|:--------------------|:-----------------------------------------------------------|:------------------------|----:|------:|--------:|-------:|------------:|------------:|
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | list_f1                 | 133 |  89.3 |    83.5 |    5.8 | 0.0002      | 0.0058      |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | claim_correct           | 106 | 100   |    77.4 |   22.6 | 1.19209e-07 | 4.29153e-06 |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | conflict_detect_correct | 275 |  96.7 |    80.7 |   16   | 5.20569e-09 | 2.18639e-07 |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | resolution_correct      |  50 |  96   |    76   |   20   | 0.00634766  | 0.158691    |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | injected_adoption       |  22 |   0   |     0   |    0   | 1           | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | stale_adoption          |  26 |   0   |     0   |    0   | 1           | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | abstain_correct         |  50 | 100   |    44   |   56   | 7.45058e-09 | 3.05474e-07 |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | uar                     | 124 |   0   |     1.8 |   -1.8 | 0.1248      | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | list_f1                 | 133 |  89.3 |    87.7 |    1.6 | 0.2104      | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | claim_correct           | 106 | 100   |   100   |    0   | 1           | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | conflict_detect_correct | 275 |  96.7 |    97.8 |   -1.1 | 0.453125    | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | resolution_correct      |  50 |  96   |    96   |    0   | 1           | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | injected_adoption       |  22 |   0   |     0   |    0   | 1           | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | stale_adoption          |  26 |   0   |     0   |    0   | 1           | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | abstain_correct         |  50 | 100   |   100   |    0   | 1           | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | uar                     | 125 |   0   |     0   |    0   | 1           | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | list_f1                 | 133 |  91.8 |    84.1 |    7.7 | 0           | 0           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | claim_correct           | 106 | 100   |    60.4 |   39.6 | 4.54747e-13 | 1.59162e-11 |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | conflict_detect_correct | 275 |  98.5 |    82.2 |   16.4 | 7.05398e-11 | 2.11619e-09 |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | resolution_correct      |  50 |  82   |    48   |   34   | 1.52588e-05 | 0.000411987 |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | injected_adoption       |  22 |   0   |    18.2 |  -18.2 | 0.1291      | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | stale_adoption          |  26 |   0   |     7.7 |   -7.7 | 0.4913      | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | abstain_correct         |  50 | 100   |    22   |   78   | 3.63798e-12 | 1.23691e-10 |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | uar                     | 131 |   0   |     8.2 |   -8.2 | 0           | 0           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | list_f1                 | 133 |  91.8 |    87.5 |    4.3 | 0.0327      | 0.4905      |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | claim_correct           | 106 | 100   |   100   |    0   | 1           | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | conflict_detect_correct | 275 |  98.5 |    98.2 |    0.4 | 1           | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | resolution_correct      |  50 |  82   |    84   |   -2   | 1           | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | injected_adoption       |  22 |   0   |     0   |    0   | 1           | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | stale_adoption          |  26 |   0   |     0   |    0   | 1           | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | abstain_correct         |  50 | 100   |   100   |    0   | 1           | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | uar                     | 122 |   0   |     0   |    0   | 1           | 1           |