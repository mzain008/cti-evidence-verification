| System                             |   LLM calls / q |   Input tok / q |   Output tok / q |   Tokens per correct answer |
|:-----------------------------------|----------------:|----------------:|-----------------:|----------------------------:|
| Graph oracle (no LLM, upper bound) |            0    |               0 |                0 |                           0 |
| Naive RAG                          |            1    |            1540 |               98 |                        5006 |
| KG-RAG                             |            1    |            3602 |              109 |                        9034 |
| Multi-hop RAG                      |            3.88 |            6709 |              328 |                       11588 |
| CRAG                               |            2.01 |            2307 |              135 |                        6398 |
| ReAct agent (A)                    |            3.43 |            5843 |              541 |                       11328 |
| Non-agentic graph verifier (B)     |            1    |            3680 |              233 |                        4503 |
| Evidence-Aware Agent (C)           |            3.43 |            5875 |              545 |                        7326 |
| - verification                     |            3.43 |            5875 |              545 |                       10387 |
| - graph verification               |            4.27 |            6354 |              635 |                        9807 |
| - temporal verification            |            3.61 |            4961 |              538 |                        6491 |
| - authority verification           |            3.43 |            5813 |              561 |                        7826 |
| - explicit conflict detection      |            3.43 |            5864 |              547 |                        7471 |