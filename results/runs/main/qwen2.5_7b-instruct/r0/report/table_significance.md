**Evidence-Aware Agent vs each system, per track: paired tests, Holm-corrected within track**

| track    | baseline                | metric          |   n |   ref_mean |   baseline_mean |    diff | test    |      p |   p_holm |
|:---------|:------------------------|:----------------|----:|-----------:|----------------:|--------:|:--------|-------:|---------:|
| text     | Corrective RAG          | f1              |  40 |     0.3968 |          0.2446 |  0.1521 | perm    | 0.0015 |   0.03   |
| text     | Corrective RAG          | uar             |  29 |     0.4612 |          0.6437 | -0.1825 | perm    | 0.0183 |   0.3294 |
| text     | Corrective RAG          | evidence_recall |  60 |     0.4734 |          0.4278 |  0.0456 | perm    | 0.0299 |   0.5083 |
| text     | Corrective RAG          | claim_correct   |  20 |     0.95   |          0.7    |  0.25   | mcnemar | 0.0625 |   1      |
| text     | KG-RAG                  | f1              |  40 |     0.3968 |          0.4021 | -0.0053 | perm    | 0.8412 |   1      |
| text     | KG-RAG                  | uar             |  36 |     0.4688 |          0.5255 | -0.0567 | perm    | 0.3172 |   1      |
| text     | KG-RAG                  | evidence_recall |  60 |     0.4734 |          0.5126 | -0.0392 | perm    | 0.2376 |   1      |
| text     | KG-RAG                  | claim_correct   |  20 |     0.95   |          0.8    |  0.15   | mcnemar | 0.375  |   1      |
| text     | Multi-hop RAG           | f1              |  40 |     0.3968 |          0.3421 |  0.0547 | perm    | 0.2013 |   1      |
| text     | Multi-hop RAG           | uar             |  24 |     0.3958 |          0.3889 |  0.0069 | perm    | 1      |   1      |
| text     | Multi-hop RAG           | evidence_recall |  60 |     0.4734 |          0.4678 |  0.0056 | perm    | 0.8713 |   1      |
| text     | Multi-hop RAG           | claim_correct   |  20 |     0.95   |          0.7    |  0.25   | mcnemar | 0.125  |   1      |
| text     | Naive RAG               | f1              |  40 |     0.3968 |          0.3973 | -0.0005 | perm    | 0.9374 |   1      |
| text     | Naive RAG               | uar             |  28 |     0.3527 |          0.3661 | -0.0134 | perm    | 1      |   1      |
| text     | Naive RAG               | evidence_recall |  60 |     0.4734 |          0.4111 |  0.0623 | perm    | 0.0074 |   0.1406 |
| text     | Naive RAG               | claim_correct   |  20 |     0.95   |          0.8    |  0.15   | mcnemar | 0.375  |   1      |
| text     | ReAct agent (no verif.) | f1              |  40 |     0.3968 |          0.406  | -0.0092 | perm    | 0.5015 |   1      |
| text     | ReAct agent (no verif.) | uar             |  36 |     0.4688 |          0.4896 | -0.0208 | perm    | 0.6298 |   1      |
| text     | ReAct agent (no verif.) | evidence_recall |  60 |     0.4734 |          0.4734 |  0      | perm    | 1      |   1      |
| text     | ReAct agent (no verif.) | claim_correct   |  20 |     0.95   |          0.9    |  0.05   | mcnemar | 1      |   1      |
| evidence | Corrective RAG          | f1              |  70 |     0.9395 |          0.672  |  0.2676 | perm    | 0      |   0      |
| evidence | Corrective RAG          | uar             |  64 |     0      |          0.2344 | -0.2344 | perm    | 0.0002 |   0.003  |
| evidence | Corrective RAG          | evidence_recall | 110 |     1      |          0.7644 |  0.2356 | perm    | 0      |   0      |
| evidence | Corrective RAG          | claim_correct   |  50 |     1      |          0.62   |  0.38   | mcnemar | 0      |   0.0001 |
| evidence | Corrective RAG          | stale_adoption  |  34 |     0      |          0      |  0      | perm    | 1      |   1      |
| evidence | KG-RAG                  | f1              |  70 |     0.9395 |          0.9218 |  0.0178 | perm    | 0.3612 |   1      |
| evidence | KG-RAG                  | uar             |  70 |     0      |          0.0086 | -0.0086 | perm    | 0.5007 |   1      |
| evidence | KG-RAG                  | evidence_recall | 110 |     1      |          0.9861 |  0.0139 | perm    | 0.0594 |   0.7722 |
| evidence | KG-RAG                  | claim_correct   |  50 |     1      |          0.72   |  0.28   | mcnemar | 0.0001 |   0.0021 |
| evidence | KG-RAG                  | stale_adoption  |  34 |     0      |          0.0588 | -0.0588 | perm    | 0.4984 |   1      |
| evidence | Multi-hop RAG           | f1              |  70 |     0.9395 |          0.8247 |  0.1149 | perm    | 0.0015 |   0.021  |
| evidence | Multi-hop RAG           | uar             |  63 |     0      |          0.0259 | -0.0259 | perm    | 0.2514 |   1      |
| evidence | Multi-hop RAG           | evidence_recall | 110 |     1      |          0.8127 |  0.1873 | perm    | 0      |   0      |
| evidence | Multi-hop RAG           | claim_correct   |  50 |     1      |          0.64   |  0.36   | mcnemar | 0      |   0.0001 |
| evidence | Multi-hop RAG           | stale_adoption  |  34 |     0      |          0.0588 | -0.0588 | perm    | 0.4984 |   1      |
| evidence | Naive RAG               | f1              |  70 |     0.9395 |          0.8915 |  0.048  | perm    | 0.0925 |   1      |
| evidence | Naive RAG               | uar             |  70 |     0      |          0.0376 | -0.0376 | perm    | 0.1263 |   1      |
| evidence | Naive RAG               | evidence_recall | 110 |     1      |          0.7598 |  0.2402 | perm    | 0      |   0      |
| evidence | Naive RAG               | claim_correct   |  50 |     1      |          0.72   |  0.28   | mcnemar | 0.0001 |   0.0021 |
| evidence | Naive RAG               | stale_adoption  |  34 |     0      |          0.0588 | -0.0588 | perm    | 0.4999 |   1      |
| evidence | ReAct agent (no verif.) | f1              |  70 |     0.9395 |          0.9143 |  0.0253 | perm    | 0.062  |   0.7722 |
| evidence | ReAct agent (no verif.) | uar             |  68 |     0      |          0.004  | -0.004  | perm    | 0.2492 |   1      |
| evidence | ReAct agent (no verif.) | evidence_recall | 110 |     1      |          0.8663 |  0.1337 | perm    | 0      |   0      |
| evidence | ReAct agent (no verif.) | claim_correct   |  50 |     1      |          0.68   |  0.32   | mcnemar | 0      |   0.0005 |
| evidence | ReAct agent (no verif.) | stale_adoption  |  34 |     0      |          0.0588 | -0.0588 | perm    | 0.5005 |   1      |