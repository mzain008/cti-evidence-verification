**Claim verification by claim type (%)**

| system                  | subtype              |   n |   claim_correct |   false_support |   nei_recall |
|:------------------------|:---------------------|----:|----------------:|----------------:|-------------:|
| Corrective RAG          | claim_behaviour      |   5 |               0 |            66.7 |          nan |
| Corrective RAG          | claim_has_weakness   |   5 |             100 |             0   |          nan |
| Corrective RAG          | claim_mapped_control |   5 |              40 |             0   |          nan |
| Corrective RAG          | claim_maps_to_attack |   5 |               0 |             0   |          nan |
| Corrective RAG          | claim_mitigated_by   |   5 |              40 |             0   |          nan |
| Corrective RAG          | claim_name           |   5 |              40 |             0   |          nan |
| Evidence-Aware Agent    | claim_behaviour      |   5 |              40 |            66.7 |          nan |
| Evidence-Aware Agent    | claim_has_weakness   |   5 |             100 |             0   |          nan |
| Evidence-Aware Agent    | claim_mapped_control |   5 |             100 |             0   |          nan |
| Evidence-Aware Agent    | claim_maps_to_attack |   5 |             100 |             0   |          nan |
| Evidence-Aware Agent    | claim_mitigated_by   |   5 |             100 |             0   |          nan |
| Evidence-Aware Agent    | claim_name           |   5 |              60 |             0   |          nan |
| Graph oracle (no LLM)   | claim_behaviour      |   5 |               0 |             0   |          nan |
| Graph oracle (no LLM)   | claim_has_weakness   |   5 |             100 |             0   |          nan |
| Graph oracle (no LLM)   | claim_mapped_control |   5 |             100 |             0   |          nan |
| Graph oracle (no LLM)   | claim_maps_to_attack |   5 |             100 |             0   |          nan |
| Graph oracle (no LLM)   | claim_mitigated_by   |   5 |             100 |             0   |          nan |
| Graph oracle (no LLM)   | claim_name           |   5 |               0 |             0   |          nan |
| KG-RAG                  | claim_behaviour      |   5 |               0 |            33.3 |          nan |
| KG-RAG                  | claim_has_weakness   |   5 |              60 |           100   |          nan |
| KG-RAG                  | claim_mapped_control |   5 |              20 |             0   |          nan |
| KG-RAG                  | claim_maps_to_attack |   5 |              20 |             0   |          nan |
| KG-RAG                  | claim_mitigated_by   |   5 |              60 |             0   |          nan |
| KG-RAG                  | claim_name           |   5 |              20 |             0   |          nan |
| Multi-hop RAG           | claim_behaviour      |   5 |              20 |             0   |          nan |
| Multi-hop RAG           | claim_has_weakness   |   5 |              60 |             0   |          nan |
| Multi-hop RAG           | claim_mapped_control |   5 |              60 |             0   |          nan |
| Multi-hop RAG           | claim_maps_to_attack |   5 |              40 |             0   |          nan |
| Multi-hop RAG           | claim_mitigated_by   |   5 |              60 |             0   |          nan |
| Multi-hop RAG           | claim_name           |   5 |              60 |             0   |          nan |
| Naive RAG               | claim_behaviour      |   5 |               0 |             0   |          nan |
| Naive RAG               | claim_has_weakness   |   5 |              20 |             0   |          nan |
| Naive RAG               | claim_mapped_control |   5 |              60 |             0   |          nan |
| Naive RAG               | claim_maps_to_attack |   5 |              20 |             0   |          nan |
| Naive RAG               | claim_mitigated_by   |   5 |              20 |             0   |          nan |
| Naive RAG               | claim_name           |   5 |               0 |            33.3 |          nan |
| ReAct agent (no verif.) | claim_behaviour      |   5 |              20 |            33.3 |          nan |
| ReAct agent (no verif.) | claim_has_weakness   |   5 |              80 |           100   |          nan |
| ReAct agent (no verif.) | claim_mapped_control |   5 |              80 |             0   |          nan |
| ReAct agent (no verif.) | claim_maps_to_attack |   5 |              60 |             0   |          nan |
| ReAct agent (no verif.) | claim_mitigated_by   |   5 |              60 |             0   |          nan |
| ReAct agent (no verif.) | claim_name           |   5 |               0 |            33.3 |          nan |