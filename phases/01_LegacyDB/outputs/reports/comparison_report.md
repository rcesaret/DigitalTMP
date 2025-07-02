# Database Comparison Report

_Generated on: 2025-07-02 16:34:48_


## 1. Executive Summary

| Database                      |   Database Size (MB) |   Table Count |   Total Estimated Rows |   JDI (Join Dependency Index) |   NF (Normalization Factor) |
|:------------------------------|---------------------:|--------------:|-----------------------:|------------------------------:|----------------------------:|
| TMP_DF10                      |                   64 |             9 |                 485797 |                        0.2778 |                      0.2485 |
| TMP_DF8                       |                   20 |            27 |                 136350 |                        0.0741 |                      0.2139 |
| TMP_DF9                       |                   28 |            62 |                 106109 |                        0.0719 |                      0.3503 |
| TMP_REAN_DF2                  |                   14 |            13 |                  65715 |                        0.1538 |                      0.1857 |
| tmp_benchmark_wide_numeric    |                   21 |             1 |                   5050 |                        0      |                    nan      |
| tmp_benchmark_wide_text_nulls |                   61 |             1 |                   5050 |                        0      |                    nan      |


## 2. Performance Benchmark Comparison

### At-a-Glance: Schema Efficiency Factor (Lower is Better)

This table shows how many times slower each database is compared to the fastest benchmark database for each query category. A value of 1.0 means it is as fast as the benchmark.

| database                      |   complex_filtering |   join_performance |
|:------------------------------|--------------------:|-------------------:|
| tmp_benchmark_wide_numeric    |                1.07 |               1.47 |
| tmp_benchmark_wide_text_nulls |                1    |               1    |


### Detailed Latency Breakdown (ms)

|                            |   tmp_benchmark_wide_numeric |   tmp_benchmark_wide_text_nulls |
|:---------------------------|-----------------------------:|--------------------------------:|
| ('baseline', 1.1)          |                            0 |                               0 |
| ('complex_filtering', 3.1) |                           16 |                              15 |
| ('join_performance', 2.1)  |                           47 |                              32 |


## 3. Run Metadata

- **Databases Processed**: ['TMP_DF10', 'TMP_DF8', 'TMP_DF9', 'TMP_REAN_DF2', 'tmp_benchmark_wide_numeric', 'tmp_benchmark_wide_text_nulls']
