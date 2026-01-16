-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.rail_data (
  id bigint NOT NULL DEFAULT nextval('rail_data_id_seq'::regclass),
  train_no integer NOT NULL CHECK (train_no > 0),
  journey_date date NOT NULL CHECK (journey_date IS NOT NULL),
  station_code character varying NOT NULL,
  scheduled_arrival integer,
  scheduled_departure integer,
  actual_arrival integer,
  actual_departure integer,
  delay_arrival_minutes integer,
  delay_departure_minutes integer,
  distance_from_origin_km numeric,
  created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT rail_data_pkey PRIMARY KEY (id)
);