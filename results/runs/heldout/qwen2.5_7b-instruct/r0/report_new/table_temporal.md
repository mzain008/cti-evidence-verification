**Outdated and conflicting evidence (%)**

| system                  | subtype       |   n |    f1 |   recall |   stale_adoption |   flag_correct |   staleness_aware |   replacement_found |
|:------------------------|:--------------|----:|------:|---------:|-----------------:|---------------:|------------------:|--------------------:|
| Corrective RAG          | nvd_kev       |   3 |  82.2 |     72.2 |              nan |            0   |               0   |                 nan |
| Corrective RAG          | rev4_rev5     |   3 |  66.7 |     66.7 |                0 |            0   |               0   |                 nan |
| Corrective RAG          | revoked       |   5 |  60   |     60   |                0 |            0   |              40   |                  40 |
| Corrective RAG          | version_drift |   5 |  89.3 |     83.3 |                0 |          nan   |             nan   |                 nan |
| Corrective RAG          | withdrawn     |   3 | 100   |    100   |                0 |          100   |             100   |                 100 |
| Evidence-Aware Agent    | nvd_kev       |   3 | 100   |    100   |              nan |          100   |             100   |                 nan |
| Evidence-Aware Agent    | rev4_rev5     |   3 |  87.6 |     79.2 |                0 |          100   |             100   |                 nan |
| Evidence-Aware Agent    | revoked       |   5 | 100   |    100   |                0 |          100   |             100   |                 100 |
| Evidence-Aware Agent    | version_drift |   5 |  77.3 |     63.3 |                0 |          nan   |             nan   |                 nan |
| Evidence-Aware Agent    | withdrawn     |   3 | 100   |    100   |                0 |          100   |             100   |                 100 |
| Graph oracle (no LLM)   | nvd_kev       |   3 | 100   |    100   |              nan |            0   |               0   |                 nan |
| Graph oracle (no LLM)   | rev4_rev5     |   3 | 100   |    100   |                0 |            0   |               0   |                 nan |
| Graph oracle (no LLM)   | revoked       |   5 | 100   |    100   |                0 |          100   |             100   |                   0 |
| Graph oracle (no LLM)   | version_drift |   5 | 100   |    100   |                0 |          nan   |             nan   |                 nan |
| Graph oracle (no LLM)   | withdrawn     |   3 | 100   |    100   |                0 |          100   |             100   |                 100 |
| KG-RAG                  | nvd_kev       |   3 |  71.1 |     55.6 |              nan |            0   |               0   |                 nan |
| KG-RAG                  | rev4_rev5     |   3 |  65.4 |     64.3 |                0 |           66.7 |              66.7 |                 nan |
| KG-RAG                  | revoked       |   5 |  93.3 |    100   |               20 |           20   |              60   |                  60 |
| KG-RAG                  | version_drift |   5 |  84   |     73.3 |                0 |          nan   |             nan   |                 nan |
| KG-RAG                  | withdrawn     |   3 | 100   |    100   |                0 |          100   |             100   |                 100 |
| Multi-hop RAG           | nvd_kev       |   3 |  82.2 |     72.2 |              nan |            0   |               0   |                 nan |
| Multi-hop RAG           | rev4_rev5     |   3 |  33.3 |     33.3 |                0 |           66.7 |              66.7 |                 nan |
| Multi-hop RAG           | revoked       |   5 | 100   |    100   |                0 |           80   |             100   |                  80 |
| Multi-hop RAG           | version_drift |   5 |  92   |     86.7 |                0 |          nan   |             nan   |                 nan |
| Multi-hop RAG           | withdrawn     |   3 |  66.7 |     66.7 |                0 |          100   |             100   |                 100 |
| Naive RAG               | nvd_kev       |   3 |  82.2 |     72.2 |              nan |            0   |               0   |                 nan |
| Naive RAG               | rev4_rev5     |   3 |  81.5 |     76.2 |                0 |            0   |               0   |                 nan |
| Naive RAG               | revoked       |   5 | 100   |    100   |                0 |           60   |             100   |                  80 |
| Naive RAG               | version_drift |   5 |  92   |     86.7 |                0 |          nan   |             nan   |                 nan |
| Naive RAG               | withdrawn     |   3 | 100   |    100   |                0 |          100   |             100   |                 100 |
| ReAct agent (no verif.) | nvd_kev       |   3 | 100   |    100   |              nan |          100   |             100   |                 nan |
| ReAct agent (no verif.) | rev4_rev5     |   3 |  61.5 |     57.8 |                0 |          100   |             100   |                 nan |
| ReAct agent (no verif.) | revoked       |   5 | 100   |    100   |                0 |          100   |             100   |                 100 |
| ReAct agent (no verif.) | version_drift |   5 |  77.3 |     63.3 |                0 |          nan   |             nan   |                 nan |
| ReAct agent (no verif.) | withdrawn     |   3 | 100   |    100   |                0 |          100   |             100   |                 100 |