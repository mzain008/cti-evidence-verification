**Claim verification by claim type (%)**

| system                  | subtype              |   n |   claim_correct |   false_support |   nei_recall |
|:------------------------|:---------------------|----:|----------------:|----------------:|-------------:|
| Corrective RAG          | claim_behaviour      |  10 |              30 |            50   |          nan |
| Corrective RAG          | claim_has_weakness   |  10 |              60 |            50   |          nan |
| Corrective RAG          | claim_mapped_control |  10 |              50 |            20   |          nan |
| Corrective RAG          | claim_maps_to_attack |  10 |              30 |             0   |          nan |
| Corrective RAG          | claim_mitigated_by   |  10 |              50 |             0   |          nan |
| Corrective RAG          | claim_name           |  10 |              60 |             0   |          nan |
| Evidence-Aware Agent    | claim_behaviour      |  10 |              70 |            50   |          nan |
| Evidence-Aware Agent    | claim_has_weakness   |  10 |             100 |             0   |          nan |
| Evidence-Aware Agent    | claim_mapped_control |  10 |             100 |             0   |          nan |
| Evidence-Aware Agent    | claim_maps_to_attack |  10 |             100 |             0   |          nan |
| Evidence-Aware Agent    | claim_mitigated_by   |  10 |             100 |             0   |          nan |
| Evidence-Aware Agent    | claim_name           |  10 |              80 |             0   |          nan |
| Graph oracle (no LLM)   | claim_behaviour      |  10 |               0 |             0   |          nan |
| Graph oracle (no LLM)   | claim_has_weakness   |  10 |             100 |             0   |          nan |
| Graph oracle (no LLM)   | claim_mapped_control |  10 |             100 |             0   |          nan |
| Graph oracle (no LLM)   | claim_maps_to_attack |  10 |             100 |             0   |          nan |
| Graph oracle (no LLM)   | claim_mitigated_by   |  10 |             100 |             0   |          nan |
| Graph oracle (no LLM)   | claim_name           |  10 |               0 |             0   |          nan |
| KG-RAG                  | claim_behaviour      |  10 |              10 |            25   |          nan |
| KG-RAG                  | claim_has_weakness   |  10 |              30 |            50   |          nan |
| KG-RAG                  | claim_mapped_control |  10 |              30 |             0   |          nan |
| KG-RAG                  | claim_maps_to_attack |  10 |              20 |             0   |          nan |
| KG-RAG                  | claim_mitigated_by   |  10 |              40 |             0   |          nan |
| KG-RAG                  | claim_name           |  10 |              10 |             0   |          nan |
| Multi-hop RAG           | claim_behaviour      |  10 |              10 |             0   |          nan |
| Multi-hop RAG           | claim_has_weakness   |  10 |              70 |             0   |          nan |
| Multi-hop RAG           | claim_mapped_control |  10 |              50 |             0   |          nan |
| Multi-hop RAG           | claim_maps_to_attack |  10 |              40 |             0   |          nan |
| Multi-hop RAG           | claim_mitigated_by   |  10 |              60 |             0   |          nan |
| Multi-hop RAG           | claim_name           |  10 |              50 |             0   |          nan |
| Naive RAG               | claim_behaviour      |  10 |              20 |             0   |          nan |
| Naive RAG               | claim_has_weakness   |  10 |              10 |            16.7 |          nan |
| Naive RAG               | claim_mapped_control |  10 |              50 |             0   |          nan |
| Naive RAG               | claim_maps_to_attack |  10 |              20 |             0   |          nan |
| Naive RAG               | claim_mitigated_by   |  10 |              10 |             0   |          nan |
| Naive RAG               | claim_name           |  10 |              10 |            20   |          nan |
| ReAct agent (no verif.) | claim_behaviour      |  10 |              50 |            25   |          nan |
| ReAct agent (no verif.) | claim_has_weakness   |  10 |              40 |            83.3 |          nan |
| ReAct agent (no verif.) | claim_mapped_control |  10 |              80 |             0   |          nan |
| ReAct agent (no verif.) | claim_maps_to_attack |  10 |              50 |            20   |          nan |
| ReAct agent (no verif.) | claim_mitigated_by   |  10 |              60 |            50   |          nan |
| ReAct agent (no verif.) | claim_name           |  10 |              10 |            20   |          nan |