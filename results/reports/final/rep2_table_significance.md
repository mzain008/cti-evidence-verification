| model               | comparison                                                 | metric                  |   n |   ref |   other |   diff |           p |      p_holm |
|:--------------------|:-----------------------------------------------------------|:------------------------|----:|------:|--------:|-------:|------------:|------------:|
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | list_f1                 | 116 |  93.6 |    85.6 |    8   | 0.0001      | 0.0013      |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | claim_correct           | 106 | 100   |    73.6 |   26.4 | 7.45058e-09 | 1.04308e-07 |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | conflict_detect_correct | 258 |  96.9 |    79.5 |   17.4 | 5.67619e-10 | 8.51429e-09 |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | resolution_correct      |  50 | 100   |    76   |   24   | 0.000488281 | 0.00585938  |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | injected_adoption       |  22 |   0   |     4.5 |   -4.5 | 1           | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | stale_adoption          |  25 |   0   |     0   |    0   | 1           | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | abstain_correct         |  50 | 100   |    32   |   68   | 1.16415e-10 | 1.86265e-09 |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs ReAct agent (A)                | uar                     | 113 |   0   |     1   |   -1   | 0.2512      | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | list_f1                 | 116 |  93.6 |    93.4 |    0.2 | 0.8469      | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | claim_correct           | 106 | 100   |   100   |    0   | 1           | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | conflict_detect_correct | 258 |  96.9 |    96.5 |    0.4 | 1           | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | resolution_correct      |  50 | 100   |   100   |    0   | 1           | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | injected_adoption       |  22 |   0   |     0   |    0   | 1           | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | stale_adoption          |  25 |   0   |     0   |    0   | 1           | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | abstain_correct         |  50 | 100   |   100   |    0   | 1           | 1           |
| qwen2.5:7b-instruct | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | uar                     | 115 |   0   |     0   |    0   | 1           | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | list_f1                 | 116 |  93.1 |    83.7 |    9.3 | 0           | 0           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | claim_correct           | 106 | 100   |    50.9 |   49.1 | 4.44089e-16 | 6.21725e-15 |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | conflict_detect_correct | 258 |  98.1 |    80.6 |   17.4 | 2.13584e-10 | 2.56301e-09 |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | resolution_correct      |  50 |  88   |    40   |   48   | 1.19209e-07 | 1.3113e-06  |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | injected_adoption       |  22 |   0   |    36.4 |  -36.4 | 0.0069      | 0.069       |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | stale_adoption          |  25 |   0   |     4   |   -4   | 1           | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | abstain_correct         |  50 | 100   |    16   |   84   | 4.54747e-13 | 5.91172e-12 |
| llama3.1:8b         | Evidence-Aware Agent (C) vs ReAct agent (A)                | uar                     | 115 |   0   |     9.6 |   -9.6 | 0           | 0           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | list_f1                 | 116 |  93.1 |    89.7 |    3.3 | 0.1495      | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | claim_correct           | 106 | 100   |   100   |    0   | 1           | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | conflict_detect_correct | 258 |  98.1 |    98.1 |    0   | 1           | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | resolution_correct      |  50 |  88   |    88   |    0   | 1           | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | injected_adoption       |  22 |   0   |     0   |    0   | 1           | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | stale_adoption          |  25 |   0   |     0   |    0   | 1           | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | abstain_correct         |  50 | 100   |   100   |    0   | 1           | 1           |
| llama3.1:8b         | Evidence-Aware Agent (C) vs Non-agentic graph verifier (B) | uar                     | 108 |   0   |     0   |    0   | 1           | 1           |