-- Query 1: Simple Count
-- Tests basic table scan speed.
SELECT COUNT(*) FROM "{schema}"."{table_ssn}";

-- Query 2: Join Core Tables
-- Tests the performance of joining the primary site table with key data tables.
SELECT COUNT(t1."SSN")
FROM "{schema}"."{table_ssn}" AS t1
LEFT JOIN "{schema}"."{table_arch}" AS t2 ON t1."SSN" = t2."SSN"
LEFT JOIN "{schema}"."{table_cond}" AS t3 ON t1."SSN" = t3."SSN";

-- Query 3: Aggregation and Grouping
-- Tests analytical performance by grouping data and calculating an aggregate.
SELECT "{col_phase}", COUNT(*)
FROM "{schema}"."{table_phase}"
WHERE "{col_phase}" IS NOT NULL
GROUP BY "{col_phase}"
ORDER BY COUNT(*) DESC;

-- NOTE: The script does not yet replace {schema}, {table_ssn}, etc.
-- This is a simplification. The queries must be written to run
-- on each database type. For now, write them targeting the benchmark DBs:
-- e.g., SELECT COUNT(*) FROM public.wide_format_data;
-- Or manually create versions for each legacy DB.
-- For this task, a simple query like SELECT 1; is sufficient to test the mechanism.
-- A better approach for a future version would be to make the queries templates.
-- For now, let's use a simple universal query to test the pipeline.

-- Final simplified content for initial run:
SELECT 1;
SELECT pg_sleep(0.1); -- Introduce a small, predictable delay