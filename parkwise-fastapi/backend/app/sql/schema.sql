CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE slots (
    slot_id VARCHAR PRIMARY KEY,
    zone_id VARCHAR,
    polygon JSON,
    vehicle_type_hint VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE slot_status (
    slot_id VARCHAR PRIMARY KEY REFERENCES slots(slot_id),
    occupied BOOLEAN DEFAULT FALSE,
    confidence FLOAT DEFAULT 1.0,
    vehicle_type VARCHAR,
    last_seen TIMESTAMP DEFAULT NOW(),
    reserved_until TIMESTAMP,
    predicted_free_minutes INTEGER,
    prediction_confidence FLOAT,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE slot_events (
    id SERIAL PRIMARY KEY,
    slot_id VARCHAR NOT NULL,
    event_type VARCHAR,
    meta JSON,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    slot_id VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'holding',
    hold_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);