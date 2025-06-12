-- ============================================================================
-- Performance Benchmark Queries for TMP_REAN_DF2
-- Ceramic reanalysis database with different analytical focus
-- Main tables: REAN_00 (location/admin), REAN_01 (ceramic data)
-- Note: No obsidian data, so using ceramic counts as proxy metrics
-- ============================================================================

-- CATEGORY: baseline
-- QUERY: 1.1
-- Full scan of primary administrative table
SELECT COUNT(*) FROM tmp_rean_df2."REAN_00";

-- CATEGORY: join_performance
-- QUERY: 2.1
-- Join main table with ceramic totals
-- Simple two-table join structure
SELECT
    r00.site,
    r00.subsite,
    r01."CerTot_REAN"
FROM tmp_rean_df2."REAN_00" as r00
JOIN tmp_rean_df2."REAN_01" as r01 ON r00.ssn = r01.ssn
WHERE r01."CerTot_REAN" IS NOT NULL
ORDER BY r01."CerTot_REAN" DESC;

-- CATEGORY: complex_filtering
-- QUERY: 3.1
-- Filter and aggregate ceramic data by location and year
-- Note: Using ceramic totals instead of obsidian for this schema
SELECT
    SUM(r01."CerTot_REAN") AS total_ceramics
FROM tmp_rean_df2."REAN_00" AS r00
JOIN tmp_rean_df2."REAN_01" AS r01 ON r00.ssn = r01.ssn
WHERE r00.unit = 'N1W4' AND r01."REAN_Year" = 96;