**Outdated and conflicting evidence (%)**

| system                  | subtype       |   n |    f1 |   recall |   stale_adoption |   flag_correct |   staleness_aware |   replacement_found |
|:------------------------|:--------------|----:|------:|---------:|-----------------:|---------------:|------------------:|--------------------:|
| Corrective RAG          | nvd_kev       |   8 |  45   |     41.7 |            nan   |              0 |                 0 |                 nan |
| Corrective RAG          | rev4_rev5     |   8 | 100   |    100   |              0   |              0 |                 0 |                 nan |
| Corrective RAG          | revoked       |  10 |  69.3 |     69.3 |              0   |             10 |                30 |                  20 |
| Corrective RAG          | version_drift |  10 |  82   |     80.4 |             50   |            nan |               nan |                 nan |
| Corrective RAG          | withdrawn     |   8 |   8.3 |     12.5 |             62.5 |            100 |               100 |                  50 |
| Evidence-Aware Agent    | nvd_kev       |   8 |  72.1 |     58.3 |            nan   |            100 |               100 |                 nan |
| Evidence-Aware Agent    | rev4_rev5     |   8 |  91.8 |     86.2 |              0   |            100 |               100 |                 nan |
| Evidence-Aware Agent    | revoked       |  10 |  90.7 |     86   |              0   |            100 |               100 |                  30 |
| Evidence-Aware Agent    | version_drift |  10 |  95.2 |     92.2 |              0   |            nan |               nan |                 nan |
| Evidence-Aware Agent    | withdrawn     |   8 | 100   |    100   |              0   |            100 |               100 |                 100 |
| Graph oracle (no LLM)   | nvd_kev       |   8 | 100   |    100   |            nan   |              0 |                 0 |                 nan |
| Graph oracle (no LLM)   | rev4_rev5     |   8 | 100   |    100   |              0   |              0 |                 0 |                 nan |
| Graph oracle (no LLM)   | revoked       |  10 | 100   |    100   |              0   |            100 |               100 |                   0 |
| Graph oracle (no LLM)   | version_drift |  10 | 100   |    100   |              0   |            nan |               nan |                 nan |
| Graph oracle (no LLM)   | withdrawn     |   8 | 100   |    100   |              0   |            100 |               100 |                 100 |
| KG-RAG                  | nvd_kev       |   8 |  88.3 |     81.2 |            nan   |              0 |                 0 |                 nan |
| KG-RAG                  | rev4_rev5     |   8 |  49.2 |     50   |             12.5 |              0 |                 0 |                 nan |
| KG-RAG                  | revoked       |  10 |  69.3 |     69.3 |             10   |              0 |                10 |                  10 |
| KG-RAG                  | version_drift |  10 |  93.5 |     89.3 |              0   |            nan |               nan |                 nan |
| KG-RAG                  | withdrawn     |   8 |  89.6 |    100   |             25   |            100 |               100 |                 100 |
| Multi-hop RAG           | nvd_kev       |   8 |  72.5 |     62.5 |            nan   |              0 |                 0 |                 nan |
| Multi-hop RAG           | rev4_rev5     |   8 |  49.6 |     49.2 |              0   |              0 |                 0 |                 nan |
| Multi-hop RAG           | revoked       |  10 |  89.3 |     89.3 |             10   |             30 |                30 |                  10 |
| Multi-hop RAG           | version_drift |  10 |  87.5 |     83.8 |             50   |            nan |               nan |                 nan |
| Multi-hop RAG           | withdrawn     |   8 | 100   |    100   |              0   |            100 |               100 |                 100 |
| Naive RAG               | nvd_kev       |   8 |  95   |     91.7 |            nan   |              0 |                 0 |                 nan |
| Naive RAG               | rev4_rev5     |   8 |  86.2 |     86.7 |             12.5 |              0 |                 0 |                 nan |
| Naive RAG               | revoked       |  10 |  77.3 |     76   |             10   |             30 |                30 |                  10 |
| Naive RAG               | version_drift |  10 |  72.5 |     65.8 |            100   |            nan |               nan |                 nan |
| Naive RAG               | withdrawn     |   8 |   8.3 |     12.5 |             37.5 |            100 |               100 |                  50 |
| ReAct agent (no verif.) | nvd_kev       |   8 |  72.1 |     58.3 |            nan   |            100 |               100 |                 nan |
| ReAct agent (no verif.) | rev4_rev5     |   8 |  91.8 |     86.2 |              0   |            100 |               100 |                 nan |
| ReAct agent (no verif.) | revoked       |  10 |  89.3 |     86   |              0   |            100 |               100 |                  30 |
| ReAct agent (no verif.) | version_drift |  10 |  95.2 |     92.2 |              0   |            nan |               nan |                 nan |
| ReAct agent (no verif.) | withdrawn     |   8 | 100   |    100   |              0   |            100 |               100 |                 100 |