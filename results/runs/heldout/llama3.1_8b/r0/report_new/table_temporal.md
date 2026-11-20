**Outdated and conflicting evidence (%)**

| system                  | subtype       |   n |    f1 |   recall |   stale_adoption |   flag_correct |   staleness_aware |   replacement_found |
|:------------------------|:--------------|----:|------:|---------:|-----------------:|---------------:|------------------:|--------------------:|
| Corrective RAG          | nvd_kev       |   3 |  60   |     55.6 |            nan   |              0 |                 0 |               nan   |
| Corrective RAG          | rev4_rev5     |   3 | 100   |    100   |              0   |              0 |                 0 |               nan   |
| Corrective RAG          | revoked       |   5 |  73.3 |     80   |              0   |             20 |                40 |                20   |
| Corrective RAG          | version_drift |   5 |  93.1 |     93.3 |            100   |            nan |               nan |               nan   |
| Corrective RAG          | withdrawn     |   3 |   0   |      0   |             33.3 |            100 |               100 |                33.3 |
| Evidence-Aware Agent    | nvd_kev       |   3 |  71.1 |     55.6 |            nan   |            100 |               100 |               nan   |
| Evidence-Aware Agent    | rev4_rev5     |   3 |  83.1 |     72.5 |              0   |            100 |               100 |               nan   |
| Evidence-Aware Agent    | revoked       |   5 |  96   |     93.3 |              0   |            100 |               100 |                 0   |
| Evidence-Aware Agent    | version_drift |   5 | 100   |    100   |              0   |            nan |               nan |               nan   |
| Evidence-Aware Agent    | withdrawn     |   3 | 100   |    100   |              0   |            100 |               100 |               100   |
| Graph oracle (no LLM)   | nvd_kev       |   3 | 100   |    100   |            nan   |              0 |                 0 |               nan   |
| Graph oracle (no LLM)   | rev4_rev5     |   3 | 100   |    100   |              0   |              0 |                 0 |               nan   |
| Graph oracle (no LLM)   | revoked       |   5 | 100   |    100   |              0   |            100 |               100 |                 0   |
| Graph oracle (no LLM)   | version_drift |   5 | 100   |    100   |              0   |            nan |               nan |               nan   |
| Graph oracle (no LLM)   | withdrawn     |   3 | 100   |    100   |              0   |            100 |               100 |               100   |
| KG-RAG                  | nvd_kev       |   3 |  93.3 |     88.9 |            nan   |              0 |                 0 |               nan   |
| KG-RAG                  | rev4_rev5     |   3 |  33.3 |     33.3 |              0   |              0 |                 0 |               nan   |
| KG-RAG                  | revoked       |   5 |  73.3 |     80   |             20   |              0 |                 0 |                 0   |
| KG-RAG                  | version_drift |   5 |  92   |     86.7 |              0   |            nan |               nan |               nan   |
| KG-RAG                  | withdrawn     |   3 |  88.9 |    100   |             33.3 |            100 |               100 |               100   |
| Multi-hop RAG           | nvd_kev       |   3 |  73.3 |     72.2 |            nan   |              0 |                 0 |               nan   |
| Multi-hop RAG           | rev4_rev5     |   3 |  66.7 |     66.7 |              0   |              0 |                 0 |               nan   |
| Multi-hop RAG           | revoked       |   5 |  93.3 |    100   |             20   |             20 |                20 |                 0   |
| Multi-hop RAG           | version_drift |   5 |  84   |     80   |            100   |            nan |               nan |               nan   |
| Multi-hop RAG           | withdrawn     |   3 | 100   |    100   |              0   |            100 |               100 |               100   |
| Naive RAG               | nvd_kev       |   3 |  93.3 |     88.9 |            nan   |              0 |                 0 |               nan   |
| Naive RAG               | rev4_rev5     |   3 | 100   |    100   |              0   |              0 |                 0 |               nan   |
| Naive RAG               | revoked       |   5 |  93.3 |    100   |             20   |             20 |                20 |                 0   |
| Naive RAG               | version_drift |   5 |  84   |     80   |            100   |            nan |               nan |               nan   |
| Naive RAG               | withdrawn     |   3 |   0   |      0   |              0   |            100 |               100 |                33.3 |
| ReAct agent (no verif.) | nvd_kev       |   3 |  71.1 |     55.6 |            nan   |            100 |               100 |               nan   |
| ReAct agent (no verif.) | rev4_rev5     |   3 |  83.1 |     72.5 |              0   |            100 |               100 |               nan   |
| ReAct agent (no verif.) | revoked       |   5 |  93.3 |     93.3 |              0   |            100 |               100 |                 0   |
| ReAct agent (no verif.) | version_drift |   5 | 100   |    100   |              0   |            nan |               nan |               nan   |
| ReAct agent (no verif.) | withdrawn     |   3 | 100   |    100   |              0   |            100 |               100 |               100   |