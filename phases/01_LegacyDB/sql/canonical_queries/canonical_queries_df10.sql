-- ============================================================================
-- Performance Benchmark Queries for TMP_DF10
-- Entity-Attribute-Value (EAV) like model with extreme normalization
-- Core tables: provTable, artifactTable, codeTable with corresponding codes
-- ============================================================================

-- CATEGORY: baseline
-- QUERY: 1.1
-- Full scan of primary provenience table
SELECT COUNT(*) FROM tmp_df10."provTable";

-- CATEGORY: join_performance
-- QUERY: 2.1
-- Complex EAV query to retrieve obsidian counts by site
-- Requires joining through the artifact codes system
SELECT
    p."Site",
    p."Unit",
    a."Count"
FROM tmp_df10."provTable" AS p
JOIN tmp_df10."artifactTable" AS a ON p."SSN" = a."SSN"
JOIN tmp_df10."artifactCodes" AS ac ON a."ArtCode2" = ac."Code"
WHERE ac."Description" = 'Obsidian' AND a."Count" > 0
ORDER BY a."Count" DESC;

-- CATEGORY: complex_filtering
-- QUERY: 3.1
-- Highly complex EAV query with multiple code lookups and filters
-- This demonstrates the extreme complexity of querying EAV models
SELECT
    SUM(a."Count") AS total_obsidian_blades
FROM tmp_df10."provTable" p
JOIN tmp_df10."artifactTable" a ON p."SSN" = a."SSN"
JOIN tmp_df10."artifactCodes" ac1 ON a."ArtCode1" = ac1."Code"
JOIN tmp_df10."artifactCodes" ac2 ON a."ArtCode2" = ac2."Code"
JOIN tmp_df10."codeTable" ct ON p."SSN" = ct."SSN"
JOIN tmp_df10."codeCodes" cc ON ct."Code" = cc."Code"
WHERE
    p."Unit" = 'N1W4'
    AND ac2."Description" = 'Obsidian'
    AND ac1."Description" = 'Lithic'
    AND ct."Variable" = 'collectionYear' 
    AND cc."Description" = '1964';