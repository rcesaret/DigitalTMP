-- ============================================================================
-- Performance Benchmark Queries for TMP_DF9
-- Highly normalized schema with 18 core tables + 45 lookup tables
-- ============================================================================

-- CATEGORY: baseline
-- QUERY: 1.1
-- Full scan of primary location table
SELECT COUNT(*) FROM tmp_df9.location;

-- CATEGORY: join_performance  
-- QUERY: 2.1
-- Complex 5-table join to retrieve complete site profile with obsidian counts
SELECT
    loc.site,
    loc.subsite,
    lith.obsidianTot
FROM tmp_df9.location AS loc
JOIN tmp_df9.description AS des ON loc."SSN" = des."SSN"
JOIN tmp_df9.archInterp AS interp ON loc."SSN" = interp."SSN"
JOIN tmp_df9.lithicFlaked AS lith ON loc."SSN" = lith."SSN"
JOIN tmp_df9.admin AS adm ON loc."SSN" = adm."SSN"
WHERE lith.obsidianTot IS NOT NULL AND lith.obsidianTot > 0
ORDER BY lith.obsidianTot DESC;

-- CATEGORY: complex_filtering
-- QUERY: 3.1
-- Filter and aggregate with multiple joins and conditions
SELECT
    SUM(lith."obsidianBlades") AS total_obsidian_blades
FROM tmp_df9.location AS loc
JOIN tmp_df9.admin AS adm ON loc."SSN" = adm."SSN"
JOIN tmp_df9.lithicFlaked AS lith ON loc."SSN" = lith."SSN"
WHERE loc.unit = 'N1W4' AND adm."collectionYear" = 64;