-- Initial schema for Supabase CLI (mirrors SQLAlchemy models)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(320) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    display_name VARCHAR(255) DEFAULT '',
    avatar_url VARCHAR(2048),
    region VARCHAR(8) DEFAULT 'US',
    dietary_preferences JSONB DEFAULT '[]',
    allergens JSONB DEFAULT '[]',
    avoid_additives JSONB DEFAULT '[]',
    notification_enabled BOOLEAN DEFAULT TRUE,
    health_goal VARCHAR(64),
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    barcode VARCHAR(64) UNIQUE,
    content_hash VARCHAR(64),
    name VARCHAR(512) DEFAULT 'Unknown Product',
    brand VARCHAR(255),
    image_url VARCHAR(2048),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    product_id UUID NOT NULL REFERENCES products(id),
    scanned_at TIMESTAMPTZ DEFAULT NOW(),
    image_storage_path VARCHAR(1024),
    ingredient_text_raw TEXT,
    provider_meta JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS scan_reports (
    scan_id UUID PRIMARY KEY REFERENCES scans(id) ON DELETE CASCADE,
    health_score INTEGER NOT NULL,
    grade VARCHAR(2) NOT NULL,
    ingredients JSONB DEFAULT '[]',
    risks JSONB DEFAULT '[]',
    profile_alerts JSONB DEFAULT '[]',
    citations JSONB DEFAULT '[]',
    summary TEXT DEFAULT '',
    recommendations JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    product_id UUID NOT NULL REFERENCES products(id),
    is_favorite BOOLEAN DEFAULT FALSE,
    notes TEXT,
    tags JSONB DEFAULT '[]',
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, product_id)
);

CREATE TABLE IF NOT EXISTS regulatory_additives (
    id SERIAL PRIMARY KEY,
    canonical_name VARCHAR(255) NOT NULL,
    e_code VARCHAR(16),
    cas_number VARCHAR(64),
    fda_status VARCHAR(128),
    eu_status VARCHAR(128),
    fssai_status VARCHAR(128),
    adi_mg_per_kg DOUBLE PRECISION,
    default_risk_tier VARCHAR(16) DEFAULT 'unknown',
    source_url VARCHAR(2048)
);

CREATE INDEX IF NOT EXISTS idx_scans_user_id ON scans(user_id);
CREATE INDEX IF NOT EXISTS idx_regulatory_e_code ON regulatory_additives(e_code);
CREATE INDEX IF NOT EXISTS idx_regulatory_name ON regulatory_additives(canonical_name);
