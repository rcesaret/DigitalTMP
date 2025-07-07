# Database Comparison Report

_Generated on: 2025-07-07 15:05:21_


## 1. Executive Summary

| Database                      |   Database Size (MB) |   Table Count |   Total Estimated Rows |   JDI (Join Dependency Index) |   NF (Normalization Factor) |
|:------------------------------|---------------------:|--------------:|-----------------------:|------------------------------:|----------------------------:|
| TMP_DF10                      |                   64 |             9 |                 485797 |                        0.2778 |                      0.2485 |
| TMP_DF8                       |                   20 |            27 |                 136350 |                        0.0741 |                      0.2139 |
| TMP_DF9                       |                   28 |            62 |                 106109 |                        0.0719 |                      0.3503 |
| TMP_REAN_DF2                  |                   14 |            13 |                  65715 |                        0.1538 |                      0.1857 |
| tmp_benchmark_wide_numeric    |                   21 |             1 |                   5050 |                      nan      |                    nan      |
| tmp_benchmark_wide_text_nulls |                   62 |             1 |                   5050 |                      nan      |                    nan      |


## 2. Performance Benchmark Comparison

### At-a-Glance: Schema Efficiency Factor (Lower is Better)

This table shows how many times slower each database is compared to the fastest benchmark database for each query category. A value of 1.0 means it is as fast as the benchmark.

| database                      |   Baseline Performance |   Complex_filtering Performance |   Join_performance Performance |
|:------------------------------|-----------------------:|--------------------------------:|-------------------------------:|
| TMP_DF10                      |                   1.04 |                            4.58 |                           5.46 |
| TMP_DF8                       |                   0.69 |                            4.38 |                           0.58 |
| TMP_DF9                       |                   1.05 |                            1.34 |                           1.56 |
| TMP_REAN_DF2                  |                   0.62 |                            1.11 |                           0.86 |
| tmp_benchmark_wide_numeric    |                   1    |                            1.29 |                           1    |
| tmp_benchmark_wide_text_nulls |                   1.37 |                            1    |                           1.34 |


### Detailed Latency Breakdown (ms)

|                                                |   TMP_DF10 |   TMP_DF8 |   TMP_DF9 |   TMP_REAN_DF2 |   tmp_benchmark_wide_numeric |   tmp_benchmark_wide_text_nulls |
|:-----------------------------------------------|-----------:|----------:|----------:|---------------:|-----------------------------:|--------------------------------:|
| ('Baseline Performance', 'Query 1.1')          |       1.54 |      1.02 |      1.55 |           0.91 |                         1.48 |                            2.03 |
| ('Complex_filtering Performance', 'Query 3.1') |       8.88 |      8.48 |      2.6  |           2.14 |                         2.5  |                            1.94 |
| ('Join_performance Performance', 'Query 2.1')  |      65.63 |      6.98 |     18.77 |          10.29 |                        12.03 |                           16.12 |


## 3. Run Metadata

- **Databases Processed**: ['TMP_DF10', 'TMP_DF8', 'TMP_DF9', 'TMP_REAN_DF2', 'tmp_benchmark_wide_numeric', 'tmp_benchmark_wide_text_nulls']
