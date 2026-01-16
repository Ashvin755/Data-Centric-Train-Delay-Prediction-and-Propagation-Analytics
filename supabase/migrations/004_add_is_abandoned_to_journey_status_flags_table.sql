-- Add is_abandoned column to journey_status_flags table
-- Migration: 004_add_is_abandoned_to_journey_status_flags_table

ALTER TABLE journey_status_flags
ADD COLUMN is_abandoned BOOLEAN DEFAULT FALSE;

-- Create index for efficient queries on abandoned journeys
CREATE INDEX idx_journey_status_is_abandoned ON journey_status_flags(is_abandoned);
CREATE INDEX idx_journey_status_active ON journey_status_flags(train_no, journey_date) 
    WHERE is_abandoned = FALSE AND is_completed = FALSE;

-- Add comment describing the new column
COMMENT ON COLUMN journey_status_flags.is_abandoned IS 'Flag indicating if the journey has been abandoned (flag > max_flag and is_completed = FALSE). Used to stop polling the RailRadar API for this journey.';
