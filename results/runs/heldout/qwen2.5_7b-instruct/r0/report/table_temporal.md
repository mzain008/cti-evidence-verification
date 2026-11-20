**Outdated and conflicting evidence (%)**

| system                  | subtype       |   n |    f1 |   recall |   stale_adoption |   flag_correct |   staleness_aware |   replacement_found |
|:------------------------|:--------------|----:|------:|---------:|-----------------:|---------------:|------------------:|--------------------:|
| Corrective RAG          | nvd_kev       |   8 |  84.2 |     75   |            nan   |            0   |               0   |                 nan |
| Corrective RAG          | rev4_rev5     |   8 |  50   |     50   |              0   |            0   |               0   |                 nan |
| Corrective RAG          | revoked       |  10 |  54   |     52.5 |              0   |           10   |              30   |                  30 |
| Corrective RAG          | version_drift |  10 |  92.4 |     87.9 |              0   |          nan   |             nan   |                 nan |
| Corrective RAG          | withdrawn     |   8 |  95.8 |    100   |              0   |          100   |             100   |                 100 |
| Evidence-Aware Agent    | nvd_kev       |   8 |  95.8 |     93.8 |            nan   |          100   |             100   |                 nan |
| Evidence-Aware Agent    | rev4_rev5     |   8 |  93.7 |     89.1 |              0   |          100   |             100   |                 nan |
| Evidence-Aware Agent    | revoked       |  10 |  98.3 |     97.1 |              0   |          100   |             100   |                 100 |
| Evidence-Aware Agent    | version_drift |  10 |  76.6 |     62.6 |              0   |          nan   |             nan   |                 nan |
| Evidence-Aware Agent    | withdrawn     |   8 | 100   |    100   |              0   |          100   |             100   |                 100 |
| Graph oracle (no LLM)   | nvd_kev       |   8 | 100   |    100   |            nan   |            0   |               0   |                 nan |
| Graph oracle (no LLM)   | rev4_rev5     |   8 | 100   |    100   |              0   |            0   |               0   |                 nan |
| Graph oracle (no LLM)   | revoked       |  10 | 100   |    100   |              0   |          100   |             100   |                   0 |
| Graph oracle (no LLM)   | version_drift |  10 | 100   |    100   |              0   |          nan   |             nan   |                 nan |
| Graph oracle (no LLM)   | withdrawn     |   8 | 100   |    100   |              0   |          100   |             100   |                 100 |
| KG-RAG                  | nvd_kev       |   8 |  80   |     68.8 |            nan   |            0   |               0   |                 nan |
| KG-RAG                  | rev4_rev5     |   8 |  73.1 |     74.1 |             25   |           37.5 |              37.5 |                 nan |
| KG-RAG                  | revoked       |  10 |  89.3 |     89.3 |             10   |           20   |              60   |                  60 |
| KG-RAG                  | version_drift |  10 |  86.1 |     76.8 |              0   |          nan   |             nan   |                 nan |
| KG-RAG                  | withdrawn     |   8 | 100   |    100   |              0   |          100   |             100   |                 100 |
| Multi-hop RAG           | nvd_kev       |   8 |  72.1 |     58.3 |            nan   |           12.5 |              12.5 |                 nan |
| Multi-hop RAG           | rev4_rev5     |   8 |  61.8 |     62.5 |             12.5 |           50   |              50   |                 nan |
| Multi-hop RAG           | revoked       |  10 |  66   |     64.3 |              0   |           50   |              80   |                  60 |
| Multi-hop RAG           | version_drift |  10 |  82.9 |     77.8 |             50   |          nan   |             nan   |                 nan |
| Multi-hop RAG           | withdrawn     |   8 |  87.5 |     87.5 |              0   |          100   |             100   |                 100 |
| Naive RAG               | nvd_kev       |   8 |  82.5 |     72.9 |            nan   |            0   |               0   |                 nan |
| Naive RAG               | rev4_rev5     |   8 |  87.6 |     83.7 |             12.5 |           25   |              25   |                 nan |
| Naive RAG               | revoked       |  10 |  86.1 |     82.9 |              0   |           70   |             100   |                  70 |
| Naive RAG               | version_drift |  10 |  94.6 |     90.8 |              0   |          nan   |             nan   |                 nan |
| Naive RAG               | withdrawn     |   8 | 100   |    100   |              0   |          100   |             100   |                 100 |
| ReAct agent (no verif.) | nvd_kev       |   8 |  95.8 |     93.8 |            nan   |          100   |             100   |                 nan |
| ReAct agent (no verif.) | rev4_rev5     |   8 |  69.8 |     69.4 |             37.5 |          100   |             100   |                 nan |
| ReAct agent (no verif.) | revoked       |  10 |  98.3 |     97.1 |              0   |          100   |             100   |                 100 |
| ReAct agent (no verif.) | version_drift |  10 |  76.6 |     62.6 |              0   |          nan   |             nan   |                 nan |
| ReAct agent (no verif.) | withdrawn     |   8 | 100   |    100   |              0   |          100   |             100   |                 100 |