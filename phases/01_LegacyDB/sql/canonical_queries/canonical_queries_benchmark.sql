-- ============================================================================
-- Performance Benchmark Queries for Benchmark Wide Tables
-- Single denormalized table with all data pre-joined
-- ============================================================================

-- CATEGORY: baseline
-- QUERY: 1.1
-- Full scan of wide table
SELECT COUNT(*) FROM public.wide_format_data;

-- CATEGORY: join_performance
-- QUERY: 2.1  
-- No joins needed - direct query on denormalized data
SELECT
    "site",
    "subsite", 
    "obsidianTot"
FROM public.wide_format_data
WHERE "obsidianTot" IS NOT NULL AND "obsidianTot" > 0
ORDER BY "obsidianTot" DESC;

-- CATEGORY: complex_filtering
-- QUERY: 3.1
-- Simple aggregation without joins
SELECT
    SUM("obsidianBlades") AS total_obsidian_blades
FROM public.wide_format_data
WHERE "unit" = 'N1W4' AND "collectionYear" = 64;