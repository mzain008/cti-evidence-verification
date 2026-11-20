| system             | conflicts                 |   n |   detected % |   resolved correctly % |
|:-------------------|:--------------------------|----:|-------------:|-----------------------:|
| naive              | real (NVD vs KEV)         |  14 |          0   |                   35.7 |
| naive              | synthetic (injected note) |  36 |         25   |                   97.2 |
| crag               | real (NVD vs KEV)         |  14 |          7.1 |                   42.9 |
| crag               | synthetic (injected note) |  36 |         13.9 |                   63.9 |
| react_agent        | real (NVD vs KEV)         |  14 |          0   |                   21.4 |
| react_agent        | synthetic (injected note) |  36 |          0   |                   97.2 |
| graph_verifier_v11 | real (NVD vs KEV)         |  14 |        100   |                   85.7 |
| graph_verifier_v11 | synthetic (injected note) |  36 |        100   |                  100   |
| evidence_agent_v11 | real (NVD vs KEV)         |  14 |        100   |                   85.7 |
| evidence_agent_v11 | synthetic (injected note) |  36 |        100   |                  100   |
| conflict_aware_rag | real (NVD vs KEV)         |  14 |        100   |                   21.4 |
| conflict_aware_rag | synthetic (injected note) |  36 |        100   |                   83.3 |