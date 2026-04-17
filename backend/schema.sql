-- =============================================================================
-- Amrit Vaayu dMRV — Supabase Database Schema
-- =============================================================================
-- Execute this SQL in the Supabase SQL Editor (https://app.supabase.com)
-- to initialize the required tables for the dMRV platform.
--
-- Tables:
--   1. Farmers       — Registered farmers with geolocation
--   2. AWD_Logs      — Alternate Wetting & Drying cycle observations
--   3. Carbon_Credits — Calculated carbon credit records per farmer
-- =============================================================================


-- ---------------------------------------------------------------------------
-- 1. FARMERS TABLE
-- ---------------------------------------------------------------------------
-- Stores registered farmer profiles. Each farmer is uniquely identified
-- by their WhatsApp phone number (E.164 format, e.g., +919876543210).
-- Latitude and longitude enable geospatial mapping on the Level 2 dashboard.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "Farmers" (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    phone         TEXT        NOT NULL UNIQUE,          -- E.164 format
    name          TEXT        DEFAULT 'Unknown',        -- Farmer display name
    lat           DOUBLE PRECISION NOT NULL,            -- Latitude  (WGS84)
    lng           DOUBLE PRECISION NOT NULL,            -- Longitude (WGS84)
    region        TEXT        DEFAULT 'Unassigned',     -- Administrative region
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Index on phone for fast WhatsApp-based lookups
CREATE INDEX IF NOT EXISTS idx_farmers_phone ON "Farmers" (phone);


-- ---------------------------------------------------------------------------
-- 2. AWD_LOGS TABLE
-- ---------------------------------------------------------------------------
-- Records each Alternate Wetting & Drying observation submitted by a farmer
-- via WhatsApp. The `state_wet_dry` field is populated by the ML vision
-- classifier ("Wet" or "Dry"). `image_url` stores the Twilio media URL.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "AWD_Logs" (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    farmer_id       BIGINT      NOT NULL REFERENCES "Farmers" (id) ON DELETE CASCADE,
    image_url       TEXT,                                -- Twilio media URL or null
    state_wet_dry   TEXT        NOT NULL CHECK (state_wet_dry IN ('Wet', 'Dry')),
    confidence      DOUBLE PRECISION DEFAULT 0.0,        -- Model prediction confidence
    timestamp       TIMESTAMPTZ DEFAULT NOW()
);

-- Index for time-range queries on the dashboard
CREATE INDEX IF NOT EXISTS idx_awd_logs_timestamp ON "AWD_Logs" (timestamp DESC);
-- Index for farmer-specific log lookups
CREATE INDEX IF NOT EXISTS idx_awd_logs_farmer    ON "AWD_Logs" (farmer_id);


-- ---------------------------------------------------------------------------
-- 3. CARBON_CREDITS TABLE
-- ---------------------------------------------------------------------------
-- Tracks the methane (CH4) flux reduction score computed by the CNN-LSTM
-- model and the verification status of the resulting carbon credit.
--
-- Status lifecycle:  Pending → Verified → Issued → Retired
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "Carbon_Credits" (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    farmer_id       BIGINT          NOT NULL REFERENCES "Farmers" (id) ON DELETE CASCADE,
    flux_reduction  DOUBLE PRECISION NOT NULL,           -- CH4 reduction in kg CO₂e
    credits_earned  DOUBLE PRECISION DEFAULT 0.0,        -- Tokenized credit value
    status          TEXT            DEFAULT 'Pending'
                                    CHECK (status IN ('Pending', 'Verified', 'Issued', 'Retired')),
    methodology     TEXT            DEFAULT 'AMS-III.AU',-- Applicable CDM methodology
    created_at      TIMESTAMPTZ     DEFAULT NOW()
);

-- Index for status-based filtering in the Level 1 dashboard
CREATE INDEX IF NOT EXISTS idx_carbon_credits_status ON "Carbon_Credits" (status);
-- Index for farmer-specific credit aggregation
CREATE INDEX IF NOT EXISTS idx_carbon_credits_farmer ON "Carbon_Credits" (farmer_id);


-- ---------------------------------------------------------------------------
-- 4. SEED DATA (Optional — for development & demo purposes)
-- ---------------------------------------------------------------------------
-- Insert sample farmers around Maharashtra, India for hackathon demo.
-- These coordinates map to real paddy-growing regions.
-- ---------------------------------------------------------------------------
INSERT INTO "Farmers" (phone, name, lat, lng, region) VALUES
    ('+919876543210', 'Ramesh Patil',     19.0760,  72.8777, 'Mumbai Suburban'),
    ('+919876543211', 'Sunil Deshmukh',   18.5204,  73.8567, 'Pune'),
    ('+919876543212', 'Anita Jadhav',     20.0063,  73.7805, 'Nashik'),
    ('+919876543213', 'Prakash More',     19.9975,  73.7898, 'Nashik'),
    ('+919876543214', 'Kavita Shinde',    17.6599,  75.9064, 'Solapur'),
    ('+919876543215', 'Manoj Kulkarni',   21.1458,  79.0882, 'Nagpur'),
    ('+919876543216', 'Sunita Gaikwad',   19.8762,  75.3433, 'Chhatrapati Sambhajinagar'),
    ('+919876543217', 'Deepak Bhosale',   16.7050,  74.2433, 'Kolhapur')
ON CONFLICT (phone) DO NOTHING;

-- Insert sample AWD logs for demo visualization
INSERT INTO "AWD_Logs" (farmer_id, image_url, state_wet_dry, confidence) VALUES
    (1, NULL, 'Wet',  0.92),
    (1, NULL, 'Dry',  0.88),
    (2, NULL, 'Wet',  0.95),
    (3, NULL, 'Dry',  0.78),
    (4, NULL, 'Wet',  0.91),
    (5, NULL, 'Wet',  0.85),
    (6, NULL, 'Dry',  0.89),
    (7, NULL, 'Wet',  0.93),
    (8, NULL, 'Dry',  0.87);

-- Insert sample carbon credit records
INSERT INTO "Carbon_Credits" (farmer_id, flux_reduction, credits_earned, status) VALUES
    (1, 12.45, 3.11,  'Verified'),
    (2, 18.72, 4.68,  'Issued'),
    (3,  9.30, 2.33,  'Pending'),
    (4, 15.60, 3.90,  'Verified'),
    (5, 22.10, 5.53,  'Issued'),
    (6, 11.80, 2.95,  'Pending'),
    (7, 14.25, 3.56,  'Verified'),
    (8, 19.90, 4.98,  'Retired');
