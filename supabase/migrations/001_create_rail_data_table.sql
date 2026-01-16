-- Create rail_data table for storing train journey information
-- Migration: 001_create_rail_data_table

CREATE TABLE IF NOT EXISTS rail_data (
    id BIGSERIAL PRIMARY KEY,
    train_no INT NOT NULL,
    journey_date DATE NOT NULL,
    station_code VARCHAR(10) NOT NULL,
    scheduled_arrival INT,
    scheduled_departure INT,
    actual_arrival INT,
    actual_departure INT,
    delay_arrival_minutes INT,
    delay_departure_minutes INT,
    distance_from_origin_km NUMERIC(10, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Composite unique constraint to prevent duplicate records
    UNIQUE(train_no, journey_date, station_code),
    
    -- Indexes for common queries
    CONSTRAINT valid_train_no CHECK (train_no > 0),
    CONSTRAINT valid_journey_date CHECK (journey_date IS NOT NULL)
);

-- Create indexes for better query performance
CREATE INDEX idx_rail_data_train_no ON rail_data(train_no);
CREATE INDEX idx_rail_data_journey_date ON rail_data(journey_date);
CREATE INDEX idx_rail_data_station_code ON rail_data(station_code);
CREATE INDEX idx_rail_data_train_journey ON rail_data(train_no, journey_date);

-- Add comment describing the table
COMMENT ON TABLE rail_data IS 'Stores detailed train journey information including scheduled and actual arrival/departure times with delays';
COMMENT ON COLUMN rail_data.train_no IS '5-digit train number';
COMMENT ON COLUMN rail_data.journey_date IS 'Date of the train journey (YYYY-MM-DD)';
COMMENT ON COLUMN rail_data.station_code IS 'Station code (e.g., CSMT, DR, KYN)';
COMMENT ON COLUMN rail_data.scheduled_arrival IS 'Scheduled arrival time (Unix timestamp)';
COMMENT ON COLUMN rail_data.scheduled_departure IS 'Scheduled departure time (Unix timestamp)';
COMMENT ON COLUMN rail_data.actual_arrival IS 'Actual arrival time (Unix timestamp)';
COMMENT ON COLUMN rail_data.actual_departure IS 'Actual departure time (Unix timestamp)';
COMMENT ON COLUMN rail_data.delay_arrival_minutes IS 'Delay in arrival (minutes)';
COMMENT ON COLUMN rail_data.delay_departure_minutes IS 'Delay in departure (minutes)';
COMMENT ON COLUMN rail_data.distance_from_origin_km IS 'Distance from origin station (kilometers)';
