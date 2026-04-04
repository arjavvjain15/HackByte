-- ╔══════════════════════════════════════════════════════════════╗
-- ║  EcoSnap — Remaining Tables (profiles already exists)      ║
-- ║  Copy ALL of this into Supabase SQL Editor → Click RUN     ║
-- ╚══════════════════════════════════════════════════════════════╝


-- ── REPORTS TABLE ─────────────────────────────────────────────
CREATE TABLE reports (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         text,
    photo_url       text NOT NULL,
    lat             double precision NOT NULL DEFAULT 0,
    lng             double precision NOT NULL DEFAULT 0,
    hazard_type     text,
    severity        text,
    department      text,
    summary         text,
    complaint       text,
    upvotes         integer DEFAULT 0,
    status          text DEFAULT 'open',
    created_at      timestamptz DEFAULT now(),
    resolved_at     timestamptz
);

CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_user_id ON reports(user_id);
CREATE INDEX idx_reports_created_at ON reports(created_at DESC);


-- ── UPVOTES TABLE ─────────────────────────────────────────────
CREATE TABLE upvotes (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       uuid REFERENCES reports(id) ON DELETE CASCADE,
    user_id         text NOT NULL,
    created_at      timestamptz DEFAULT now(),
    UNIQUE(report_id, user_id)
);


-- ── USER BADGES TABLE ─────────────────────────────────────────
CREATE TABLE user_badges (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         text NOT NULL,
    badge_id        text NOT NULL,
    earned_at       timestamptz DEFAULT now(),
    UNIQUE(user_id, badge_id)
);


-- ── RPC FUNCTIONS (counter increments) ────────────────────────
CREATE OR REPLACE FUNCTION increment_reports_submitted(user_id_input text)
RETURNS void AS $$
BEGIN
    UPDATE profiles SET reports_submitted = reports_submitted + 1
    WHERE id::text = user_id_input;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION increment_reports_resolved(user_id_input text)
RETURNS void AS $$
BEGIN
    UPDATE profiles SET reports_resolved = reports_resolved + 1
    WHERE id::text = user_id_input;
END;
$$ LANGUAGE plpgsql;


-- ── ROW LEVEL SECURITY ───────────────────────────────────────
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE upvotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_badges ENABLE ROW LEVEL SECURITY;

CREATE POLICY "allow_all_reports" ON reports FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_upvotes" ON upvotes FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_badges" ON user_badges FOR ALL USING (true) WITH CHECK (true);
