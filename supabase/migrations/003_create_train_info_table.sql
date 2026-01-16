-- Create train_info table for storing static train metadata
-- Migration: 003_create_train_info_table

CREATE TABLE IF NOT EXISTS train_info (
    id BIGSERIAL PRIMARY KEY,
    train_no INT NOT NULL UNIQUE,
    train_name VARCHAR(100) NOT NULL,
    journey_type VARCHAR(50) NOT NULL,
    destination_station_code VARCHAR(10) NOT NULL,
    journey_duration INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints for data validity
    CONSTRAINT valid_train_no CHECK (train_no > 0),
    CONSTRAINT valid_journey_type CHECK (journey_type IN ('one_day', 'multiple_day')),
    CONSTRAINT valid_journey_duration CHECK (journey_duration > 0)
);

-- Create indexes for common queries
CREATE INDEX idx_train_info_train_no ON train_info(train_no);
CREATE INDEX idx_train_info_train_name ON train_info(train_name);
CREATE INDEX idx_train_info_journey_type ON train_info(journey_type);
CREATE INDEX idx_train_info_destination_station ON train_info(destination_station_code);

-- Add comments describing the table
COMMENT ON TABLE train_info IS 'Stores static train metadata and information';
COMMENT ON COLUMN train_info.train_no IS '5-digit train number (unique)';
COMMENT ON COLUMN train_info.train_name IS 'Official name of the train';
COMMENT ON COLUMN train_info.journey_type IS 'Type of journey: one_day or multiple_day';
COMMENT ON COLUMN train_info.destination_station_code IS 'Destination station code (e.g., CSMT, NGP)';
COMMENT ON COLUMN train_info.journey_duration IS 'Total journey duration in hours';
