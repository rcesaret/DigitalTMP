-- ============================================================================
-- Performance Benchmark Queries for TMP_DF8
-- Vertically partitioned schema with separate tables for different data aspects
-- Primary tables: v401 (location), v201 (admin), v301 (lithics)
-- ============================================================================

-- CATEGORY: baseline
-- QUERY: 1.1
-- Full scan of primary SSN master table
SELECT COUNT(*) FROM tmp_df8.ssn_master;

-- CATEGORY: join_performance
-- QUERY: 2.1
-- Join location info with obsidian artifact counts
-- Tests efficiency of vertical partitioning approach
SELECT
    t1."SITENUM",
    t2."OBSITOTS"
FROM tmp_df8.v401 AS t1
LEFT JOIN tmp_df8.v301 AS t2 ON t1."SSN" = t2."SSN"
WHERE t2."OBSITOTS" IS NOT NULL
ORDER BY t2."OBSITOTS" DESC;

-- CATEGORY: complex_filtering
-- QUERY: 3.1
-- Multi-table join with filtering and aggregation
-- Requires joining 3 vertically partitioned tables
SELECT
    SUM(t3."OBSIBLDS") AS total_obsidian_blades
FROM tmp_df8.v401 AS t1
JOIN tmp_df8.v201 AS t2 ON t1."SSN" = t2."SSN"
JOIN tmp_df8.v301 AS t3 ON t1."SSN" = t3."SSN"
WHERE t1."UNIT" = 'N1W4' AND t2."COLLYEAR" = 64;