-- noqa: disable=all
-- ============================================================================
-- Performance Benchmark Queries for TMP_DF8
-- Vertically partitioned schema with separate tables for different data aspects
-- Primary tables: v401 (location), v201 (admin), v301 (lithics)
-- ============================================================================

-- CATEGORY: baseline
-- QUERY: 1.1
-- Full scan of primary SSN master table
SELECT COUNT(*) FROM ${schema}."ssn_master";
-- END Query

-- CATEGORY: join_performance
-- QUERY: 2.1
-- Join location info with obsidian artifact counts
-- Tests efficiency of vertical partitioning approach
SELECT
    t1."subsite",
    t1."obsitots"
FROM ${schema}."v401" AS t1
LEFT JOIN ${schema}."v301" AS t2 ON t1."ssn" = t2."ssn"
WHERE t1."obsitots" IS NOT NULL
ORDER BY t1."obsitots" DESC;
-- END Query

-- CATEGORY: complex_filtering
-- QUERY: 3.1
-- Multi-table join with filtering and aggregation
-- Requires joining 3 vertically partitioned tables
SELECT
    SUM(t3."obsiblds") AS total_obsidian_blades
FROM ${schema}."v401" AS t1
JOIN ${schema}."v201" AS t2 ON t1."ssn" = t2."ssn"
JOIN ${schema}."v301" AS t3 ON t1."ssn" = t3."ssn"
WHERE t1."unit" = 'N1W4' AND t2."collyear" = 64;
-- END Query
