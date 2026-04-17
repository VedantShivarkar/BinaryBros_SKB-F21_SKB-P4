-- Supabase schema initialization for Amrit Vaayu dMRV

-- Farmers table
CREATE TABLE Farmers (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL
);

-- AWD_Logs table (Alternate Wetting and Drying cycles)
CREATE TABLE AWD_Logs (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES Farmers(id),
    image_url TEXT,
    state_wet_dry VARCHAR(10) NOT NULL CHECK (state_wet_dry IN ('Wet', 'Dry')),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Carbon_Credits table
CREATE TABLE Carbon_Credits (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES Farmers(id),
    flux_reduction DOUBLE PRECISION NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending'
);
