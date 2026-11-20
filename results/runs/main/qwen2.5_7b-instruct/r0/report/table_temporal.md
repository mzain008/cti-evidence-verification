**Outdated and conflicting evidence (%)**

| system                  | subtype       |   n |    f1 |   recall |   stale_adoption |   flag_correct |   staleness_aware |   replacement_found |
|:------------------------|:--------------|----:|------:|---------:|-----------------:|---------------:|------------------:|--------------------:|
| Corrective RAG          | nvd_kev       |  10 |  93.3 |     90   |              nan |              0 |                 0 |                 nan |
| Corrective RAG          | rev4_rev5     |  10 |  49.7 |     49.3 |                0 |             10 |                10 |                 nan |
| Corrective RAG          | revoked       |  10 |  42.6 |     38.5 |                0 |             40 |                50 |                  30 |
| Corrective RAG          | version_drift |  10 |  84.8 |     80.8 |                0 |            nan |               nan |                 nan |
| Corrective RAG          | withdrawn     |  10 |  80   |     80   |                0 |            100 |               100 |                  80 |
| Evidence-Aware Agent    | nvd_kev       |  10 | 100   |    100   |              nan |            100 |               100 |                 nan |
| Evidence-Aware Agent    | rev4_rev5     |  10 |  89.1 |     81.2 |                0 |            100 |               100 |                 nan |
| Evidence-Aware Agent    | revoked       |  10 |  88   |     83.6 |                0 |            100 |               100 |                 100 |
| Evidence-Aware Agent    | version_drift |  10 |  91.5 |     85.8 |                0 |            nan |               nan |                 nan |
| Evidence-Aware Agent    | withdrawn     |  10 | 100   |    100   |                0 |            100 |               100 |                 100 |
| Graph oracle (no LLM)   | nvd_kev       |  10 | 100   |    100   |              nan |              0 |                 0 |                 nan |
| Graph oracle (no LLM)   | rev4_rev5     |  10 | 100   |    100   |                0 |              0 |                 0 |                 nan |
| Graph oracle (no LLM)   | revoked       |  10 | 100   |    100   |                0 |            100 |               100 |                   0 |
| Graph oracle (no LLM)   | version_drift |  10 | 100   |    100   |                0 |            nan |               nan |                 nan |
| Graph oracle (no LLM)   | withdrawn     |  10 | 100   |    100   |                0 |            100 |               100 |                 100 |
| KG-RAG                  | nvd_kev       |  10 |  93.3 |     90   |              nan |              0 |                 0 |                 nan |
| KG-RAG                  | rev4_rev5     |  10 |  94   |     90.7 |               10 |             10 |                10 |                 nan |
| KG-RAG                  | revoked       |  10 |  83.8 |     75.1 |                0 |             40 |                60 |                  50 |
| KG-RAG                  | version_drift |  10 |  87.6 |     80   |                0 |            nan |               nan |                 nan |
| KG-RAG                  | withdrawn     |  10 |  96.7 |    100   |               10 |            100 |               100 |                 100 |
| Multi-hop RAG           | nvd_kev       |  10 |  80   |     70   |              nan |              0 |                 0 |                 nan |
| Multi-hop RAG           | rev4_rev5     |  10 |  58.9 |     59.3 |               10 |             20 |                20 |                 nan |
| Multi-hop RAG           | revoked       |  10 |  68.3 |     62.5 |                0 |             40 |                70 |                  60 |
| Multi-hop RAG           | version_drift |  10 |  93.4 |     88.3 |                0 |            nan |               nan |                 nan |
| Multi-hop RAG           | withdrawn     |  10 |  86.7 |     90   |               10 |            100 |               100 |                  90 |
| Naive RAG               | nvd_kev       |  10 |  80   |     70   |              nan |              0 |                 0 |                 nan |
| Naive RAG               | rev4_rev5     |  10 |  97.6 |     96.7 |               10 |             20 |                20 |                 nan |
| Naive RAG               | revoked       |  10 |  83.8 |     75.1 |                0 |             60 |                70 |                  50 |
| Naive RAG               | version_drift |  10 |  91.4 |     85   |                0 |            nan |               nan |                 nan |
| Naive RAG               | withdrawn     |  10 |  76.7 |     80   |               10 |            100 |               100 |                  80 |
| ReAct agent (no verif.) | nvd_kev       |  10 | 100   |    100   |              nan |            100 |               100 |                 nan |
| ReAct agent (no verif.) | rev4_rev5     |  10 |  71.4 |     66.7 |               20 |            100 |               100 |                 nan |
| ReAct agent (no verif.) | revoked       |  10 |  88   |     83.6 |                0 |            100 |               100 |                 100 |
| ReAct agent (no verif.) | version_drift |  10 |  91.5 |     85.8 |                0 |            nan |               nan |                 nan |
| ReAct agent (no verif.) | withdrawn     |  10 | 100   |    100   |                0 |            100 |               100 |                 100 |