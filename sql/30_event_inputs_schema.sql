CREATE TABLE IF NOT EXISTS event_hs_scope (
  event_id TEXT NOT NULL,
  hs_code TEXT NOT NULL,
  PRIMARY KEY (event_id, hs_code)
);

CREATE TABLE IF NOT EXISTS firm_event_exposure (
  event_id TEXT NOT NULL,
  firm_id TEXT NOT NULL,
  exposed_flag INT NOT NULL CHECK (exposed_flag IN (0, 1)),
  exposure_bucket TEXT NULL,
  evidence_note TEXT NULL,
  PRIMARY KEY (event_id, firm_id)
);

CREATE TABLE IF NOT EXISTS observed_margin_sign (
  event_id TEXT NOT NULL,
  firm_id TEXT NOT NULL,
  margin_change_sign INT NOT NULL CHECK (margin_change_sign IN (-1, 0, 1)),
  PRIMARY KEY (event_id, firm_id)
);

CREATE INDEX IF NOT EXISTS idx_event_hs_scope_event ON event_hs_scope (event_id);
CREATE INDEX IF NOT EXISTS idx_firm_event_exposure_event ON firm_event_exposure (event_id);
CREATE INDEX IF NOT EXISTS idx_observed_margin_sign_event ON observed_margin_sign (event_id);
