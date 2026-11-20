**Evidence-Aware Agent vs each system, per track: paired tests, Holm-corrected within track**

| track    | baseline                | metric          |   n |   ref_mean |   baseline_mean |    diff | test    |      p |   p_holm |
|:---------|:------------------------|:----------------|----:|-----------:|----------------:|--------:|:--------|-------:|---------:|
| text     | Corrective RAG          | f1              |  20 |     0.5    |          0.2986 |  0.2014 | perm    | 0.0614 |   0.9824 |
| text     | Corrective RAG          | uar             |  12 |     0.3333 |          0.4167 | -0.0833 | perm    | 1      |   1      |
| text     | Corrective RAG          | evidence_recall |  30 |     0.6591 |          0.4367 |  0.2224 | perm    | 0.0007 |   0.014  |
| text     | Corrective RAG          | claim_correct   |  10 |     0.5    |          0.2    |  0.3    | mcnemar | 0.375  |   1      |
| text     | KG-RAG                  | f1              |  20 |     0.5    |          0.4319 |  0.0681 | perm    | 0.4406 |   1      |
| text     | KG-RAG                  | uar             |  17 |     0.4118 |          0.4412 | -0.0294 | perm    | 1      |   1      |
| text     | KG-RAG                  | evidence_recall |  30 |     0.6591 |          0.56   |  0.0991 | perm    | 0.033  |   0.561  |
| text     | KG-RAG                  | claim_correct   |  10 |     0.5    |          0.1    |  0.4    | mcnemar | 0.2188 |   1      |
| text     | Multi-hop RAG           | f1              |  20 |     0.5    |          0.47   |  0.03   | perm    | 1      |   1      |
| text     | Multi-hop RAG           | uar             |  13 |     0.2308 |          0.2308 |  0      | perm    | 1      |   1      |
| text     | Multi-hop RAG           | evidence_recall |  30 |     0.6591 |          0.5167 |  0.1424 | perm    | 0.0115 |   0.207  |
| text     | Multi-hop RAG           | claim_correct   |  10 |     0.5    |          0.4    |  0.1    | mcnemar | 1      |   1      |
| text     | Naive RAG               | f1              |  20 |     0.5    |          0.3986 |  0.1014 | perm    | 0.2571 |   1      |
| text     | Naive RAG               | uar             |  14 |     0.4286 |          0.3571 |  0.0714 | perm    | 1      |   1      |
| text     | Naive RAG               | evidence_recall |  30 |     0.6591 |          0.4367 |  0.2224 | perm    | 0.0007 |   0.014  |
| text     | Naive RAG               | claim_correct   |  10 |     0.5    |          0      |  0.5    | mcnemar | 0.0625 |   0.9824 |
| text     | ReAct agent (no verif.) | f1              |  20 |     0.5    |          0.525  | -0.025  | perm    | 1      |   1      |
| text     | ReAct agent (no verif.) | uar             |  17 |     0.4118 |          0.3725 |  0.0392 | perm    | 1      |   1      |
| text     | ReAct agent (no verif.) | evidence_recall |  30 |     0.6591 |          0.6591 |  0      | perm    | 1      |   1      |
| text     | ReAct agent (no verif.) | claim_correct   |  10 |     0.5    |          0.1    |  0.4    | mcnemar | 0.125  |   1      |
| evidence | Corrective RAG          | f1              |  29 |     0.9388 |          0.7545 |  0.1843 | perm    | 0.0247 |   0.3952 |
| evidence | Corrective RAG          | uar             |  28 |     0      |          0.2113 | -0.2113 | perm    | 0.0077 |   0.1386 |
| evidence | Corrective RAG          | evidence_recall |  49 |     1      |          0.7847 |  0.2153 | perm    | 0      |   0      |
| evidence | Corrective RAG          | claim_correct   |  20 |     1      |          0.45   |  0.55   | mcnemar | 0.001  |   0.0195 |
| evidence | Corrective RAG          | stale_adoption  |  12 |     0      |          0.1667 | -0.1667 | perm    | 0.5027 |   1      |
| evidence | KG-RAG                  | f1              |  29 |     0.9388 |          0.846  |  0.0928 | perm    | 0.1539 |   1      |
| evidence | KG-RAG                  | uar             |  26 |     0      |          0.0385 | -0.0385 | perm    | 0.5092 |   1      |
| evidence | KG-RAG                  | evidence_recall |  49 |     1      |          1      |  0      | perm    | 1      |   1      |
| evidence | KG-RAG                  | claim_correct   |  20 |     1      |          0.4    |  0.6    | mcnemar | 0.0005 |   0.0103 |
| evidence | KG-RAG                  | stale_adoption  |  12 |     0      |          0.1667 | -0.1667 | perm    | 0.496  |   1      |
| evidence | Multi-hop RAG           | f1              |  29 |     0.9388 |          0.7437 |  0.1951 | perm    | 0.0168 |   0.2856 |
| evidence | Multi-hop RAG           | uar             |  25 |     0      |          0.1067 | -0.1067 | perm    | 0.1259 |   1      |
| evidence | Multi-hop RAG           | evidence_recall |  49 |     1      |          0.8262 |  0.1738 | perm    | 0      |   0      |
| evidence | Multi-hop RAG           | claim_correct   |  20 |     1      |          0.55   |  0.45   | mcnemar | 0.0039 |   0.0742 |
| evidence | Multi-hop RAG           | stale_adoption  |  12 |     0      |          0.1667 | -0.1667 | perm    | 0.5011 |   1      |
| evidence | Naive RAG               | f1              |  29 |     0.9388 |          0.828  |  0.1108 | perm    | 0.1103 |   1      |
| evidence | Naive RAG               | uar             |  29 |     0      |          0.1429 | -0.1429 | perm    | 0.0291 |   0.4365 |
| evidence | Naive RAG               | evidence_recall |  49 |     1      |          0.7847 |  0.2153 | perm    | 0      |   0      |
| evidence | Naive RAG               | claim_correct   |  20 |     1      |          0.3    |  0.7    | mcnemar | 0.0001 |   0.0027 |
| evidence | Naive RAG               | stale_adoption  |  12 |     0      |          0.1667 | -0.1667 | perm    | 0.5011 |   1      |
| evidence | ReAct agent (no verif.) | f1              |  29 |     0.9388 |          0.9342 |  0.0046 | perm    | 1      |   1      |
| evidence | ReAct agent (no verif.) | uar             |  29 |     0      |          0.0115 | -0.0115 | perm    | 1      |   1      |
| evidence | ReAct agent (no verif.) | evidence_recall |  49 |     1      |          0.9827 |  0.0173 | perm    | 0.4891 |   1      |
| evidence | ReAct agent (no verif.) | claim_correct   |  20 |     1      |          0.7    |  0.3    | mcnemar | 0.0312 |   0.4375 |
| evidence | ReAct agent (no verif.) | stale_adoption  |  12 |     0      |          0      |  0      | perm    | 1      |   1      |