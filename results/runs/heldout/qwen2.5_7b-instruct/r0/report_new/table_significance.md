**Evidence-Aware Agent vs each system, per track: paired tests, Holm-corrected within track**

| track    | baseline                | metric          |   n |   ref_mean |   baseline_mean |    diff | test    |      p |   p_holm |
|:---------|:------------------------|:----------------|----:|-----------:|----------------:|--------:|:--------|-------:|---------:|
| text     | Corrective RAG          | f1              |  20 |     0.4417 |          0.4724 | -0.0307 | perm    | 0.605  |   1      |
| text     | Corrective RAG          | uar             |  14 |     0.3571 |          0.2714 |  0.0857 | perm    | 0.4939 |   1      |
| text     | Corrective RAG          | evidence_recall |  30 |     0.585  |          0.47   |  0.115  | perm    | 0.0293 |   0.5567 |
| text     | Corrective RAG          | claim_correct   |  10 |     0.7    |          0.5    |  0.2    | mcnemar | 0.625  |   1      |
| text     | KG-RAG                  | f1              |  20 |     0.4417 |          0.3143 |  0.1274 | perm    | 0.254  |   1      |
| text     | KG-RAG                  | uar             |  17 |     0.4706 |          0.6176 | -0.1471 | perm    | 0.3776 |   1      |
| text     | KG-RAG                  | evidence_recall |  30 |     0.585  |          0.56   |  0.025  | perm    | 0.8139 |   1      |
| text     | KG-RAG                  | claim_correct   |  10 |     0.7    |          0.7    |  0      | mcnemar | 1      |   1      |
| text     | Multi-hop RAG           | f1              |  20 |     0.4417 |          0.3833 |  0.0583 | perm    | 0.502  |   1      |
| text     | Multi-hop RAG           | uar             |  12 |     0.3333 |          0.375  | -0.0417 | perm    | 1      |   1      |
| text     | Multi-hop RAG           | evidence_recall |  30 |     0.585  |          0.4933 |  0.0917 | perm    | 0.2164 |   1      |
| text     | Multi-hop RAG           | claim_correct   |  10 |     0.7    |          0.5    |  0.2    | mcnemar | 0.6875 |   1      |
| text     | Naive RAG               | f1              |  20 |     0.4417 |          0.4319 |  0.0098 | perm    | 0.9379 |   1      |
| text     | Naive RAG               | uar             |  15 |     0.4    |          0.3667 |  0.0333 | perm    | 1      |   1      |
| text     | Naive RAG               | evidence_recall |  30 |     0.585  |          0.4367 |  0.1483 | perm    | 0.0148 |   0.296  |
| text     | Naive RAG               | claim_correct   |  10 |     0.7    |          0.7    |  0      | mcnemar | 1      |   1      |
| text     | ReAct agent (no verif.) | f1              |  20 |     0.4417 |          0.4733 | -0.0317 | perm    | 0.499  |   1      |
| text     | ReAct agent (no verif.) | uar             |  18 |     0.4444 |          0.4167 |  0.0278 | perm    | 1      |   1      |
| text     | ReAct agent (no verif.) | evidence_recall |  30 |     0.585  |          0.585  |  0      | perm    | 1      |   1      |
| text     | ReAct agent (no verif.) | claim_correct   |  10 |     0.7    |          0.6    |  0.1    | mcnemar | 1      |   1      |
| evidence | Corrective RAG          | f1              |  29 |     0.9166 |          0.7218 |  0.1948 | perm    | 0.0204 |   0.3876 |
| evidence | Corrective RAG          | uar             |  28 |     0      |          0.2143 | -0.2143 | perm    | 0.0313 |   0.5634 |
| evidence | Corrective RAG          | evidence_recall |  49 |     1      |          0.7847 |  0.2153 | perm    | 0      |   0      |
| evidence | Corrective RAG          | claim_correct   |  20 |     1      |          0.55   |  0.45   | mcnemar | 0.0039 |   0.082  |
| evidence | Corrective RAG          | stale_adoption  |  12 |     0      |          0      |  0      | perm    | 1      |   1      |
| evidence | KG-RAG                  | f1              |  29 |     0.9166 |          0.8286 |  0.088  | perm    | 0.0487 |   0.8279 |
| evidence | KG-RAG                  | uar             |  28 |     0      |          0.0536 | -0.0536 | perm    | 0.5003 |   1      |
| evidence | KG-RAG                  | evidence_recall |  49 |     1      |          1      |  0      | perm    | 1      |   1      |
| evidence | KG-RAG                  | claim_correct   |  20 |     1      |          0.9    |  0.1    | mcnemar | 0.5    |   1      |
| evidence | KG-RAG                  | stale_adoption  |  12 |     0      |          0.0833 | -0.0833 | perm    | 1      |   1      |
| evidence | Multi-hop RAG           | f1              |  29 |     0.9166 |          0.7583 |  0.1583 | perm    | 0.0597 |   0.9552 |
| evidence | Multi-hop RAG           | uar             |  23 |     0      |          0.0062 | -0.0062 | perm    | 1      |   1      |
| evidence | Multi-hop RAG           | evidence_recall |  49 |     1      |          0.8092 |  0.1908 | perm    | 0      |   0      |
| evidence | Multi-hop RAG           | claim_correct   |  20 |     1      |          0.55   |  0.45   | mcnemar | 0.0039 |   0.082  |
| evidence | Multi-hop RAG           | stale_adoption  |  12 |     0      |          0      |  0      | perm    | 1      |   1      |
| evidence | Naive RAG               | f1              |  29 |     0.9166 |          0.9487 | -0.0321 | perm    | 0.3845 |   1      |
| evidence | Naive RAG               | uar             |  29 |     0      |          0      |  0      | perm    | 1      |   1      |
| evidence | Naive RAG               | evidence_recall |  49 |     1      |          0.7847 |  0.2153 | perm    | 0      |   0      |
| evidence | Naive RAG               | claim_correct   |  20 |     1      |          0.85   |  0.15   | mcnemar | 0.25   |   1      |
| evidence | Naive RAG               | stale_adoption  |  12 |     0      |          0      |  0      | perm    | 1      |   1      |
| evidence | ReAct agent (no verif.) | f1              |  29 |     0.9166 |          0.8884 |  0.0282 | perm    | 0.5002 |   1      |
| evidence | ReAct agent (no verif.) | uar             |  28 |     0      |          0.0179 | -0.0179 | perm    | 1      |   1      |
| evidence | ReAct agent (no verif.) | evidence_recall |  49 |     1      |          0.8656 |  0.1344 | perm    | 0.001  |   0.022  |
| evidence | ReAct agent (no verif.) | claim_correct   |  20 |     1      |          0.75   |  0.25   | mcnemar | 0.0625 |   0.9552 |
| evidence | ReAct agent (no verif.) | stale_adoption  |  12 |     0      |          0      |  0      | perm    | 1      |   1      |