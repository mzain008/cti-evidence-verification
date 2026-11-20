**Claim verification by claim type (%)**

| system                  | subtype              |   n |   claim_correct |   false_support |   nei_recall |
|:------------------------|:---------------------|----:|----------------:|----------------:|-------------:|
| Corrective RAG          | claim_behaviour      |  10 |              30 |            16.7 |          nan |
| Corrective RAG          | claim_has_weakness   |  10 |              30 |            60   |          nan |
| Corrective RAG          | claim_mapped_control |  10 |              40 |            20   |          nan |
| Corrective RAG          | claim_maps_to_attack |  10 |              40 |            20   |          nan |
| Corrective RAG          | claim_mitigated_by   |  10 |              40 |            12.5 |          nan |
| Corrective RAG          | claim_name           |  10 |              50 |             0   |          nan |
| Corrective RAG          | claim_nei            |  10 |               0 |           nan   |            0 |
| Evidence-Aware Agent    | claim_behaviour      |  10 |              60 |            50   |          nan |
| Evidence-Aware Agent    | claim_has_weakness   |  10 |             100 |             0   |          nan |
| Evidence-Aware Agent    | claim_mapped_control |  10 |             100 |             0   |          nan |
| Evidence-Aware Agent    | claim_maps_to_attack |  10 |             100 |             0   |          nan |
| Evidence-Aware Agent    | claim_mitigated_by   |  10 |             100 |             0   |          nan |
| Evidence-Aware Agent    | claim_name           |  10 |              60 |             0   |          nan |
| Evidence-Aware Agent    | claim_nei            |  10 |             100 |           nan   |          100 |
| Graph oracle (no LLM)   | claim_behaviour      |  10 |               0 |             0   |          nan |
| Graph oracle (no LLM)   | claim_has_weakness   |  10 |             100 |             0   |          nan |
| Graph oracle (no LLM)   | claim_mapped_control |  10 |             100 |             0   |          nan |
| Graph oracle (no LLM)   | claim_maps_to_attack |  10 |             100 |             0   |          nan |
| Graph oracle (no LLM)   | claim_mitigated_by   |  10 |             100 |             0   |          nan |
| Graph oracle (no LLM)   | claim_name           |  10 |               0 |             0   |          nan |
| Graph oracle (no LLM)   | claim_nei            |  10 |             100 |           nan   |          100 |
| KG-RAG                  | claim_behaviour      |  10 |              10 |             0   |          nan |
| KG-RAG                  | claim_has_weakness   |  10 |              40 |            60   |          nan |
| KG-RAG                  | claim_mapped_control |  10 |              10 |            20   |          nan |
| KG-RAG                  | claim_maps_to_attack |  10 |              10 |             0   |          nan |
| KG-RAG                  | claim_mitigated_by   |  10 |              10 |             0   |          nan |
| KG-RAG                  | claim_name           |  10 |              20 |             0   |          nan |
| KG-RAG                  | claim_nei            |  10 |               0 |           nan   |            0 |
| Multi-hop RAG           | claim_behaviour      |  10 |              50 |             0   |          nan |
| Multi-hop RAG           | claim_has_weakness   |  10 |              50 |            60   |          nan |
| Multi-hop RAG           | claim_mapped_control |  10 |              60 |             0   |          nan |
| Multi-hop RAG           | claim_maps_to_attack |  10 |              70 |             0   |          nan |
| Multi-hop RAG           | claim_mitigated_by   |  10 |              90 |             0   |          nan |
| Multi-hop RAG           | claim_name           |  10 |              60 |             0   |          nan |
| Multi-hop RAG           | claim_nei            |  10 |              10 |           nan   |           10 |
| Naive RAG               | claim_behaviour      |  10 |              30 |             0   |          nan |
| Naive RAG               | claim_has_weakness   |  10 |              30 |            20   |          nan |
| Naive RAG               | claim_mapped_control |  10 |              10 |            20   |          nan |
| Naive RAG               | claim_maps_to_attack |  10 |              20 |            20   |          nan |
| Naive RAG               | claim_mitigated_by   |  10 |               0 |             0   |          nan |
| Naive RAG               | claim_name           |  10 |              20 |             0   |          nan |
| Naive RAG               | claim_nei            |  10 |               0 |           nan   |            0 |
| ReAct agent (no verif.) | claim_behaviour      |  10 |              20 |            16.7 |          nan |
| ReAct agent (no verif.) | claim_has_weakness   |  10 |              50 |           100   |          nan |
| ReAct agent (no verif.) | claim_mapped_control |  10 |              60 |            20   |          nan |
| ReAct agent (no verif.) | claim_maps_to_attack |  10 |              50 |            40   |          nan |
| ReAct agent (no verif.) | claim_mitigated_by   |  10 |              20 |            12.5 |          nan |
| ReAct agent (no verif.) | claim_name           |  10 |              20 |            16.7 |          nan |
| ReAct agent (no verif.) | claim_nei            |  10 |               0 |           nan   |            0 |