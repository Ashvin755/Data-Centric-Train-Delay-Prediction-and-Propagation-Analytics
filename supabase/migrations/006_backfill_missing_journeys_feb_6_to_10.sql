-- Migration: 006_backfill_missing_journeys_feb_6_to_10
-- Purpose: Add journey entries for Feb 6-10, 2026 gap when GitHub Actions was blocked
-- Note: Phase 2 will fetch historical data from RailRadar API and mark as completed

-- These journeys likely completed already. Phase 2 will:
-- 1. Fetch historical journey data from RailRadar API
-- 2. Check if journey reached destination  
-- 3. Extract route/station delay data into rail_data table
-- 4. Mark journey as completed

-- Add one_day train journeys (Feb 6-10)
INSERT INTO journey_status_flags (
    train_no,
    journey_date,
    flag,
    is_completed,
    is_abandoned,
    last_checked_at,
    created_at,
    updated_at
)
SELECT 
    t.train_no,
    d.date AS journey_date,
    0 AS flag,  -- Start at 0 so Phase 2 will process
    false AS is_completed,
    false AS is_abandoned,  -- Let Phase 2 determine final status
    NULL AS last_checked_at,  -- Never checked yet
    CURRENT_TIMESTAMP AS created_at,
    CURRENT_TIMESTAMP AS updated_at
FROM 
    train_info t
CROSS JOIN (
    SELECT '2026-02-06'::date AS date UNION ALL
    SELECT '2026-02-07'::date UNION ALL
    SELECT '2026-02-08'::date UNION ALL
    SELECT '2026-02-09'::date UNION ALL
    SELECT '2026-02-10'::date
) d
WHERE 
    t.journey_type = 'one_day'
    AND NOT EXISTS (
        SELECT 1 FROM journey_status_flags j
        WHERE j.train_no = t.train_no 
        AND j.journey_date = d.date
    );

-- Add multiple_day train journeys (Feb 6-10)
INSERT INTO journey_status_flags (
    train_no,
    journey_date,
    flag,
    is_completed,
    is_abandoned,
    last_checked_at,
    created_at,
    updated_at
)
SELECT 
    t.train_no,
    d.date AS journey_date,
    0 AS flag,  -- Start at 0 so Phase 2 will process
    false AS is_completed,
    false AS is_abandoned,  -- Let Phase 2 determine final status
    NULL AS last_checked_at,  -- Never checked yet
    CURRENT_TIMESTAMP AS created_at,
    CURRENT_TIMESTAMP AS updated_at
FROM 
    train_info t
CROSS JOIN (
    SELECT '2026-02-06'::date AS date UNION ALL
    SELECT '2026-02-07'::date UNION ALL
    SELECT '2026-02-08'::date UNION ALL
    SELECT '2026-02-09'::date UNION ALL
    SELECT '2026-02-10'::date
) d
WHERE 
    t.journey_type = 'multiple_day'
    AND NOT EXISTS (
        SELECT 1 FROM journey_status_flags j
        WHERE j.train_no = t.train_no 
        AND j.journey_date = d.date
    );

-- Verification queries (run after migration to confirm)
-- Expected result: 50 new rows (10 trains × 5 days)

-- Check inserted rows
-- SELECT 
--     journey_date,
--     COUNT(*) as journey_count,
--     SUM(CASE WHEN is_completed THEN 1 ELSE 0 END) as completed_count,
--     SUM(CASE WHEN is_abandoned THEN 1 ELSE 0 END) as abandoned_count
-- FROM journey_status_flags
-- WHERE journey_date BETWEEN '2026-02-06' AND '2026-02-10'
-- GROUP BY journey_date
-- ORDER BY journey_date;

-- Check which journeys Phase 2 will process
-- SELECT train_no, journey_date, flag, is_completed, is_abandoned
-- FROM journey_status_flags
-- WHERE journey_date BETWEEN '2026-02-06' AND '2026-02-10'
-- ORDER BY journey_date, train_no;

-- After next poll, check if data was collected:
-- SELECT 
--     j.journey_date,
--     COUNT(DISTINCT j.train_no) as journeys_tracked,
--     SUM(CASE WHEN j.is_completed THEN 1 ELSE 0 END) as completed,
--     COUNT(DISTINCT r.train_no) as trains_with_data
-- FROM journey_status_flags j
-- LEFT JOIN rail_data r ON j.train_no = r.train_no AND j.journey_date = r.journey_date
-- WHERE j.journey_date BETWEEN '2026-02-06' AND '2026-02-10'
-- GROUP BY j.journey_date
-- ORDER BY j.journey_date;

-- TOTAL EXPECTED CHANGES: 
-- - 50 new journey_status_flags rows (flag=0, is_completed=false, is_abandoned=false)
-- - After next poll: up to 50 journeys marked completed + rail_data entries
