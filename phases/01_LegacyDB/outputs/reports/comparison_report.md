# Database Comparison Report

_Generated on: 2025-07-06 22:17:55_


## 1. Executive Summary

| Database                      |   Database Size (MB) |   Table Count |   Total Estimated Rows |   JDI (Join Dependency Index) |   NF (Normalization Factor) |
|:------------------------------|---------------------:|--------------:|-----------------------:|------------------------------:|----------------------------:|
| TMP_DF10                      |                   64 |             9 |                 485797 |                        0.2778 |                      0.2485 |
| TMP_DF8                       |                   20 |            27 |                 136350 |                        0.0741 |                      0.2139 |
| TMP_DF9                       |                   28 |            62 |                 106109 |                        0.0719 |                      0.3503 |
| TMP_REAN_DF2                  |                   14 |            13 |                  65715 |                        0.1538 |                      0.1857 |
| tmp_benchmark_wide_numeric    |                   21 |             1 |                   5050 |                      nan      |                    nan      |
| tmp_benchmark_wide_text_nulls |                   61 |             1 |                   5050 |                      nan      |                    nan      |


## 2. Performance Benchmark Comparison

### At-a-Glance: Schema Efficiency Factor (Lower is Better)

This table shows how many times slower each database is compared to the fastest benchmark database for each query category. A value of 1.0 means it is as fast as the benchmark.

| database                      |   Baseline Performance |   Complex_filtering Performance |   Join_performance Performance |
|:------------------------------|-----------------------:|--------------------------------:|-------------------------------:|
| TMP_DF10                      |                   0.49 |                            2.51 |                           2.27 |
| TMP_DF8                       |                   0.42 |                            1.15 |                           0.31 |
| TMP_DF9                       |                   0.43 |                            0.68 |                           0.52 |
| TMP_REAN_DF2                  |                   0.5  |                            0.4  |                           0.35 |
| tmp_benchmark_wide_numeric    |                   1.09 |                            1    |                           1    |
| tmp_benchmark_wide_text_nulls |                   1    |                            1.43 |                           1.03 |


### Detailed Latency Breakdown (ms)

|                                                |   TMP_DF10 |   TMP_DF8 |   TMP_DF9 |   TMP_REAN_DF2 |   tmp_benchmark_wide_numeric |   tmp_benchmark_wide_text_nulls |
|:-----------------------------------------------|-----------:|----------:|----------:|---------------:|-----------------------------:|--------------------------------:|
| ('Baseline Performance', 'Query 1.1')          |       0.95 |      0.81 |      0.82 |           0.96 |                         2.11 |                            1.93 |
| ('Complex_filtering Performance', 'Query 3.1') |       7.9  |      3.6  |      2.13 |           1.27 |                         3.14 |                            4.5  |
| ('Join_performance Performance', 'Query 2.1')  |      52.78 |      7.11 |     12.11 |           8.04 |                        23.21 |                           23.8  |


## 3. Run Metadata

- **Databases Processed**: ['TMP_DF10', 'TMP_DF8', 'TMP_DF9', 'TMP_REAN_DF2', 'tmp_benchmark_wide_numeric', 'tmp_benchmark_wide_text_nulls']
