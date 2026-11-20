| model               | system             |   calls/question |   prompt tokens/question |   completion tokens/question |   share answered from cache |
|:--------------------|:-------------------|-----------------:|-------------------------:|-----------------------------:|----------------------------:|
| qwen2.5:7b-instruct | react_agent        |             2.53 |                     4134 |                          287 |                        0    |
| qwen2.5:7b-instruct | conflict_aware_rag |             2    |                     8770 |                          263 |                        0    |
| qwen2.5:7b-instruct | graph_verifier_v11 |             1.01 |                     4375 |                          124 |                        0.98 |
| qwen2.5:7b-instruct | evidence_agent_v11 |             2.53 |                     4194 |                          288 |                        1    |
| llama3.1:8b         | react_agent        |             3.43 |                     5843 |                          542 |                        0    |
| llama3.1:8b         | conflict_aware_rag |             2    |                     7467 |                          258 |                        0    |
| llama3.1:8b         | graph_verifier_v11 |             1    |                     3675 |                          235 |                        0.98 |
| llama3.1:8b         | evidence_agent_v11 |             3.43 |                     5874 |                          544 |                        1    |