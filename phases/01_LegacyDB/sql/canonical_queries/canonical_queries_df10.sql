-- noqa: disable=all
-- ============================================================================
-- Performance Benchmark Queries for TMP_DF10
-- Entity-Attribute-Value (EAV) like model with extreme normalization
-- Core tables: provTable, artifactTable, codeTable with corresponding codes
-- ============================================================================

-- CATEGORY: baseline
-- QUERY: 1.1
-- Full scan of primary provenience table
SELECT COUNT(*) FROM ${schema}."provTable";
-- END Query

-- CATEGORY: join_performance
-- QUERY: 2.1
-- Complex EAV query to retrieve obsidian counts by site
-- Requires joining through the artifact codes system
SELECT
    p."Site",
    p."Unit",
    a."Count"
FROM ${schema}."provTable" AS p
JOIN ${schema}."artifactTable" AS a ON p."SSN" = a."SSN"
JOIN ${schema}."artifactCodes" AS ac ON a."ArtCode2" = ac."Code"
WHERE ac."Description" = 'Obsidian' AND a."Count" > 0
ORDER BY a."Count" DESC;
-- END Query

-- CATEGORY: complex_filtering
-- QUERY: 3.1
-- Highly complex EAV query with multiple code lookups and filters
-- This demonstrates the extreme complexity of querying EAV models
SELECT
    SUM(a."Count") AS total_obsidian_blades
FROM ${schema}."provTable" p
JOIN ${schema}."artifactTable" a ON p."SSN" = a."SSN"
JOIN ${schema}."artifactCodes" ac1 ON a."ArtCode1" = ac1."Code"
JOIN ${schema}."artifactCodes" ac2 ON a."ArtCode2" = ac2."Code"
JOIN ${schema}."codeTable" ct ON p."SSN" = ct."SSN"
JOIN ${schema}."codeCodes" cc ON ct."Code" = cc."Code"
WHERE
    p."Unit" = 'N1W4'
    AND ac2."Description" = 'Obsidian'
    AND ac1."Description" = 'Lithic'
    AND ct."Variable" = 'collectionYear'
    AND cc."Description" = '1964';
-- END Query
