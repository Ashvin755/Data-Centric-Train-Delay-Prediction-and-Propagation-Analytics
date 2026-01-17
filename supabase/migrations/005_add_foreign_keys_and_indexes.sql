-- Add foreign key constraints and indexes for referential integrity
-- Migration: 005_add_foreign_keys_and_indexes
-- SAFE FOR EXISTING DATA: Uses IF NOT EXISTS and handles existing constraints

-- Add foreign key from journey_status_flags to train_info (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_journey_train_info' 
        AND table_name = 'journey_status_flags'
    ) THEN
        ALTER TABLE journey_status_flags 
        ADD CONSTRAINT fk_journey_train_info 
        FOREIGN KEY (train_no) 
        REFERENCES train_info(train_no) 
        ON DELETE CASCADE;
        RAISE NOTICE 'Added foreign key: fk_journey_train_info';
    ELSE
        RAISE NOTICE 'Foreign key fk_journey_train_info already exists';
    END IF;
END $$;

-- Add foreign key from rail_data to train_info (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_rail_data_train_info' 
        AND table_name = 'rail_data'
    ) THEN
        ALTER TABLE rail_data 
        ADD CONSTRAINT fk_rail_data_train_info 
        FOREIGN KEY (train_no) 
        REFERENCES train_info(train_no) 
        ON DELETE CASCADE;
        RAISE NOTICE 'Added foreign key: fk_rail_data_train_info';
    ELSE
        RAISE NOTICE 'Foreign key fk_rail_data_train_info already exists';
    END IF;
END $$;

-- Add index for is_abandoned field (if not exists)
CREATE INDEX IF NOT EXISTS idx_journey_status_is_abandoned 
ON journey_status_flags(is_abandoned)
WHERE is_abandoned = FALSE;

-- Add composite index for Phase 2 query optimization (if not exists)
CREATE INDEX IF NOT EXISTS idx_journey_status_ongoing 
ON journey_status_flags(is_completed, is_abandoned, train_no)
WHERE is_completed = FALSE AND is_abandoned = FALSE;

-- Add comments
COMMENT ON CONSTRAINT fk_journey_train_info ON journey_status_flags IS 
'Foreign key ensuring journey_status_flags.train_no exists in train_info';

COMMENT ON CONSTRAINT fk_rail_data_train_info ON rail_data IS 
'Foreign key ensuring rail_data.train_no exists in train_info';
