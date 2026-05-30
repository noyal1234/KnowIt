-- IngredientIQ + watchlist schema (sync with app/db/models.py)

ALTER TABLE regulatory_additives
    ADD COLUMN IF NOT EXISTS function VARCHAR(128),
    ADD COLUMN IF NOT EXISTS iupac_name VARCHAR(512),
    ADD COLUMN IF NOT EXISTS who_jecfa_status VARCHAR(128),
    ADD COLUMN IF NOT EXISTS banned_in JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS at_risk_groups JSONB DEFAULT '[]';

CREATE TABLE IF NOT EXISTS ingredient_watchlist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    label_name VARCHAR(255) NOT NULL,
    e_code VARCHAR(16),
    normalized_key VARCHAR(270) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_user_watch_ingredient UNIQUE (user_id, normalized_key)
);

CREATE INDEX IF NOT EXISTS idx_ingredient_watchlist_user_id ON ingredient_watchlist(user_id);
CREATE INDEX IF NOT EXISTS idx_ingredient_watchlist_normalized_key ON ingredient_watchlist(normalized_key);
