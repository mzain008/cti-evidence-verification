**Outdated and conflicting evidence (%)**

| system               | subtype       |   n |    f1 |   recall |   stale_adoption |   flag_correct |   staleness_aware |   replacement_found |
|:---------------------|:--------------|----:|------:|---------:|-----------------:|---------------:|------------------:|--------------------:|
| − authority          | nvd_kev       |  10 |  80   |     70   |              nan |              0 |                 0 |                 nan |
| − authority          | rev4_rev5     |  10 |  89.1 |     81.2 |                0 |            100 |               100 |                 nan |
| − authority          | revoked       |  10 |  88   |     83.6 |                0 |            100 |               100 |                 100 |
| − authority          | version_drift |  10 |  91.5 |     85.8 |                0 |            nan |               nan |                 nan |
| − authority          | withdrawn     |  10 | 100   |    100   |                0 |            100 |               100 |                 100 |
| − graph tools        | nvd_kev       |  10 |  86.7 |     80   |              nan |            100 |               100 |                 nan |
| − graph tools        | rev4_rev5     |  10 |  23.6 |     14.4 |               10 |            100 |               100 |                 nan |
| − graph tools        | revoked       |  10 |  65.8 |     54.7 |                0 |            100 |               100 |                 100 |
| − graph tools        | version_drift |  10 |  83.6 |     75.8 |                0 |            nan |               nan |                 nan |
| − graph tools        | withdrawn     |  10 | 100   |    100   |                0 |            100 |               100 |                 100 |
| − temporal           | nvd_kev       |  10 | 100   |    100   |              nan |            100 |               100 |                 nan |
| − temporal           | rev4_rev5     |  10 |  79   |     74.7 |               20 |             10 |                10 |                 nan |
| − temporal           | revoked       |  10 |  79.2 |     70.4 |                0 |             60 |                90 |                  80 |
| − temporal           | version_drift |  10 |  87.6 |     80   |                0 |            nan |               nan |                 nan |
| − temporal           | withdrawn     |  10 |  80   |     80   |                0 |            100 |               100 |                  80 |
| Evidence-Aware Agent | nvd_kev       |  10 | 100   |    100   |              nan |            100 |               100 |                 nan |
| Evidence-Aware Agent | rev4_rev5     |  10 |  89.1 |     81.2 |                0 |            100 |               100 |                 nan |
| Evidence-Aware Agent | revoked       |  10 |  88   |     83.6 |                0 |            100 |               100 |                 100 |
| Evidence-Aware Agent | version_drift |  10 |  91.5 |     85.8 |                0 |            nan |               nan |                 nan |
| Evidence-Aware Agent | withdrawn     |  10 | 100   |    100   |                0 |            100 |               100 |                 100 |