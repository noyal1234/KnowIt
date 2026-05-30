-- Row Level Security policies for Supabase production

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_watchlist ENABLE ROW LEVEL SECURITY;

CREATE POLICY profiles_select_own ON profiles
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY profiles_update_own ON profiles
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY scans_select_own ON scans
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY scans_insert_own ON scans
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY scans_delete_own ON scans
    FOR DELETE USING (user_id = auth.uid());

CREATE POLICY scan_reports_select_own ON scan_reports
    FOR SELECT USING (
        scan_id IN (SELECT id FROM scans WHERE user_id = auth.uid())
    );

CREATE POLICY user_products_all_own ON user_products
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY ingredient_watchlist_select_own ON ingredient_watchlist
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY ingredient_watchlist_insert_own ON ingredient_watchlist
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY ingredient_watchlist_delete_own ON ingredient_watchlist
    FOR DELETE USING (user_id = auth.uid());

-- Storage bucket: label-images (create via Supabase dashboard or CLI)
-- Path pattern: {user_id}/{scan_id}.jpg
