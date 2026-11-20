**Outdated and conflicting evidence (%)**

| system                  | subtype       |   n |    f1 |   recall |   stale_adoption |   flag_correct |   staleness_aware |   replacement_found |
|:------------------------|:--------------|----:|------:|---------:|-----------------:|---------------:|------------------:|--------------------:|
| Corrective RAG          | nvd_kev       |  10 |  46.7 |     45   |              nan |              0 |                 0 |                 nan |
| Corrective RAG          | rev4_rev5     |  10 |  98.3 |    100   |               20 |              0 |                 0 |                 nan |
| Corrective RAG          | revoked       |  10 |  35.6 |     31.5 |                0 |             10 |                10 |                  10 |
| Corrective RAG          | version_drift |  10 |  97.1 |     95   |                0 |            nan |               nan |                 nan |
| Corrective RAG          | withdrawn     |  10 |  33.3 |     50   |               70 |            100 |               100 |                  60 |
| Evidence-Aware Agent    | nvd_kev       |  10 |  73.3 |     60   |              nan |            100 |               100 |                 nan |
| Evidence-Aware Agent    | rev4_rev5     |  10 |  91.6 |     86.4 |                0 |            100 |               100 |                 nan |
| Evidence-Aware Agent    | revoked       |  10 |  91.7 |     88.3 |                0 |            100 |               100 |                   0 |
| Evidence-Aware Agent    | version_drift |  10 |  95.2 |     92.5 |                0 |            nan |               nan |                 nan |
| Evidence-Aware Agent    | withdrawn     |  10 | 100   |    100   |                0 |            100 |               100 |                 100 |
| Graph oracle (no LLM)   | nvd_kev       |  10 | 100   |    100   |              nan |              0 |                 0 |                 nan |
| Graph oracle (no LLM)   | rev4_rev5     |  10 | 100   |    100   |                0 |              0 |                 0 |                 nan |
| Graph oracle (no LLM)   | revoked       |  10 | 100   |    100   |                0 |            100 |               100 |                   0 |
| Graph oracle (no LLM)   | version_drift |  10 | 100   |    100   |                0 |            nan |               nan |                 nan |
| Graph oracle (no LLM)   | withdrawn     |  10 | 100   |    100   |                0 |            100 |               100 |                 100 |
| KG-RAG                  | nvd_kev       |  10 |  83.3 |     75   |              nan |             10 |                10 |                 nan |
| KG-RAG                  | rev4_rev5     |  10 |  65.9 |     65.6 |               20 |              0 |                 0 |                 nan |
| KG-RAG                  | revoked       |  10 |  69.8 |     64.2 |                0 |             10 |                10 |                  10 |
| KG-RAG                  | version_drift |  10 |  95.7 |     92.5 |                0 |            nan |               nan |                 nan |
| KG-RAG                  | withdrawn     |  10 |  96.7 |    100   |               10 |            100 |               100 |                 100 |
| Multi-hop RAG           | nvd_kev       |  10 |  90   |     85   |              nan |              0 |                 0 |                 nan |
| Multi-hop RAG           | rev4_rev5     |  10 |  57.4 |     60   |               20 |             10 |                10 |                 nan |
| Multi-hop RAG           | revoked       |  10 |  87.2 |     81   |                0 |             20 |                20 |                  10 |
| Multi-hop RAG           | version_drift |  10 |  95.7 |     92.5 |                0 |            nan |               nan |                 nan |
| Multi-hop RAG           | withdrawn     |  10 |  80   |     80   |               10 |            100 |               100 |                  90 |
| Naive RAG               | nvd_kev       |  10 |  86.7 |     80   |              nan |              0 |                 0 |                 nan |
| Naive RAG               | rev4_rev5     |  10 |  89   |     90   |               10 |              0 |                 0 |                 nan |
| Naive RAG               | revoked       |  10 |  85.8 |     78.5 |                0 |             30 |                30 |                   0 |
| Naive RAG               | version_drift |  10 |  94.7 |     91.7 |                0 |            nan |               nan |                 nan |
| Naive RAG               | withdrawn     |  10 |  10   |     10   |               60 |            100 |               100 |                  60 |
| ReAct agent (no verif.) | nvd_kev       |  10 |  73.3 |     60   |              nan |            100 |               100 |                 nan |
| ReAct agent (no verif.) | rev4_rev5     |  10 |  87.9 |     86.4 |               10 |            100 |               100 |                 nan |
| ReAct agent (no verif.) | revoked       |  10 |  91   |     88.3 |                0 |            100 |               100 |                   0 |
| ReAct agent (no verif.) | version_drift |  10 |  95.2 |     92.5 |                0 |            nan |               nan |                 nan |
| ReAct agent (no verif.) | withdrawn     |  10 | 100   |    100   |                0 |            100 |               100 |                 100 |