-- Create journey_status_flags table for tracking train journey completion status
-- Migration: 002_create_journey_status_flags_table

CREATE TABLE IF NOT EXISTS journey_status_flags (
    id BIGSERIAL PRIMARY KEY,
    train_no INT NOT NULL,
    journey_date DATE NOT NULL,
    flag INT NOT NULL DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    last_checked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint to ensure one entry per train journey
    UNIQUE(train_no, journey_date),
    
    -- Constraints for data validity
    CONSTRAINT valid_train_no CHECK (train_no > 0),
    CONSTRAINT valid_flag CHECK (flag >= 0)
);

-- Create indexes for efficient queries
CREATE INDEX idx_journey_status_train_no ON journey_status_flags(train_no);
CREATE INDEX idx_journey_status_journey_date ON journey_status_flags(journey_date);
CREATE INDEX idx_journey_status_is_completed ON journey_status_flags(is_completed);
CREATE INDEX idx_journey_status_train_journey ON journey_status_flags(train_no, journey_date);
CREATE INDEX idx_journey_status_incomplete ON journey_status_flags(train_no, journey_date) 
    WHERE is_completed = FALSE;

-- Add comments describing the table
COMMENT ON TABLE journey_status_flags IS 'Tracks the polling status and completion flag for each train journey';
COMMENT ON COLUMN journey_status_flags.train_no IS '5-digit train number';
COMMENT ON COLUMN journey_status_flags.journey_date IS 'Date of the train journey (YYYY-MM-DD)';
COMMENT ON COLUMN journey_status_flags.flag IS 'Counter tracking number of polling attempts or checks';
COMMENT ON COLUMN journey_status_flags.is_completed IS 'Flag indicating if the journey has been completed and data written to rail_data table';
COMMENT ON COLUMN journey_status_flags.last_checked_at IS 'Timestamp of the last polling/status check';
