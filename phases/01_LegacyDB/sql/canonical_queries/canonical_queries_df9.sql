-- noqa: disable=all
-- ============================================================================
-- Performance Benchmark Queries for TMP_DF9
-- Highly normalized schema with 18 core tables + 45 lookup tables
-- ============================================================================

-- CATEGORY: baseline
-- QUERY: 1.1
-- Full scan of primary location table
SELECT COUNT(*) FROM ${schema}."location";
-- END Query

-- CATEGORY: join_performance
-- QUERY: 2.1
-- Complex 5-table join to retrieve complete site profile with obsidian counts
SELECT
    loc."site",
    loc."subsite",
    lith."obsidianTot"
FROM ${schema}."location" AS loc
JOIN ${schema}."description" AS des ON loc."SSN" = des."SSN"
JOIN ${schema}."archInterp" AS interp ON loc."SSN" = interp."SSN"
JOIN ${schema}."lithicFlaked" AS lith ON loc."SSN" = lith."SSN"
JOIN ${schema}."admin" AS adm ON loc."SSN" = adm."SSN"
WHERE lith."obsidianTot" IS NOT NULL AND lith."obsidianTot" > 0
ORDER BY lith."obsidianTot" DESC;
-- END Query

-- CATEGORY: complex_filtering
-- QUERY: 3.1
-- Filter and aggregate with multiple joins and conditions
SELECT
    SUM(lith."obsidianBlades") AS total_obsidian_blades
FROM ${schema}."location" AS loc
JOIN ${schema}."admin" AS adm ON loc."SSN" = adm."SSN"
JOIN ${schema}."lithicFlaked" AS lith ON loc."SSN" = lith."SSN"
WHERE loc."unit" = 'N1W4' AND adm."collectionYear" = 64;
-- END Query
